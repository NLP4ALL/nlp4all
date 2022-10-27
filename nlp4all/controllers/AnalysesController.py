"""Analyses controller""" # pylint: disable=invalid-name

import ast
import datetime
from random import sample
import re
from flask import jsonify, redirect, render_template, request, url_for, flash
from flask_login import current_user


from sqlalchemy.orm.attributes import flag_modified

from nlp4all.models.database import db_session
from nlp4all.models import (
    BayesianAnalysis,
    BayesianRobot,
    ConfusionMatrix,
    Project,
    Tweet,
    TweetAnnotation,
    TweetTag,
    TweetTagCategory,
    User,
)

from nlp4all.helpers.analyses import (
    add_matrix,
    ann_create_css_info,
    create_bar_chart_data,
    create_css_info,
    create_pie_chart_data,
    get_tags,
    matrix_css_info,
    matrix_metrics,
)

from nlp4all.forms.analyses import BayesianRobotForms, CreateMatrixForm, TaggingForm, ThresholdForm


class AnalysesController:
    """Analyses Controller"""

    # @TODO break out (probably)

    @classmethod
    def robot_summary(cls):
        """Robot summary page"""
        analysis_id = request.args.get("analysis", 0, type=int)
        bayes_analysis = BayesianAnalysis.query.get(analysis_id)
        robots = [r for r in bayes_analysis.robots if r.retired and r.user == current_user.id]
        return render_template("robot_summary.html", analysis=bayes_analysis, robots=robots)

    @classmethod
    def robot(cls):
        """Robot page"""
        # first get user's robot associated with
        robot_id = request.args.get("robot", 0, type=int)
        # find the analysis and check if it belongs to the user
        bayes_robot = BayesianRobot.query.get(robot_id)
        if bayes_robot.retired:
            acc_dict = bayes_robot.accuracy
            if bayes_robot.parent is not None:
                parent_robot = BayesianRobot.query.get(bayes_robot.parent)
                parent_accuracy = parent_robot.accuracy
                acc_dict["parent_accuracy"] = parent_accuracy["accuracy"]
                acc_dict["parent_tweets_targeted"] = parent_accuracy["tweets_targeted"]
        else:
            acc_dict = {
                "accuracy": 0,
                "tweets_targeted": 0,
                "features": {},
                "table_data": [],
            }
        if request.method == "POST" and "delete" in request.form.to_dict():
            del bayes_robot.features[request.form.to_dict()["delete"]]
            flag_modified(bayes_robot, "features")
            db_session.add(bayes_robot)
            db_session.merge(bayes_robot)
            db_session.flush()
            db_session.commit()
            redirect(url_for("robot", robot=robot_id))
        form = BayesianRobotForms()
        if request.method == "POST" and "add_feature_form-submit" in request.form.to_dict():
            if (
                " " not in form.add_feature_form.data
                and len(form.add_feature_form.feature.data) > 3
                and len(form.add_feature_form.reasoning.data) > 5
                and len(bayes_robot.features) <= 20
            ):
                new_feature = {
                    form.add_feature_form.feature.data.strip(): form.add_feature_form.reasoning.data
                }
                bayes_robot.features.update(new_feature)
                flag_modified(bayes_robot, "features")
                db_session.add(bayes_robot)
                db_session.merge(bayes_robot)
                db_session.flush()
                db_session.commit()
                return redirect(url_for("robot", robot=robot_id))
        form = BayesianRobotForms()
        if request.method == "POST" and "run_analysis_form-run_analysis" in request.form.to_dict():
            if len(bayes_robot.features) > 0:
                bayes_robot.accuracy = bayes_robot.calculate_accuracy()
                flag_modified(bayes_robot, "accuracy")
                db_session.merge(bayes_robot)
                bayes_robot.accuracy = BayesianRobot.calculate_accuracy(bayes_robot)
                bayes_robot.retired = True
                bayes_robot.time_retired = datetime.datetime.utcnow()
                child_robot = bayes_robot.clone()
                db_session.add(child_robot)
                db_session.flush()
                bayes_robot.child = child_robot.id
                db_session.add(bayes_robot)
                db_session.commit()
                return redirect(url_for("robot", robot=bayes_robot.id))
        table_data = acc_dict["table_data"]
        table_data = [d for d in table_data if not "*" in d["word"]]
        acc_dict["table_data"] = table_data
        print(table_data)
        return render_template(
            "robot.html", title="Robot", r=bayes_robot, form=form, acc_dict=acc_dict
        )

    @classmethod
    def high_score(cls):
        """High score page"""
        project_id = request.args.get("project", 1, type=int)
        a_project = Project.query.get(project_id)
        table_data = []
        for ana in a_project.analyses:
            if len(ana.robots) > 1:
                last_run_robot = ana.robots[-2]
                rob_dict = {}
                user = User.query.get(ana.user)
                rob_dict["user"] = user.username
                link_text = (
                    '<a href="/robot?robot='
                    + str(last_run_robot.id)
                    + '">'
                    + str(last_run_robot.id)
                    + "</a>"
                )
                print(link_text)
                rob_dict["robot"] = last_run_robot.id
                acc_dict = last_run_robot.accuracy
                score = (
                    acc_dict["accuracy"] * acc_dict["tweets_targeted"]
                    - (1 - acc_dict["accuracy"]) * acc_dict["tweets_targeted"]
                )
                rob_dict["score"] = score
                table_data.append(rob_dict)

        print(table_data)
        return render_template("highscore.html", title="High Score", table_data=table_data)

    @classmethod
    def shared_analysis_view(cls):  # pylint: disable=too-many-locals
        """Shared analysis view page"""
        analysis_id = request.args.get("analysis", 0, type=int)
        tweet_info = {}
        all_words = []
        if analysis_id == 0:
            return
        bayes_analysis: BayesianAnalysis = BayesianAnalysis.query.get(analysis_id)
        # if not analysis.shared:
        #     return(redirect(url_for('home')))
        if bayes_analysis.shared:
            tweet_info = {t: {"correct": 0, "incorrect": 0, "%": 0} for t in bayes_analysis.tweets}
        else:
            tweet_info = {
                t.tweet: {"correct": 0, "incorrect": 0, "%": 0} for t in bayes_analysis.tags
            }
        # for tag in analysis.tags:
        non_empty_tags = [t for t in bayes_analysis.tags if t.tweet is not None]
        for tag in non_empty_tags:
            twit = Tweet.query.get(tag.tweet)
            all_words.extend(twit.words)
            tweet_info[twit.id]["full_text"] = twit.full_text
            tweet_info[twit.id]["category"] = TweetTagCategory.query.get(twit.category).name
            if twit.category == tag.category:
                tweet_info[twit.id]["correct"] = tweet_info[twit.id]["correct"] + 1
            else:
                tweet_info[twit.id]["incorrect"] = tweet_info[twit.id]["incorrect"] + 1
        for tweet_id in list(tweet_info.keys()):
            # if they haven't been categorized by anyone, remove them
            if tweet_info[tweet_id]["correct"] == 0 and tweet_info[tweet_id]["incorrect"] == 0:
                del tweet_info[tweet_id]
            else:
                tweet_info[tweet_id].update(
                    {
                        "%": (
                            tweet_info[tweet_id]["correct"]
                            / (tweet_info[tweet_id]["incorrect"] + tweet_info[tweet_id]["correct"])
                        )
                        * 100
                    }
                )
        tweet_info = sorted(
            [t for t in tweet_info.items()],  # pylint: disable=unnecessary-comprehension
            key=lambda x: x[1]["%"],
            reverse=True,
        )
        data = {}
        percent_values = [d[1]["%"] for d in tweet_info]
        percent_counts = [
            {"label": str(percent), "estimate": percent_values.count(percent)}
            for percent in set(percent_values)
        ]
        for data_point in percent_counts:
            color = float(data_point["label"]) / 100 * 120
            color = int(color)
            data_point.update(
                {"color": f"hsl({color}, 50%, 70%)", "bg_color": f"hsl({color}, 50%, 70%)"}
            )
        chart_data = {"title": "Antal korrekte", "data_points": percent_counts}
        data["chart_data"] = chart_data
        # words = [word for x in tweet_info for word in x[1]["words"]]
        (
            pred_by_word,
            data["predictions"],
        ) = bayes_analysis.get_predictions_and_words(  # pylint: disable=line-too-long
            all_words
        )
        word_info = []
        for wrd in set(all_words):
            word_dict = {"word": wrd, "counts": all_words.count(wrd)}
            for k, val in pred_by_word[wrd].items():
                word_dict[k] = val
            word_info.append(word_dict)
        tweet_info = [t[1] for t in tweet_info]
        # we don't need to sort this since we put it in a datatable anyway
        # print(word_info)
        # sorted_word_info = sorted([w for w in word_info], key=lambda x: x['counts'], reverse=True)
        return render_template(
            "shared_analysis_view.html",
            title="Oversigt over analyse",
            tweets=tweet_info,
            word_info=word_info,
            analysis=bayes_analysis,
            **data,
        )

    @classmethod
    def analysis(cls):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Analysis page"""
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        analysis_id = request.args.get("analysis", 1, type=int)
        bayes_analysis = BayesianAnalysis.query.get(analysis_id)
        a_project = Project.query.get(bayes_analysis.project)
        if "tag" in request.form.to_dict():
            # category = TweetTagCategory.query.get(int(form.choices.data))
            tag_info = ast.literal_eval(request.form["tag"])
            tweet_id = tag_info[0]
            category_id = tag_info[1]
            the_tweet = Tweet.query.get(tweet_id)
            category = TweetTagCategory.query.get(category_id)
            the_tweet = Tweet.query.get(tweet_id)
            bayes_analysis.data = bayes_analysis.updated_data(the_tweet, category)
            # all this  stuff is necessary  because the database backend doesnt resgister
            # changes on JSON
            flag_modified(bayes_analysis, "data")
            db_session.add(bayes_analysis)
            db_session.merge(bayes_analysis)
            db_session.flush()
            db_session.commit()
            tag = TweetTag(
                category=category.id,
                analysis=bayes_analysis.id,
                tweet=the_tweet.id,
                user=current_user.id,
            )
            db_session.add(tag)
            db_session.commit()
            # redirect(url_for('home'))
            return redirect(url_for("analysis", analysis=analysis_id))
        # check if user has access to this.
        # either it is a shared project. In that case the user needs to be a member of
        # projects.organization
        # or it is not a shared project, in which case the user must be the owner.
        # owned = False
        # if analysis.shared :
        #     if project.organization in [org.id for org in current_user.organizations]:
        #         owned = True
        # if analysis.user == current_user.id or current_user.admin:#or current_user.
        #     owned = True
        # if owned == False:
        #     return redirect(url_for('home'))
        categories = TweetTagCategory.query.filter(
            TweetTagCategory.id.in_(
                [p.id for p in a_project.categories]
            )  # pylint: disable=no-member
        ).all()  # @TODO: pretty sure we can just get project.categories
        # tweets = project.tweets
        the_tweet = None
        uncompleted_counts = 0
        if bayes_analysis.shared:
            completed_tweets = [t.tweet for t in bayes_analysis.tags if t.user == current_user.id]
            uncompleted_tweets = [t for t in bayes_analysis.tweets if t not in completed_tweets]
            uncompleted_counts = len(uncompleted_tweets)
            if len(uncompleted_tweets) > 0:
                the_tweet_id = uncompleted_tweets[0]
                the_tweet = Tweet.query.get(the_tweet_id)
            else:
                flash(
                    "Well done! You finished all your tweets, wait for the rest of the group.",
                    "success",
                )
                the_tweet = Tweet(full_text="", words=[])
        else:
            the_tweet = a_project.get_random_tweet()
        form = TaggingForm()
        form.choices.choices = [(str(c.id), c.name) for c in categories]
        number_of_tagged = len(bayes_analysis.tags)
        data = {}
        data["number_of_tagged"] = number_of_tagged
        data["words"], data["predictions"] = bayes_analysis.get_predictions_and_words(
            set(the_tweet.words)
        )
        data["word_tuples"] = create_css_info(data["words"], the_tweet.full_text, categories)

        data["chart_data"] = create_bar_chart_data(data["predictions"], "Computeren gætter på...")
        # filter robots that are retired, and sort them alphabetically
        # data['robots'] = sorted(robots, key= lambda r: r.name)
        data["analysis_data"] = bayes_analysis.data
        data["user"] = current_user
        data["user_role"] = current_user.roles
        data["tag_options"] = a_project.categories
        data["uncompleted_counts"] = uncompleted_counts
        data["pie_chart_data"] = create_pie_chart_data([c.name for c in categories], "Categories")
        # data['pie_chart']['data_points']['pie_data']

        if form.validate_on_submit() and form.data:  # pylint: disable=no-member
            category = TweetTagCategory.query.get(
                int(form.choices.data)
            )  # pylint: disable=no-member
            bayes_analysis.data = bayes_analysis.updated_data(the_tweet, category)
            # all this  stuff is necessary  because the database backend doesnt resgister
            # changes on JSON
            flag_modified(bayes_analysis, "data")
            db_session.add(bayes_analysis)
            db_session.merge(bayes_analysis)
            db_session.flush()
            db_session.commit()
            tag = TweetTag(
                category=category.id,
                analysis=bayes_analysis.id,
                tweet=the_tweet.id,
                user=current_user.id,
            )
            db_session.add(tag)
            db_session.commit()
            # redirect(url_for('home'))
            return redirect(url_for("analysis", analysis=analysis_id))

        # tags per user
        ann_tags = []
        if bayes_analysis.annotate == 2:
            ann_names = [cat.name for cat in a_project.categories]
            ann_tags = TweetAnnotation.query.filter(
                TweetAnnotation.annotation_tag.in_(ann_names),  # pylint: disable=no-member
                TweetAnnotation.analysis == analysis_id,
                TweetAnnotation.user == current_user.id,
            ).all()
            categories = TweetTagCategory.query.filter(
                TweetTagCategory.id.in_(
                    [p.id for p in a_project.categories]
                )  # pylint: disable=no-member
            ).all()  # @TODO: pretty sure we can just get project.categories
        if bayes_analysis.annotate == 3:
            ann_tags = TweetAnnotation.query.filter(
                TweetAnnotation.analysis == analysis_id, TweetAnnotation.user == current_user.id
            ).all()
        tag_list = list(
            set([a.annotation_tag for a in ann_tags])
        )  # pylint: disable=consider-using-set-comprehension
        for i in categories:
            if i.name not in tag_list:
                tag_list.append(i.name)

        if not bayes_analysis.shared:
            user_analysis_robots = BayesianRobot.query.filter(
                BayesianRobot.user == current_user.id, BayesianRobot.analysis == bayes_analysis.id
            ).all()
            if len(user_analysis_robots) == 0:
                bayes_robot = BayesianRobot(
                    name=current_user.username + "s robot",
                    analysis=bayes_analysis.id,
                    user=current_user.id,
                )
                db_session.add(bayes_robot)
                db_session.flush()
                db_session.commit()
                return redirect(url_for("analysis", analysis=analysis_id))
            data["last_robot"] = user_analysis_robots[-1]

        # finally get the last robot to link, if it is not a shared analysis
        return render_template(
            "analysis.html",
            analysis=bayes_analysis,
            tag_list=tag_list,
            tweet=the_tweet,
            form=form,
            **data,
        )

    # for the template with three tabs: matrix, iterate, and compare

    @classmethod
    def matrix(
        cls, matrix_id
    ):  # pylint: disable=too-many-locals, too-many-statements, too-many-branches
        """Matrix page"""
        userid = current_user.id
        c_matrix = ConfusionMatrix.query.get(matrix_id)
        matrices = ConfusionMatrix.query.filter(
            ConfusionMatrix.user == userid
        ).all()  # all matrices for the other tabs
        all_cats = TweetTagCategory.query.all()  # all cats for the other tabs

        categories = c_matrix.categories
        cat_names = [c.name for c in categories]
        form = ThresholdForm()
        # get a tnt_set
        tnt_sets = c_matrix.training_and_test_sets
        if "tnt_nr" in request.args.to_dict().keys():
            tnt_nr = request.args.get("tnt_nr", type=int)
            a_tnt_set = tnt_sets[tnt_nr]
        else:
            a_tnt_set = tnt_sets[0]
            tnt_nr = 0

        train_tweet_ids = a_tnt_set[0].keys()
        train_set_size = len(a_tnt_set[0].keys())
        test_tweets = [Tweet.query.get(tweet_id) for tweet_id in a_tnt_set[1].keys()]

        # threshold and ratio accuracy
        if form.validate_on_submit():

            c_matrix.threshold = form.threshold.data
            flag_modified(c_matrix, "threshold")
            c_matrix.ratio = round(form.ratio.data * 0.01, 3)
            flag_modified(c_matrix, "ratio")
            c_matrix.training_and_test_sets = c_matrix.update_tnt_set()
            flag_modified(c_matrix, "training_and_test_sets")
            db_session.add(c_matrix)
            db_session.merge(c_matrix)
            db_session.flush()
            db_session.commit()
            if form.shuffle.data:
                tnt_list = list(range(0, len(tnt_sets)))
                tnt_nr = sample(tnt_list, 1)[0]
                a_tnt_set = tnt_sets[tnt_nr]  # tnt_set id
                train_tweet_ids = a_tnt_set[0].keys()
                train_set_size = len(a_tnt_set[0].keys())
                test_tweets = [Tweet.query.get(tweet_id) for tweet_id in a_tnt_set[1].keys()]

                # train on the training set:
                c_matrix.train_data = c_matrix.train_model(train_tweet_ids)
                flag_modified(c_matrix, "train_data")

                # make matrix data
                matrix_data = c_matrix.make_matrix_data(test_tweets, cat_names)
                c_matrix.matrix_data = {i[0]: i[1] for i in matrix_data}
                flag_modified(c_matrix, "matrix_data")

                # filter according to the threshold
                incl_tweets = sorted(
                    [
                        t
                        for t in c_matrix.matrix_data.items()
                        if t[1]["probability"] >= c_matrix.threshold
                        and t[1]["class"] != "undefined"
                    ],
                    key=lambda x: x[1]["probability"],
                    reverse=True,
                )
                excl_tweets = sorted(
                    [
                        t
                        for t in c_matrix.matrix_data.items()
                        if t[1]["probability"] < c_matrix.threshold or t[1]["class"] == "undefined"
                    ],
                    key=lambda x: x[1]["probability"],
                    reverse=True,
                )

                # count different occurences
                class_list = [t[1]["class"] for t in incl_tweets]
                class_list_all = []
                class_list_all = []
                for cat in cat_names:
                    for cat in cat_names:
                        class_list_all.append(str("Pred_" + str(cat) + "_Real_" + str(cat)))
                        class_list_all.append(str("Pred_" + str(cat) + "_Real_" + str(cat)))
                class_list_all = list(set(class_list_all))
                matrix_classes = {c: 0 for c in class_list_all}
                for i in set(class_list):
                    matrix_classes[i] = class_list.count(i)

                true_keys = [str("Pred_" + i + "_Real_" + i) for i in cat_names]
                true_dict = dict(filter(lambda item: item[0] in true_keys, matrix_classes.items()))

                accuracy = round((sum(true_dict.values()) / sum(matrix_classes.values())), 3)

                # precision and recall
                metrics = matrix_metrics(cat_names, matrix_classes)

                # summarise data
                c_matrix.data = {
                    "matrix_classes": matrix_classes,
                    "accuracy": accuracy,
                    "metrics": metrics,
                    "nr_test_tweets": len(test_tweets),
                    "nr_train_tweets": train_set_size,
                    "nr_incl_tweets": len(incl_tweets),
                    "nr_excl_tweets": len(excl_tweets),
                }
                flag_modified(c_matrix, "data")
                db_session.add(c_matrix)
                db_session.merge(c_matrix)
                db_session.flush()
                db_session.commit()
                return redirect(url_for("matrix", matrix_id=c_matrix.id, tnt_nr=tnt_nr))

            # train on the training set:
            c_matrix.train_data = c_matrix.train_model(train_tweet_ids)
            flag_modified(c_matrix, "train_data")

            # make matrix data
            matrix_data = c_matrix.make_matrix_data(test_tweets, cat_names)
            c_matrix.matrix_data = {i[0]: i[1] for i in matrix_data}
            flag_modified(c_matrix, "matrix_data")

            # filter according to the threshold
            incl_tweets = sorted(
                [
                    t
                    for t in c_matrix.matrix_data.items()
                    if t[1]["probability"] >= c_matrix.threshold and t[1]["class"] != "undefined"
                ],
                key=lambda x: x[1]["probability"],
                reverse=True,
            )
            excl_tweets = sorted(
                [
                    t
                    for t in c_matrix.matrix_data.items()
                    if t[1]["probability"] < c_matrix.threshold or t[1]["class"] == "undefined"
                ],
                key=lambda x: x[1]["probability"],
                reverse=True,
            )

            # count different occurences
            class_list = [t[1]["class"] for t in incl_tweets]
            class_list_all = []
            for cat in cat_names:
                for cat in cat_names:
                    class_list_all.append(str("Pred_" + str(cat) + "_Real_" + str(cat)))
                    class_list_all.append(str("Pred_" + str(cat) + "_Real_" + str(cat)))
            matrix_classes = {c: 0 for c in class_list_all}
            for i in set(class_list):
                matrix_classes[i] = class_list.count(i)

            true_keys = [str("Pred_" + i + "_Real_" + i) for i in cat_names]
            true_dict = dict(filter(lambda item: item[0] in true_keys, matrix_classes.items()))

            # accuracy = sum(correct predictions)/sum(all matrix points)
            accuracy = round((sum(true_dict.values()) / sum(matrix_classes.values())), 3)
            # precision and recall
            metrics = matrix_metrics(cat_names, matrix_classes)

            # summarise data
            c_matrix.data = {
                "matrix_classes": matrix_classes,
                "accuracy": accuracy,
                "metrics": metrics,
                "nr_test_tweets": len(test_tweets),
                "nr_train_tweets": train_set_size,
                "nr_incl_tweets": len(incl_tweets),
                "nr_excl_tweets": len(excl_tweets),
            }
            flag_modified(c_matrix, "data")
            db_session.add(c_matrix)
            db_session.merge(c_matrix)
            db_session.flush()
            db_session.commit()
            return redirect(url_for("matrix", matrix_id=c_matrix.id, tnt_nr=tnt_nr))

        # prepare data for matrix table
        counts = c_matrix.make_table_data(cat_names)
        for i in range(len(counts)):  # pylint: disable=consider-using-enumerate
            counts[i].insert(0, cat_names[i])
        index_list = []
        for i in range(len(counts)):  # pylint: disable=consider-using-enumerate
            cat_counts = cat_names[i]
            count_comparison = [
                str("Pred_" + counts[i][0] + "_Real_" + cat_counts) for i in range(len(counts))
            ]
            index_list.append(count_comparison)
        for i in range(len(index_list)):  # pylint: disable=consider-using-enumerate
            index_list[i].insert(0, cat_names[i])
        index_list = [
            [[counts[j][i], index_list[j][i], (j, i)] for i in range(0, len(counts[j]))]
            for j in range(len(counts))
        ]
        index_list = matrix_css_info(index_list)

        metrics = sorted(
            [t for t in c_matrix.data["metrics"].items()],
            key=lambda x: x[1]["recall"],
            reverse=True,  # pylint: disable=unnecessary-comprehension
        )
        metrics = [t[1] for t in metrics]
        return render_template(
            "matrix.html",
            cat_names=cat_names,
            form=form,
            matrix=c_matrix,
            all_cats=all_cats,
            matrices=matrices,
            index_list=index_list,
            metrics=metrics,
        )

    @classmethod
    def matrix_tweets(cls, matrix_id):
        """show tweets in matrix"""
        c_matrix = ConfusionMatrix.query.get(matrix_id)
        # request tweets from the correct quadrant
        cm_name = request.args.get("cm", type=str)
        title = str("Tweets classified as " + cm_name)
        if cm_name in [c.name for c in c_matrix.categories]:
            id_c = [
                {
                    int(k): {
                        "probability": v["probability"],
                        "relative probability": v["relative probability"],
                        "prediction": v["pred_cat"],
                    }
                    for k, v in c_matrix.matrix_data.items()
                    if v["real_cat"] == cm_name and v["probability"] >= c_matrix.threshold
                }
            ][0]
            tweets = Tweet.query.filter(
                Tweet.id.in_(id_c.keys())
            ).all()  # pylint: disable=no-member
        else:
            id_c = [
                {
                    int(k): {
                        "probability": v["probability"],
                        "relative probability": v["relative probability"],
                        "prediction": v["pred_cat"],
                    }
                    for k, v in c_matrix.matrix_data.items()
                    if v["class"] == cm_name and v["probability"] >= c_matrix.threshold
                }
            ][0]
            tweets = Tweet.query.filter(
                Tweet.id.in_(id_c.keys())
            ).all()  # pylint: disable=no-member

        cm_info = {
            t.id: {
                "text": t.full_text,
                "category": t.handle,
                "prediction": id_c[t.id]["prediction"],
                "probability": round(id_c[t.id]["probability"], 3),
                "relative probability": round(id_c[t.id]["relative probability"], 3),
            }
            for t in tweets
        }
        cm_info = sorted(
            [t for t in cm_info.items()],  # pylint: disable=unnecessary-comprehension
            key=lambda x: x[1]["probability"],
            reverse=True,
        )
        cm_info = [t[1] for t in cm_info]
        return render_template("matrix_tweets.html", cm_info=cm_info, matrix=c_matrix, title=title)

    @classmethod
    def my_matrices(cls):  # pylint: disable=too-many-locals
        """show all matrices"""
        userid = current_user.id
        matrices = ConfusionMatrix.query.filter(ConfusionMatrix.user == userid).all()

        form = CreateMatrixForm()
        form.categories.choices = [(str(s.id), s.name) for s in TweetTagCategory.query.all()]

        # create a new matrix
        if form.validate_on_submit():
            userid = current_user.id
            cats = [int(n) for n in form.categories.data]
            ratio = form.ratio.data * 0.01  # convert back to decimals
            c_matrix = add_matrix(cat_ids=cats, ratio=ratio, userid=userid)
            db_session.add(c_matrix)
            db_session.merge(c_matrix)
            db_session.flush()
            db_session.commit()  # not sure if this is necessary

            cat_names = [c.name for c in c_matrix.categories]
            a_tnt_set = c_matrix.training_and_test_sets[0]  # as a default
            train_tweet_ids = a_tnt_set[0].keys()
            train_set_size = len(a_tnt_set[0].keys())
            test_tweets = [Tweet.query.get(tweet_id) for tweet_id in a_tnt_set[1].keys()]

            # train on the training set:
            c_matrix.train_data = c_matrix.train_model(train_tweet_ids)
            flag_modified(c_matrix, "train_data")

            # make matrix data
            matrix_data = c_matrix.make_matrix_data(test_tweets, cat_names)
            c_matrix.matrix_data = {i[0]: i[1] for i in matrix_data}
            flag_modified(c_matrix, "matrix_data")

            # filter according to the threshold
            incl_tweets = sorted(
                [
                    t
                    for t in c_matrix.matrix_data.items()
                    if t[1]["probability"] >= c_matrix.threshold and t[1]["class"] != "undefined"
                ],
                key=lambda x: x[1]["probability"],
                reverse=True,
            )
            excl_tweets = sorted(
                [
                    t
                    for t in c_matrix.matrix_data.items()
                    if t[1]["probability"] < c_matrix.threshold or t[1]["class"] == "undefined"
                ],
                key=lambda x: x[1]["probability"],
                reverse=True,
            )

            # count different occurences
            class_list = [t[1]["class"] for t in incl_tweets]
            class_list_all = []
            for c_name in cat_names:
                for cat in cat_names:
                    class_list_all.append(str("Pred_" + str(c_name) + "_Real_" + str(cat)))
                    class_list_all.append(str("Pred_" + str(cat) + "_Real_" + str(c_name)))
            class_list_all = list(set(class_list_all))
            matrix_classes = {c: 0 for c in class_list_all}
            for i in set(class_list):
                matrix_classes[i] = class_list.count(i)

            true_keys = [str("Pred_" + i + "_Real_" + i) for i in cat_names]
            true_dict = dict(filter(lambda item: item[0] in true_keys, matrix_classes.items()))

            # accuracy = sum(correct predictions)/sum(all matrix points)
            accuracy = round((sum(true_dict.values()) / sum(matrix_classes.values())), 3)
            # precision and recall
            metrics = matrix_metrics(cat_names, matrix_classes)

            # summarise data
            c_matrix.data = {
                "matrix_classes": matrix_classes,
                "accuracy": accuracy,
                "metrics": metrics,
                "nr_test_tweets": len(test_tweets),
                "nr_train_tweets": train_set_size,
                "nr_incl_tweets": len(incl_tweets),
                "nr_excl_tweets": len(excl_tweets),
            }
            flag_modified(c_matrix, "data")
            db_session.add(c_matrix)
            db_session.merge(c_matrix)
            db_session.flush()
            db_session.commit()
            return redirect(url_for("my_matrices"))

        return render_template("my_matrices.html", matrices=matrices, form=form)

    @classmethod
    def included_tweets(cls, matrix_id):
        """show all tweets in the matrix"""
        c_matrix = ConfusionMatrix.query.get(matrix_id)
        title = "Included tweets"
        # filter according to the threshold
        id_c = [
            {
                int(k): {
                    "probability": v["probability"],
                    "relative probability": v["relative probability"],
                    "pred_cat": v["pred_cat"],
                    "class": v["class"],
                }
                for k, v in c_matrix.matrix_data.items()
                if v["probability"] >= c_matrix.threshold and v["class"] != "undefined"
            }
        ][0]

        tweets = Tweet.query.filter(Tweet.id.in_(id_c.keys())).all()  # pylint: disable=no-member
        # collect necessary data for the table
        cm_info = {
            t.id: {
                "text": t.full_text,
                "category": t.handle,
                "predicted category": id_c[t.id]["pred_cat"],
                "probability": round(id_c[t.id]["probability"], 3),
                "relative probability": id_c[t.id]["relative probability"],
            }
            for t in tweets
        }

        cm_info = sorted(
            [t for t in cm_info.items()],  # pylint: disable=unnecessary-comprehension
            key=lambda x: x[1]["probability"],
            reverse=True,
        )
        cm_info = [t[1] for t in cm_info]
        return render_template("matrix_tweets.html", cm_info=cm_info, matrix=c_matrix, title=title)

    @classmethod
    def excluded_tweets(cls, matrix_id):
        """show excluded tweets in the matrix"""
        c_matrix = ConfusionMatrix.query.get(matrix_id)
        title = "Excluded tweets"
        # filter according to the threshold (or if prediction is undefined)
        id_c = [
            {
                int(k): {
                    "probability": v["probability"],
                    "relative probability": v["relative probability"],
                    "pred_cat": v["pred_cat"],
                    "class": v["class"],
                }
                for k, v in c_matrix.matrix_data.items()
                if v["probability"] < c_matrix.threshold or v["class"] == "undefined"
            }
        ][0]

        tweets = Tweet.query.filter(Tweet.id.in_(id_c.keys())).all()  # pylint: disable=no-member
        # collect necessary data for the table
        cm_info = {
            t.id: {
                "text": t.full_text,
                "category": t.handle,
                "predicted category": id_c[t.id]["pred_cat"],
                "probability": round(id_c[t.id]["probability"], 3),
                "relative probability": id_c[t.id]["relative probability"],
            }
            for t in tweets
        }

        cm_info = sorted(
            [t for t in cm_info.items()],  # pylint: disable=unnecessary-comprehension
            key=lambda x: x[1]["probability"],
            reverse=True,
        )
        cm_info = [t[1] for t in cm_info]
        return render_template("matrix_tweets.html", cm_info=cm_info, matrix=c_matrix, title=title)

    @classmethod
    def matrix_overview(cls):
        """show all matrices"""
        userid = current_user.id  # get matrices for the user
        matrices = ConfusionMatrix.query.filter(ConfusionMatrix.user == userid).all()
        all_cats = TweetTagCategory.query.all()

        matrix_info = {
            m.id: {
                "accuracy": m.data["accuracy"],
                "threshold": m.threshold,
                "ratio": m.ratio,
                "categories": [", ".join([c.name for c in m.categories][0:])][0],
                "excluded tweets (%)": round(
                    m.data["nr_excl_tweets"] / m.data["nr_test_tweets"] * 100, 3
                ),
            }
            for m in matrices
        }
        matrix_info = sorted(
            [t for t in matrix_info.items()],
            key=lambda x: x[1]["accuracy"],
            reverse=True,  # pylint: disable=unnecessary-comprehension
        )
        matrix_info = [m[1] for m in matrix_info]
        form = ThresholdForm()
        return render_template(
            "matrix_overview.html",
            matrices=matrices,
            matrix_info=matrix_info,
            form=form,
            userid=userid,
            all_cats=all_cats,
        )

    @classmethod
    def aggregate_matrix(
        cls,
    ):  # pylint: disable=too-many-locals, too-many-statements, too-many-branches
        """aggregate the matrix data"""
        args = request.args.to_dict()
        m_id = args["matrix_id"]
        c_matrix = ConfusionMatrix.query.get(int(m_id))

        if "n" in request.args.to_dict().keys():
            n = request.args.get("n", type=int)  # pylint: disable=invalid-name
        else:
            n = 3  # pylint: disable=invalid-name

        used_tnt_sets = []  # log used tnt sets
        agg_data = {m: {"data": {}} for m in range(n)}
        accuracy_list = []
        metrics_list = []
        list_excluded = []
        list_included = []
        counts_list = []
        cat_names = [n.name for n in c_matrix.categories]

        # this loop creates a new matrix for each iteration
        for i in range(n):
            new_mx = c_matrix.clone()
            db_session.add(new_mx)
            db_session.flush()
            db_session.commit()
            tnt_sets = new_mx.training_and_test_sets
            # select a new
            tnt_list = [
                x
                for x in list(range(0, len(c_matrix.training_and_test_sets)))
                if x not in used_tnt_sets
            ]

            tnt_nr = sample(tnt_list, 1)[0]
            used_tnt_sets.append(tnt_nr)  # log used sets
            a_tnt_set = tnt_sets[tnt_nr]
            train_tweet_ids = a_tnt_set[0].keys()
            train_set_size = len(a_tnt_set[0].keys())
            test_tweets = [Tweet.query.get(tweet_id) for tweet_id in a_tnt_set[1].keys()]

            # train on the training set:
            new_mx.train_data = new_mx.train_model(train_tweet_ids)
            flag_modified(new_mx, "train_data")
            db_session.flush()

            # make matrix data
            matrix_data = new_mx.make_matrix_data(test_tweets, cat_names)
            new_mx.matrix_data = {i[0]: i[1] for i in matrix_data}

            flag_modified(new_mx, "matrix_data")
            db_session.flush()

            # filter according to the threshold
            incl_tweets = sorted(
                [
                    t
                    for t in new_mx.matrix_data.items()
                    if t[1]["probability"] >= c_matrix.threshold and t[1]["class"] != "undefined"
                ],
                key=lambda x: x[1]["probability"],
                reverse=True,
            )
            excl_tweets = sorted(
                [
                    t
                    for t in new_mx.matrix_data.items()
                    if t[1]["probability"] < c_matrix.threshold or t[1]["class"] == "undefined"
                ],
                key=lambda x: x[1]["probability"],
                reverse=True,
            )

            list_excluded.append(len(excl_tweets))
            list_included.append(len(incl_tweets))

            # count different occurences
            class_list = [t[1]["class"] for t in incl_tweets]
            class_list_all = []
            for cat_name in cat_names:
                for cat in cat_names:
                    class_list_all.append(str("Pred_" + str(cat_name) + "_Real_" + str(cat)))
                    class_list_all.append(str("Pred_" + str(cat) + "_Real_" + str(cat_name)))
            class_list_all = list(set(class_list_all))
            matrix_classes = {c: 0 for c in class_list_all}
            for i in set(class_list):
                matrix_classes[i] = class_list.count(i)

            true_keys = [str("Pred_" + i + "_Real_" + i) for i in cat_names]
            true_dict = dict(
                filter(lambda item: item[0] in true_keys, matrix_classes.items())
            )  # pylint: disable=cell-var-from-loop

            # accuracy = sum(correct predictions)/sum(all matrix points)
            accuracy = round((sum(true_dict.values()) / sum(matrix_classes.values())), 3)
            accuracy_list.append(accuracy)
            # precision and recall
            metrics = matrix_metrics(cat_names, matrix_classes)

            # summarise data
            new_mx.data = {
                "matrix_classes": matrix_classes,
                "accuracy": accuracy,
                "metrics": metrics,
                "nr_test_tweets": len(test_tweets),
                "nr_train_tweets": train_set_size,
                "nr_incl_tweets": len(incl_tweets),
                "nr_excl_tweets": len(excl_tweets),
            }
            flag_modified(new_mx, "data")
            db_session.add(new_mx)
            db_session.merge(new_mx)
            db_session.flush()
            db_session.commit()
            metrix = new_mx.data["metrics"].items()
            metrix = sorted(
                [t for t in new_mx.data["metrics"].items()],
                key=lambda x: x[1]["recall"],
                reverse=True,  # pylint: disable=unnecessary-comprehension
            )
            metrix = [t[1] for t in metrix]
            metrics_list.append(metrix)
            agg_data[i]["data"] = new_mx.data
            # build matrix data
            current_data_class = [
                new_mx.matrix_data[i].get("real_cat") for i in new_mx.matrix_data.keys()
            ]
            predicted_class = [
                new_mx.matrix_data[i].get("pred_cat") for i in new_mx.matrix_data.keys()
            ]
            number_list = list(range(len(cat_names)))

            for i in number_list:
                for k in range(len(current_data_class)):  # pylint: disable=consider-using-enumerate
                    if current_data_class[k] == cat_names[i]:
                        current_data_class[k] = i + 1
            for i in number_list:
                for k in range(len(predicted_class)):  # pylint: disable=consider-using-enumerate
                    if predicted_class[k] == cat_names[i]:
                        predicted_class[k] = i + 1
            # find number of classes
            classes = int(max(current_data_class) - min(current_data_class)) + 1
            counts = [
                [
                    sum(  # pylint: disable=consider-using-generator
                        [
                            (current_data_class[i] == true_class)
                            and (predicted_class[i] == pred_class)
                            for i in range(len(current_data_class))
                        ]
                    )
                    for pred_class in range(1, classes + 1)
                ]
                for true_class in range(1, classes + 1)
            ]
            counts_list.append(counts)

        # accuracy, excluded, included
        averages = [
            round(sum(accuracy_list) / len(accuracy_list), 3),
            round(sum(list_included) / len(list_included), 2),
            round(sum(list_excluded) / n, 2),
        ]
        avg_metrix = [
            [
                metrics_list[0][0]["category"],
                round(sum(i[0]["recall"] for i in metrics_list) / len(metrics_list), 3),
                round(sum(i[0]["precision"] for i in metrics_list) / len(metrics_list), 3),
            ],
            [
                metrics_list[0][1]["category"],
                round(sum(i[1]["recall"] for i in metrics_list) / len(metrics_list), 3),
                round(sum(i[1]["precision"] for i in metrics_list) / len(metrics_list), 3),
            ],
        ]
        # quadrants
        avg_quadrants = {}
        quadrants = [agg_data[m]["data"]["matrix_classes"] for m in agg_data]
        for dictionary in quadrants:
            for key, value in dictionary.items():
                if key in avg_quadrants:
                    avg_quadrants[key] = value + avg_quadrants[key]
                else:
                    avg_quadrants[key] = value
        avg_quadrants = [round(m / n, 3) for m in avg_quadrants.values()]
        # get info from each iteration to show how it varies
        loop_table = [
            [i + 1, accuracy_list[i], list_included[i], list_excluded[i]] for i in range(n)
        ]
        count_sum = [
            [
                [counts_list[j][l][i] + counts_list[j][l][i] for i in range(len(counts_list[0]))]
                for l in range(len(counts_list[0]))
            ]
            for j in range(len(counts_list))
        ][0]
        matrix_values = [
            [round(count_sum[i][j] / len(counts_list), 2) for j in range(len(count_sum[i]))]
            for i in range(len(count_sum))
        ]
        for i in range(len(matrix_values)):  # pylint: disable=consider-using-enumerate
            matrix_values[i].insert(0, cat_names[i])
        # add cell indices
        for i in range(len(matrix_values)):  # pylint: disable=consider-using-enumerate
            j = 0
            for k in range(len(matrix_values[i])):
                matrix_values[i][k] = [matrix_values[i][k], (i, 0 + j)]
                j += 1
        matrix_values = matrix_css_info(matrix_values)
        return jsonify(avg_quadrants, averages, n, loop_table, matrix_values, avg_metrix)

    @classmethod
    def get_matrix_categories(cls):
        """Get matrix categories."""
        args = request.args.to_dict()
        m_id = args["matrix_id"]
        c_matrix = ConfusionMatrix.query.get(int(m_id))

        cat_ids = [c.id for c in c_matrix.categories]
        cat_names = [c.name for c in c_matrix.categories]
        all_cats = TweetTagCategory.query.all()
        new_cats = [[i.id, i.name] for i in all_cats if i.id not in cat_ids]
        return jsonify(cat_ids, cat_names, new_cats)

    @classmethod
    def get_compare_matrix_data(
        cls,
    ):  # pylint: disable=too-many-locals, too-many-statements, too-many-branches
        """Get matrix data."""
        args = request.args.to_dict()
        m_id = args["matrix_id"]
        alt_cat = args["alt_cat"]
        new_cat = args["new_cat"]
        c_matrix = ConfusionMatrix.query.get(int(m_id))
        alt_cat = TweetTagCategory.query.get(int(alt_cat))
        new_cat = TweetTagCategory.query.get(int(new_cat))
        # cat ids for the two matrices
        old_cats = [c.id for c in c_matrix.categories]
        cat_ids = [new_cat.id if x == alt_cat.id else x for x in old_cats]

        # create a new matrix with the new category
        matrix2 = add_matrix(cat_ids, ratio=c_matrix.ratio, userid="")
        matrix2.threshold = c_matrix.threshold
        flag_modified(matrix2, "threshold")
        db_session.add(matrix2)
        db_session.merge(matrix2)
        db_session.flush()
        db_session.commit()  # not sure if this is necessary

        tnt_sets = matrix2.training_and_test_sets

        # select a new
        tnt_list = [
            x for x in list(range(0, len(matrix2.training_and_test_sets)))
        ]  # pylint: disable=unnecessary-comprehension
        tnt_nr = sample(tnt_list, 1)[0]
        a_tnt_set = tnt_sets[tnt_nr]
        train_tweet_ids = a_tnt_set[0].keys()
        train_set_size = len(a_tnt_set[0].keys())
        test_tweets = [Tweet.query.get(tweet_id) for tweet_id in a_tnt_set[1].keys()]

        # train on the training set:
        matrix2.train_data = matrix2.train_model(train_tweet_ids)
        flag_modified(matrix2, "train_data")

        # make matrix data
        cat_names = [c.name for c in matrix2.categories]
        matrix_data = matrix2.make_matrix_data(test_tweets, cat_names)
        matrix2.matrix_data = {i[0]: i[1] for i in matrix_data}
        flag_modified(matrix2, "matrix_data")

        # filter according to the threshold
        incl_tweets = sorted(
            [
                t
                for t in matrix2.matrix_data.items()
                if t[1]["probability"] >= c_matrix.threshold and t[1]["class"] != "undefined"
            ],
            key=lambda x: x[1]["probability"],
            reverse=True,
        )
        excl_tweets = sorted(
            [
                t
                for t in matrix2.matrix_data.items()
                if t[1]["probability"] < c_matrix.threshold or t[1]["class"] == "undefined"
            ],
            key=lambda x: x[1]["probability"],
            reverse=True,
        )

        # count different occurences
        class_list = [t[1]["class"] for t in incl_tweets]
        class_list_all = []
        for cat_name in cat_names:
            for cat in cat_names:
                class_list_all.append(str("Pred_" + str(cat_name) + "_Real_" + str(cat)))
                class_list_all.append(str("Pred_" + str(cat) + "_Real_" + str(cat_name)))
        class_list_all = list(set(class_list_all))
        matrix_classes = {c: 0 for c in class_list_all}
        for i in set(class_list):
            matrix_classes[i] = class_list.count(i)

        true_keys = [str("Pred_" + i + "_Real_" + i) for i in cat_names]
        true_dict = dict(filter(lambda item: item[0] in true_keys, matrix_classes.items()))

        # accuracy = sum(correct predictions)/sum(all matrix points)
        accuracy = round((sum(true_dict.values()) / sum(matrix_classes.values())), 3)
        # precision and recall
        metrics = matrix_metrics(cat_names, matrix_classes)

        # summarise data
        matrix2.data = {
            "matrix_classes": matrix_classes,
            "accuracy": accuracy,
            "metrics": metrics,
            "nr_test_tweets": len(test_tweets),
            "nr_train_tweets": train_set_size,
            "nr_incl_tweets": len(incl_tweets),
            "nr_excl_tweets": len(excl_tweets),
        }
        flag_modified(matrix2, "data")
        db_session.add(matrix2)
        db_session.merge(matrix2)
        db_session.flush()
        db_session.commit()

        # prepare data for matrix table
        old_names = [c.name for c in c_matrix.categories]
        counts1 = c_matrix.make_table_data(old_names)
        counts2 = matrix2.make_table_data(cat_names)
        for i in range(len(counts1)):  # pylint: disable=consider-using-enumerate
            counts1[i].insert(0, old_names[i])
        for i in range(len(counts2)):  # pylint: disable=consider-using-enumerate
            counts2[i].insert(0, cat_names[i])
        for i in range(len(counts1)):  # pylint: disable=consider-using-enumerate
            j = 0
            for k in range(len(counts1[i])):
                counts1[i][k] = [counts1[i][k], (i, 0 + j)]
                j += 1
        for i in range(len(counts2)):  # pylint: disable=consider-using-enumerate
            j = 0
            for k in range(len(counts2[i])):
                counts2[i][k] = [counts2[i][k], (i, 0 + j)]
                j += 1

        table_data = [
            [m.id, m.data["accuracy"], m.data["nr_incl_tweets"], m.data["nr_excl_tweets"]]
            for m in [c_matrix, matrix2]
        ]
        # for the jquery confusion matrix with colors
        counts1 = matrix_css_info(counts1)
        counts2 = matrix_css_info(counts2)

        # precision and accuracy table
        metrics = [list(c_matrix.data["metrics"][cat].values()) for cat in old_names], [
            list(matrix2.data["metrics"][cat].values()) for cat in cat_names
        ]

        return jsonify(counts1, counts2, c_matrix.threshold, c_matrix.ratio, table_data, metrics)

    @classmethod
    def compare_matrices(cls):
        """Compare matrices."""
        # there you can try out the comparison templates
        userid = current_user.id
        all_cats = TweetTagCategory.query.all()
        matrices = ConfusionMatrix.query.filter(ConfusionMatrix.user == userid).all()
        cat_names = [c.name for c in all_cats]

        return render_template(
            "matrix_compare_base.html", cat_names=cat_names, matrices=matrices, all_cats=all_cats
        )

    # this is not used rn
    # here you need the analysis in request args!

    @classmethod
    def tweet_annotation(cls):
        """Tweet annotation."""
        analysis_id = request.args.get("analysis", 0, type=int)  # pylint: disable=no-member
        bayes_analysis = BayesianAnalysis.query.get(analysis_id)
        a_project = Project.query.get(bayes_analysis.project)
        tweets = a_project.tweets  # Tweet.query.all()
        categories = a_project.categories  # TweetTagCategory.query.all()
        tweet_table = {}
        # if category in request_dict_keys

        if "cat" in request.args.to_dict().keys():  # pylint: disable=no-member
            cat_id = request.args.get("cat", type=int)  # pylint: disable=no-member
            tweets = Tweet.query.filter(Tweet.category == cat_id)
            tweet_table = {
                t.id: {"tweet": t.full_text, "category": t.handle, "id": t.id} for t in tweets
            }
            tweet_table = sorted(
                [t for t in tweet_table.items()],
                key=lambda x: x[1]["id"],
                reverse=True,  # pylint: disable=unnecessary-comprehension
            )
            tweet_table = [t[1] for t in tweet_table]

        if request.method == "POST" and "select-category" in request.form.to_dict():
            myargs = request.form.to_dict()
            cat_id = myargs["select-category"]
            tweets = Tweet.query.filter(Tweet.category == cat_id)
            tweet_table = {
                t.id: {"tweet": t.full_text, "category": t.handle, "id": t.id} for t in tweets
            }
            tweet_table = sorted(
                [t for t in tweet_table.items()],
                key=lambda x: x[1]["id"],
                reverse=True,  # pylint: disable=unnecessary-comprehension
            )
            tweet_table = [t[1] for t in tweet_table]
            return redirect(url_for("tweet_annotation", analysis=bayes_analysis.id, cat=cat_id))

        return render_template(
            "tweet_annotate.html",
            tweet_table=tweet_table,
            categories=categories,
            analysis=bayes_analysis,
        )

    # showing all annotations in an analysis, from all users ==> useful in
    # shared projects

    @classmethod
    def annotation_summary(
        cls, analysis_id
    ):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Annotation summary."""

        bayes_analysis = BayesianAnalysis.query.get(analysis_id)
        all_tags = list(bayes_analysis.annotation_tags.keys())

        if request.method == "POST" and "select-tag" in request.form.to_dict():
            myargs = request.form.to_dict()
            new_tag = myargs["select-tag"]
            return redirect(
                url_for("annotation_summary", analysis_id=bayes_analysis.id, tag=new_tag)
            )

        # get annotations by selected tag
        a_tag: str
        if "tag" in request.args.to_dict():
            a_tag = str(request.args.get("tag", type=str))
        else:
            a_tag = all_tags[0]

        # relevant annotations for a_tag
        tag_anns = TweetAnnotation.query.filter(
            TweetAnnotation.annotation_tag == a_tag, TweetAnnotation.analysis == analysis_id
        ).all()
        tagged_tweets = list(
            set([t.tweet for t in tag_anns])
        )  # pylint: disable=consider-using-set-comprehension

        tag_table = {t: {"tweet": t} for t in tagged_tweets}
        for twit in tagged_tweets:
            t_anns = (
                TweetAnnotation.query.filter(TweetAnnotation.annotation_tag == a_tag.lower())
                .filter(TweetAnnotation.tweet == twit)
                .all()
            )
            users = len(
                set([i.user for i in t_anns])
            )  # pylint: disable=consider-using-set-comprehension
            tag_table[twit]["tag_count"] = len(t_anns)
            tag_table[twit]["users"] = users
        tag_table = sorted(
            [t for t in tag_table.items()],  # pylint: disable=unnecessary-comprehension
            key=lambda x: x[1]["tweet"],
            reverse=True,
        )
        tag_table = [t[1] for t in tag_table]

        # do the same for all tags:
        tagdict = {t: {"tag": t} for t in all_tags}

        for tag in all_tags:
            tag_anns = TweetAnnotation.query.filter(
                TweetAnnotation.annotation_tag == tag.lower()
            ).all()
            tagdict[tag]["tag_count"] = len(tag_anns)
            tagdict[tag]["users"] = len(
                set([an.user for an in tag_anns])
            )  # pylint: disable=consider-using-set-comprehension
            tagged_tweets = list(
                set([t.tweet for t in tag_anns])
            )  # pylint: disable=consider-using-set-comprehension
            tagdict[tag]["nr_tweets"] = len(tagged_tweets)
        alltag_table = sorted(
            [t for t in tagdict.items()],
            key=lambda x: x[1]["nr_tweets"],
            reverse=True,  # pylint: disable=unnecessary-comprehension
        )
        alltag_table = [t[1] for t in alltag_table]

        # now showing how many times each tag has been used (tag_count), NOT by
        # how many users (change to 'users')
        chart_data = create_bar_chart_data(
            {tag: tagdict[tag]["tag_count"] for tag in all_tags}, title="Annotation tags"
        )

        tags = bayes_analysis.annotation_tags  # not sure if this is needed
        # the_tag = request.args.get('tag', type=str)
        # get all tweets with a specific tag
        tweets = tags[a_tag]["tweets"]

        # all annotations in the analysis, third tab
        all_tag_anns = TweetAnnotation.query.filter(TweetAnnotation.analysis == analysis_id).all()
        a_list = set(
            [a.tweet for a in all_tag_anns]
        )  # pylint: disable=consider-using-set-comprehension
        # list(set([t.tweet for t in all_tag_anns]))
        all_tagged_tweets = Tweet.query.filter(
            Tweet.id.in_(a_list)
        ).all()  # pylint: disable=no-member

        return render_template(
            "annotation_summary.html",
            ann_table=tag_table,
            analysis=bayes_analysis,
            tag=a_tag,
            all_tags=all_tags,
            allann_table=chart_data,
            tweets=tweets,
            tagged_tweets=tagged_tweets,
            all_tagged_tweets=all_tagged_tweets,
        )

    # annotations by user
    # @TODO: Maybe? a similar tab but without filtering by user?
    # ==> would be interesting to see all tags in a tweet
    # however, remember to check that only own tags can be deleted (delete form)
    # AH: when it is a shared analysis, we should be able to see all of them

    @classmethod
    def annotations(cls):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Show all annotations by user."""
        page = request.args.get("page", 1, type=int)
        analysis_id = request.args.to_dict()["analysis_id"]  # , 0, type=int)
        bayes_analysis = BayesianAnalysis.query.get(analysis_id)
        shared = bayes_analysis.shared
        a_project = Project.query.get(bayes_analysis.project)
        anns = []
        if shared:
            anns = TweetAnnotation.query.filter(TweetAnnotation.analysis == analysis_id).all()
        else:
            anns = TweetAnnotation.query.filter(
                TweetAnnotation.analysis == analysis_id, TweetAnnotation.user == current_user.id
            ).all()
        a_list = set([a.tweet for a in anns])  # pylint: disable=consider-using-set-comprehension
        tweets = Tweet.query.filter(Tweet.id.in_(a_list)).all()  # pylint: disable=no-member

        ann_info = {
            a.id: {"annotation": a.text, "tag": a.annotation_tag, "user": a.user} for a in anns
        }
        print(ann_info)

        ann_dict = (
            bayes_analysis.annotation_counts(tweets, current_user.id)
            if not shared
            else bayes_analysis.annotation_counts(tweets, "all")
        )

        word_tuples = []
        ann_tags = [c.name for c in a_project.categories]
        for tag in list(bayes_analysis.annotation_tags.keys()):
            if tag not in ann_tags:
                ann_tags.append(tag)
        for a_tweet in tweets:
            mytagcounts = get_tags(bayes_analysis, set(a_tweet.words), a_tweet)
            myanns = TweetAnnotation.query.filter(TweetAnnotation.tweet == a_tweet.id).all()
            my_tuples = ann_create_css_info(mytagcounts, a_tweet.full_text, ann_tags, myanns)
            word_tuples.append(my_tuples)

        ann_list = (
            Tweet.query.join(TweetAnnotation, (TweetAnnotation.tweet == Tweet.id))
            .filter(TweetAnnotation.user == current_user.id)
            .filter_by(analysis=analysis_id)
            .order_by(Tweet.id)
            .distinct()
            .paginate(page, per_page=1)
        )

        next_url = (
            url_for("annotations", analysis_id=analysis_id, page=ann_list.next_num)
            if ann_list.has_next
            else None
        )
        prev_url = (
            url_for("annotations", analysis_id=analysis_id, page=ann_list.prev_num)
            if ann_list.has_prev
            else None
        )

        return render_template(
            "annotations.html",
            anns=ann_list.items,
            next_url=next_url,
            prev_url=prev_url,
            word_tuples=word_tuples,
            page=page,
            analysis=bayes_analysis,
            ann_dict=ann_dict,
        )

    # new jquery way for 'annotations.html'
    # didn't get this to entirely work, not used now

    @classmethod
    def tweet_annotations(
        cls,
    ):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Show all annotations by user."""
        args = request.args.to_dict()
        analysis_id = int(args["analysis_id"])
        tweet_id = int(args["tweet_id"])
        bayes_analysis = BayesianAnalysis.query.get(analysis_id)
        a_tweet = Tweet.query.get(tweet_id)
        a_project = Project.query.get(bayes_analysis.project)
        anns = TweetAnnotation.query.filter(
            TweetAnnotation.tweet == tweet_id, TweetAnnotation.analysis == analysis_id
        ).all()
        a_list = set([a.tweet for a in anns])  # pylint: disable=consider-using-set-comprehension
        tweets = Tweet.query.filter(Tweet.id.in_(a_list)).all()  # pylint: disable=no-member
        ann_dict = bayes_analysis.annotation_counts(tweets, "all")
        tweet_ids = []
        ann_tags = [c.name for c in a_project.categories]
        for tag in list(bayes_analysis.annotation_tags.keys()):
            if tag not in ann_tags:
                ann_tags.append(tag)

        mytagcounts = get_tags(bayes_analysis, set(a_tweet.words), a_tweet)
        # TweetAnnotation.query.filter(TweetAnnotation.tweet==a_tweet.id).all()
        myanns = anns
        my_tuples = ann_create_css_info(mytagcounts, a_tweet.full_text, ann_tags, myanns)
        # word_tuples.append(my_tuples)
        tweet_ids.append(a_tweet.id)

        return jsonify(my_tuples, tweet_ids, ann_dict)

    # saving the annotation by word position
    # @TODO: figure out a better way, now the word before gets saved sometimes..

    @classmethod
    def save_annotation(
        cls,
    ):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Save annotation."""
        args = request.args.to_dict()  # pylint: disable=no-member
        t_id = int(args["tweet_id"])
        twit = Tweet.query.get(t_id)
        text = str(args["text"])
        atag = str(args["atag"])
        print(atag)
        pos = int(args["pos"])
        pos2 = int(args["pos2"])
        analysis_id = int(args["analysis"])
        bayes_analysis = BayesianAnalysis.query.get(analysis_id)
        bayes_analysis.updated_a_tags(atag, twit)
        flag_modified(bayes_analysis, "annotation_tags")
        db_session.add(bayes_analysis)
        db_session.merge(bayes_analysis)
        db_session.flush()
        db_session.commit()

        coordinates = {}
        # end and start word position
        txtstart = min(pos, pos2)
        txtend = max(pos, pos2)

        words = twit.full_text.split()
        word_locs = {}

        word_count = 0
        for wrd in range(len(words)):  # pylint: disable=consider-using-enumerate
            word_locs[word_count] = words[wrd]
            word_count += 1
        # a word list of the words in the annotation
        words = [
            re.sub(r"[^\w\s]", "", w)
            for w in text.lower().split()
            if "#" not in w and "http" not in w and "@" not in w
        ]  # text.split()
        # coordinates of all words in the tweet
        coordinates["word_locs"] = word_locs

        # make a list of locations in-between
        loc_list = list(range(txtstart, txtend + 1))
        # save annotation coordinates  + [original, cleaned word]
        # for each highlighted word in the annotation
        # later used for the css info
        coords = {}
        for loc in loc_list:
            coords[loc] = [
                coordinates["word_locs"][loc],
                re.sub(r"[^\w\s]", "", coordinates["word_locs"][loc].lower()),
            ]
        coordinates["txt_coords"] = coords

        annotation = TweetAnnotation(
            user=current_user.id,
            text=text,
            analysis=analysis_id,
            tweet=t_id,
            coordinates=coordinates,
            words=words,
            annotation_tag=atag.lower(),
        )
        db_session.add(annotation)
        db_session.commit()

        ann_tags = [c.name for c in Project.query.get(bayes_analysis.project).categories]
        for tag in list(bayes_analysis.annotation_tags.keys()):
            if tag not in ann_tags:
                ann_tags.append(tag)
        mytagcounts = get_tags(bayes_analysis, set(twit.words), twit)
        myanns = TweetAnnotation.query.filter(
            TweetAnnotation.tweet == twit.id, TweetAnnotation.user == current_user.id
        ).all()
        my_tuples = ann_create_css_info(
            mytagcounts, twit.full_text, ann_tags, myanns
        )  # tuples for the css info

        return jsonify(my_tuples)

    # save the dragged tweet category guess

    @classmethod
    def draggable(cls):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Save draggable tweet."""
        args = request.args.to_dict()
        print(args)
        t_id = int(args["tweet_id"])
        this_tweet = Tweet.query.get(t_id)
        bayes_analysis = BayesianAnalysis.query.get(int(args["analysis_id"]))
        a_project = Project.query.get(bayes_analysis.project)
        cat = str(args["category"])
        category = TweetTagCategory.query.filter(TweetTagCategory.name == cat).first()

        print("hep1")

        # save the prediction
        bayes_analysis.data = bayes_analysis.updated_data(this_tweet, category)
        # all this  stuff is necessary  because the database backend doesnt resgister
        # changes on JSON
        flag_modified(bayes_analysis, "data")
        db_session.add(bayes_analysis)
        db_session.merge(bayes_analysis)
        db_session.flush()
        db_session.commit()
        print("hep2")
        tag = TweetTag(
            category=category.id,
            analysis=bayes_analysis.id,
            tweet=this_tweet.id,
            user=current_user.id,
        )
        db_session.add(tag)
        db_session.commit()

        # show a new tweet
        categories = TweetTagCategory.query.filter(
            TweetTagCategory.id.in_(
                [p.id for p in a_project.categories]
            )  # pylint: disable=no-member
        ).all()  # @TODO: pretty sure we can just get project.categories
        # tweets = project.tweets # AH: this is where we need to do something
        # faster
        the_tweet = None
        print(the_tweet)
        if bayes_analysis.shared:
            completed_tweets = [t.tweet for t in bayes_analysis.tags if t.user == current_user.id]
            uncompleted_tweets = [t for t in bayes_analysis.tweets if t not in completed_tweets]
            print(the_tweet.full_text)
            if len(uncompleted_tweets) > 0:
                the_tweet_id = uncompleted_tweets[0]
                the_tweet = Tweet.query.get(the_tweet_id)
            else:
                # create an alternative message
                the_tweet = Tweet(full_text="", words=[])
                return jsonify("the end")
        else:
            print("trying to get a random tweet")
            # so the same tweet might come again? # AH: this is where we need to do
            # something faster
            the_tweet = a_project.get_random_tweet()
            print(the_tweet.full_text)
            print("id", the_tweet.id)

        print(the_tweet.full_text)
        number_of_tagged = len(bayes_analysis.tags)
        data = {}
        data["number_of_tagged"] = number_of_tagged
        data["words"], data["predictions"] = bayes_analysis.get_predictions_and_words(
            set(the_tweet.words)
        )
        data["word_tuples"] = create_css_info(data["words"], the_tweet.full_text, categories)
        data["chart_data"] = create_bar_chart_data(data["predictions"], "Computeren gætter på...")
        # filter robots that are retired, and sort them alphabetically
        # data['robots'] = sorted(robots, key= lambda r: r.name)
        data["analysis_data"] = bayes_analysis.data

        return jsonify(data, the_tweet.id, the_tweet.time_posted)

    @classmethod
    def tweet(cls, tid):
        """Show a tweet."""
        twit = Tweet.query.get(tid)
        return jsonify(twit.full_text)

    # update the bar chart

    @classmethod
    def get_bar_chart_data(
        cls,
    ):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Get bar chart data."""
        args = request.args.to_dict()  # pylint: disable=no-member
        t_id = int(args["tweet_id"])
        this_tweet = Tweet.query.get(t_id)
        bayes_analysis = BayesianAnalysis.query.get(int(args["analysis_id"]))
        a_project = Project.query.get(bayes_analysis.project)
        categories = TweetTagCategory.query.filter(
            TweetTagCategory.id.in_(
                [p.id for p in a_project.categories]
            )  # pylint: disable=no-member
        ).all()  # project.categories

        number_of_tagged = len(bayes_analysis.tags)
        data = {}
        data["number_of_tagged"] = number_of_tagged
        data["words"], data["predictions"] = bayes_analysis.get_predictions_and_words(
            set(this_tweet.words)
        )
        data["word_tuples"] = create_css_info(data["words"], this_tweet.full_text, categories)
        data["chart_data"] = create_bar_chart_data(data["predictions"], "Computeren gætter på...")
        # filter robots that are retired, and sort them alphabetically

        return jsonify(data)

    # when loading the analysis page
    # load a tweet to show

    @classmethod
    def get_first_tweet(cls):
        """Get first tweet."""
        print("get first tweet called")
        args = request.args.to_dict()
        bayes_analysis = BayesianAnalysis.query.get(int(args["analysis_id"]))
        a_project = Project.query.get(bayes_analysis.project)
        # show a new tweet
        categories = TweetTagCategory.query.filter(
            TweetTagCategory.id.in_(
                [p.id for p in a_project.categories]
            )  # pylint: disable=no-member
        ).all()  # @TODO: pretty sure we can just get project.categories
        # tweets = project.tweets
        the_tweet = None
        if bayes_analysis.shared:
            completed_tweets = [t.tweet for t in bayes_analysis.tags if t.user == current_user.id]
            uncompleted_tweets = [t for t in bayes_analysis.tweets if t not in completed_tweets]
            if len(uncompleted_tweets) > 0:
                the_tweet_id = uncompleted_tweets[0]
                the_tweet = Tweet.query.get(the_tweet_id)
            else:
                # create an alternative message
                the_tweet = Tweet(full_text="", words=[])
                return jsonify("the end")
        else:
            # sample(tweets, 1)[0] # so the same tweet might come again?
            the_tweet = a_project.get_random_tweet()
        number_of_tagged = len(bayes_analysis.tags)
        data = {}
        data["number_of_tagged"] = number_of_tagged
        data["words"], data["predictions"] = bayes_analysis.get_predictions_and_words(
            set(the_tweet.words)
        )
        data["word_tuples"] = create_css_info(data["words"], the_tweet.full_text, categories)
        data["chart_data"] = create_bar_chart_data(data["predictions"], "Computeren gætter på...")
        # filter robots that are retired, and sort them alphabetically
        # data['robots'] = sorted(robots, key= lambda r: r.name)
        # data['analysis_data'] = analysis.data
        ann_tags = list(bayes_analysis.annotation_tags.keys())
        mytagcounts = get_tags(bayes_analysis, set(the_tweet.words), the_tweet)
        myanns = TweetAnnotation.query.filter(
            TweetAnnotation.tweet == the_tweet.id, TweetAnnotation.user == current_user.id
        ).all()
        # if there already are annotations
        if len(myanns) > 0:
            my_tuples = ann_create_css_info(mytagcounts, the_tweet.full_text, ann_tags, myanns)
        else:
            my_tuples = 0
        return jsonify(data, the_tweet.id, the_tweet.time_posted, my_tuples)

    @classmethod
    def highlight_tweet(cls, bayes_analysis):
        """Highlight tweet."""
        # add if tag in request.args.to_dict():
        bayes_analysis = BayesianAnalysis.query.get(bayes_analysis)
        tags = bayes_analysis.annotation_tags  # not sure if this is needed
        the_tag = request.args.get("tag", type=str)
        # get all tags with a specific tweet
        tweets = tags[the_tag]["tweets"]

        return render_template("annotations_per_tweet.html", the_tag=the_tag, tweets=tweets)

    @classmethod
    def jq_highlight_tweet(cls):
        """Jquery highlight tweet."""
        args = request.args.to_dict()
        t_id = int(args["tweet_id"])
        the_tag = str(args["the_tag"])

        the_tags = TweetAnnotation.query.filter(
            TweetAnnotation.tweet == t_id, TweetAnnotation.annotation_tag == the_tag
        ).all()
        pos_list = []
        for ann in the_tags:
            pos_list = pos_list + [
                k for k in ann.coordinates["txt_coords"].keys()
            ]  # pylint: disable=unnecessary-comprehension
        pos_dict = {}
        for pos in pos_list:
            if pos not in pos_dict:
                pos_dict[pos] = 1
            else:
                pos_dict[pos] += 1

        bg_tuples = create_ann_css_info(the_tags, pos_dict)

        return jsonify(bg_tuples)

    @classmethod
    def show_highlights(cls):
        """Show highlights."""
        args = request.args.to_dict()
        t_id = int(args["tweet_id"])
        analysis_id = int(args["analysis_id"])
        bayes_analysis = BayesianAnalysis.query.get(analysis_id)
        a_tweet = Tweet.query.get(t_id)

        ann_tags = list(bayes_analysis.annotation_tags.keys())

        mytagcounts = get_tags(bayes_analysis, set(a_tweet.words), a_tweet)
        myanns = TweetAnnotation.query.filter(TweetAnnotation.tweet == a_tweet.id).all()
        my_tuples = ann_create_css_info(mytagcounts, a_tweet.full_text, ann_tags, myanns)

        return jsonify(my_tuples)

    @classmethod
    def get_annotations(cls):
        """Get annotations."""
        args = request.args.to_dict()  # pylint: disable=no-member
        span_id = str(args["span_id"])
        t_id = int(args["tweet_id"])
        the_tweet = Tweet.query.get(t_id)
        analysis_id = int(args["analysis_id"])
        bayes_analysis = BayesianAnalysis.query.get(analysis_id)

        # filter relevant annotations
        myanns = TweetAnnotation.query.filter(
            TweetAnnotation.tweet == the_tweet.id,
            TweetAnnotation.user == current_user.id,
            TweetAnnotation.analysis == bayes_analysis.id,
        ).all()
        # if the key matches

        ann_list = [a for a in myanns if span_id in a.coordinates["txt_coords"].keys()]
        if len(ann_list) > 0:
            the_word = the_tweet.full_text.split()[int(span_id)]
            tagdict = {
                a.id: {"tag": a.annotation_tag, "text": " ".join(a.words), "id": a.id}
                for a in ann_list
            }
            alltag_table = sorted(
                [t for t in tagdict.items()],  # pylint: disable=unnecessary-comprehension
                key=lambda x: x[1]["tag"],
                reverse=True,
            )
            alltag_table = [t[1] for t in alltag_table]
        else:
            return jsonify("no annotations")

        return jsonify(alltag_table, the_word, current_user.id)

    @classmethod
    def delete_last_annotation(cls):
        """Delete last annotation."""
        print("delete last ")
        args = request.args.to_dict()  # pylint: disable=no-member
        t_id = int(args["tweet_id"])
        analysis_id = int(args["analysis"])

        # get all annotations
        myanns = TweetAnnotation.query.filter(
            TweetAnnotation.tweet == t_id,
            TweetAnnotation.user == current_user.id,
            TweetAnnotation.analysis == analysis_id,
        ).all()
        print(myanns)
        if len(myanns) > 0:
            # delete the last one
            ann_to_delete = myanns[-1]
            print(ann_to_delete)
            db_session.delete(ann_to_delete)
            db_session.commit()

        return jsonify({})

    @classmethod
    def delete_annotation(cls):
        """Delete annotation."""
        args = request.args.to_dict()
        span_id = str(args["span_id"])
        ann_id = str(args["ann_id"])
        ann = TweetAnnotation.query.get(ann_id)
        t_id = int(args["tweet_id"])
        the_tweet = Tweet.query.get(t_id)
        analysis_id = int(args["analysis_id"])
        bayes_analysis = BayesianAnalysis.query.get(analysis_id)

        # delete
        db_session.delete(ann)
        db_session.commit()

        # make new table data
        # filter relevant annotations
        myanns = TweetAnnotation.query.filter(
            TweetAnnotation.tweet == the_tweet.id,
            TweetAnnotation.user == current_user.id,
            TweetAnnotation.analysis == bayes_analysis.id,
        ).all()
        # if the key matches
        ann_list = [a for a in myanns if span_id in a.coordinates["txt_coords"].keys()]
        if len(ann_list) > 0:
            the_word = the_tweet.full_text.split()[int(span_id)]
            tagdict = {
                a.id: {"tag": a.annotation_tag, "text": " ".join(a.words), "id": a.id}
                for a in ann_list
            }
            alltag_table = sorted(
                [t for t in tagdict.items()],  # pylint: disable=unnecessary-comprehension
                key=lambda x: x[1]["tag"],
                reverse=True,
            )
            alltag_table = [t[1] for t in alltag_table]
        else:
            return jsonify("no annotations")

        return jsonify(alltag_table, the_word)

    @classmethod
    def precision_recall(cls):
        """precision recall table"""
        args = request.args.to_dict()
        m_id = args["matrix_id"]
        cat_names = args["cat_names"]
        c_matrix = ConfusionMatrix.query.get(int(m_id))

        counts = c_matrix.make_table_data(cat_names)
        [counts[i].insert(0, cat_names[i]) for i in range(len(counts))]
        index_list = []
        for i in range(len(counts)):
            p = cat_names[i]
            t = [str("Pred_" + counts[i][0] + "_Real_" + p) for i in range(len(counts))]
            index_list.append(t)
        [index_list[i].insert(0, cat_names[i]) for i in range(len(index_list))]
        index_list = [
            [[counts[j][i], index_list[j][i], (j, i)] for i in range(0, len(counts[j]))]
            for j in range(len(counts))
        ]
        index_list = matrix_css_info(index_list)

        metrics = sorted(
            [t for t in c_matrix.data["metrics"].items()],
            key=lambda x: x[1]["recall"],
            reverse=True,
        )
        metrics = [t[1] for t in metrics]
        return jsonify(index_list, metrics)
