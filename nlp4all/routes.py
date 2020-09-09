import os, time
import secrets
import nlp4all.utils
from random import sample, shuffle
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, jsonify
from nlp4all import app, db, bcrypt, mail
from nlp4all.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm, AddOrgForm, AddBayesianAnalysisForm, AddProjectForm, TaggingForm, AddTweetCategoryForm, AddTweetCategoryForm, AddBayesianRobotForm, TagButton, AddBayesianRobotFeatureForm, BayesianRobotForms, AddAnalysisForm
from nlp4all.models import User, Organization, Project, BayesianAnalysis, TweetTagCategory, TweetTag, BayesianRobot, Tweet, LogRegAnalysis
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import datetime
import json, ast
from sqlalchemy.orm.attributes import flag_modified
from nlp4all.utils import get_user_projects, get_user_project_analyses
import pandas as pd

@app.route("/")
@app.route("/home")
@app.route("/home/", methods=['GET', 'POST'])
@login_required
def home():
    my_projects = get_user_projects(current_user) 
    return render_template('home.html', projects=my_projects)


@app.route("/robot_summary", methods=['GET', 'POST'])
def robot_summary():
    analysis_id = request.args.get('analysis', 0, type=int)
    analysis = BayesianAnalysis.query.get(analysis_id)
    robots = [r for r in analysis.robots if r.retired]
    return render_template('robot_summary.html', analysis=analysis, robots=robots)

@app.route("/data_table")
def data_table():
    my_projects = get_user_projects(current_user) 
    test_data = [{'a' : 25, 'b': 200, 'c': 400}]
    test_data.append({'a' : 25, 'b': 200, 'c': 80})
    return render_template('data_table.html', table_data=test_data)

@app.route("/add_project", methods=['GET', 'POST'])
def add_project():
    form = AddProjectForm()
    # find forst alle mulige organizations
    form.organization.choices = [( str(o.id), o.name ) for o in Organization.query.all()]
    form.categories.choices = [( str(s.id), s.name ) for s in TweetTagCategory.query.all()]
    if form.validate_on_submit():
        # orgs = [int(n) for n in form.organization.data]
        # orgs_objs = Organization.query.filter(Organization.id.in_(orgs)).all()
        org = Organization.query.get(int(form.organization.data))
        cats = [int(n) for n in form.categories.data]
        project = nlp4all.utils.add_project(name=form.title.data, description=form.description.data, org=org.id, cat_ids=cats)
        project_id = project.id
        return(redirect(url_for('home', project=project_id)))
    return render_template('add_project.html', title='Add New Project', form=form)

@app.route("/project", methods=['GET', "POST"])
def project():
    project_id = request.args.get('project', None, type=int)
    project = Project.query.get(project_id)
    form = AddAnalysisForm()
    analyses = BayesianAnalysis.query.filter_by(user = current_user.id).filter_by(project=project_id).all()
    analyses = nlp4all.utils.get_user_project_analyses(current_user, project)
    if form.validate_on_submit():
        userid = current_user.id
        name = form.name.data
        method = form.method.data # type of analysis
        number_per_category = form.number.data
        analysis_tweets = [] 
        if form.shared.data:
            tweets_by_cat = {cat : [t.id for t in project.tweets if t.category == cat.id] for cat in project.categories}
            for cat, tweets in tweets_by_cat.items():
                analysis_tweets.extend(sample(tweets, number_per_category))
        # make sure all students see tweets in the same order. So shuffle them now, and then 
        # put them in the database
        shuffle(analysis_tweets)
        analysis = BayesianAnalysis(user = userid, name=name, project=project.id, data = {"counts" : 0, "words" : {}}, shared=form.shared.data, tweets=analysis_tweets , method=method)
        db.session.add(analysis)
        db.session.commit()
        return(redirect(url_for('project', project=project_id)))
    return render_template('project.html', title='About', project=project, analyses=analyses, form=form)


@app.route("/test", methods=['GET', 'POST'])
def test():

    return render_template('test.html', title='Test', buttons=[])


@app.route('/_add_numbers')
def add_numbers():
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    return jsonify(result=a + b)
    
@app.route("/ajax")
def ajax():
    o = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    number = a + b
    return render_template('ajax.html', title='Test')


@app.route("/robot", methods=['GET', 'POST'])
def robot():
    # first get user's robot associated with
    robot_id = request.args.get('robot', 0, type=int)
    # find the analysis and check if it belongs to the user
    robot = BayesianRobot.query.get(robot_id)
    if robot.retired:
        acc_dict = robot.accuracy
        if robot.parent != None:
            parent_robot = BayesianRobot.query.get(robot.parent)
            parent_accuracy = parent_robot.accuracy
            acc_dict['parent_accuracy'] = parent_accuracy['accuracy']
            acc_dict['parent_tweets_targeted'] = parent_accuracy['tweets_targeted']
    else:
        acc_dict = {'features' : [], 'accuracy' : 0, 'tweets_targeted' : 0, 'features' : {}, 'table_data' : []}
    if request.method == "POST" and 'delete' in request.form.to_dict():
        del robot.features[request.form.to_dict()['delete']]
        flag_modified(robot, "features")
        db.session.add(robot)
        db.session.merge(robot)
        db.session.flush()
        db.session.commit()
        redirect(url_for('robot', robot=robot_id))
    form = BayesianRobotForms()
    if request.method == "POST" and 'add_feature_form-submit' in request.form.to_dict():
        if " " not in form.add_feature_form.data and len(form.add_feature_form.feature.data) > 3 and len(form.add_feature_form.reasoning.data) > 15 and len(robot.features) <= 20:
            new_feature = {form.add_feature_form.feature.data.strip() : form.add_feature_form.reasoning.data}
            robot.features.update(new_feature)
            flag_modified(robot, "features")
            db.session.add(robot)
            db.session.merge(robot)
            db.session.flush()
            db.session.commit()
            return redirect(url_for('robot', robot=robot_id))
    form = BayesianRobotForms()
    if request.method == "POST" and 'run_analysis_form-run_analysis' in request.form.to_dict():
        if len(robot.features) > 0:
            robot.accuracy = robot.calculate_accuracy()
            flag_modified(robot, "accuracy")
            db.session.merge(robot)
            robot.accuracy = BayesianRobot.calculate_accuracy(robot)
            robot.retired = True
            robot.time_retired = datetime.datetime.utcnow()
            child_robot = robot.clone()
            db.session.add(child_robot)
            db.session.flush()
            robot.child = child_robot.id
            db.session.add(robot)
            db.session.commit()
            return redirect(url_for('robot', robot = robot.id))
    return render_template('robot.html', title='Robot', r = robot, form = form, acc_dict=acc_dict)

@app.route("/shared_analysis_view", methods=['GET', 'POST'])
def shared_analysis_view():
    analysis_id = request.args.get('analysis', 0, type=int)
    tweet_info = {}
    all_words = []
    if analysis_id != 0:
        analysis = BayesianAnalysis.query.get(analysis_id)
        # if not analysis.shared:
        #     return(redirect(url_for('home')))
        if analysis.shared:
            tweet_info = {t : {"correct": 0, "incorrect" : 0, "%" : 0} for t in analysis.tweets}
        else:
            tweet_info = {t.tweet : {"correct" : 0, "incorrect" : 0, "%" : 0} for t in analysis.tags}
        # for tag in analysis.tags:
        non_empty_tags = [t for t in analysis.tags if t.tweet != None]
        for tag in non_empty_tags:
            user = User.query.get(tag.user)
            tweet = Tweet.query.get(tag.tweet)
            all_words.extend(tweet.words)
            tweet_info[tweet.id]["full_text"] = tweet.full_text
            tweet_info[tweet.id]["category"] = TweetTagCategory.query.get(tweet.category).name
            if tweet.category == tag.category:
                tweet_info[tweet.id]["correct"]  = tweet_info[tweet.id]["correct"]   + 1
            else:
                tweet_info[tweet.id]["incorrect"]  = tweet_info[tweet.id]["incorrect"]   + 1
        for tweet_id in list(tweet_info.keys()):
            # if they haven't been categorized by anyone, remove them
            if tweet_info[tweet_id]["correct"] == 0 and tweet_info[tweet_id]["incorrect"] == 0:
                del tweet_info[ tweet_id ]
            else:
                tweet_info[tweet_id].update({"%": (tweet_info[tweet_id]["correct"] / (tweet_info[tweet_id]["incorrect"] + tweet_info[tweet_id]["correct"])) * 100})
    tweet_info = sorted([t for t in tweet_info.items()], key=lambda x:x[1]["%"], reverse=True)
    data={}
    percent_values = [d[1]["%"] for d in tweet_info]
    percent_counts = [{'label' : str(percent), 'estimate' : percent_values.count(percent)} for percent in set(percent_values)]
    for d in percent_counts:
        color = float(d['label']) / 100 * 120
        color = int(color)
        d.update({'color' : f"hsl({color}, 50%, 70%)", 'bg_color' : f"hsl({color}, 50%, 70%)"})
    chart_data = {'title' : 'Antal korrekte', 'data_points' : percent_counts}
    data['chart_data'] = chart_data
    # words = [word for x in tweet_info for word in x[1]["words"]]
    pred_by_word, data['predictions'] = analysis.get_predictions_and_words(all_words)
    # word_info = {word : {'predictions' : pred_by_word[word], 'counts' : words.count(word)} for word in set(words)}
    word_info = []
    for word in set(all_words):
        word_dict = {'word' : word, 'counts' : all_words.count(word)}
        for k,v in pred_by_word[word].items():
            word_dict[k] = v
        word_info.append(word_dict)
    tweet_info = [t[1] for t in tweet_info]
    # we don't need to sort this since we put it in a datatable anyway
    # print(word_info)
    # sorted_word_info = sorted([w for w in word_info], key=lambda x: x['counts'], reverse=True)
    return render_template('shared_analysis_view.html', title='Oversigt over analyse', tweets = tweet_info, word_info = word_info, analysis=analysis, **data)



@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/word")
def word():
    return render_template('word.html', title='Word examples')

@app.route("/analysis", methods=['GET', 'POST'])
def analysis():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    analysis_id = request.args.get('analysis', 1, type=int)
    analysis = BayesianAnalysis.query.get(analysis_id)
    analysis_method = analysis.method
    if analysis_method == 'Logistic Regression':
        return redirect(url_for('log_analysis'))
    project = Project.query.get(analysis.project)
    if 'tag' in request.form.to_dict():
        # category = TweetTagCategory.query.get(int(form.choices.data))
        tag_info = ast.literal_eval(request.form['tag'])
        tweet_id = tag_info[0]
        category_id = tag_info[1]
        the_tweet = Tweet.query.get(tweet_id)
        category = TweetTagCategory.query.get(category_id)
        the_tweet = Tweet.query.get(tweet_id)
        analysis.data = analysis.updated_data(the_tweet, category)
        ## all this  stuff is necessary  because the database backend doesnt resgister
        ## changes on JSON
        flag_modified(analysis, "data")
        db.session.add(analysis)
        db.session.merge(analysis)
        db.session.flush()
        db.session.commit()
        tag = TweetTag (category = category.id, analysis = analysis.id, tweet=the_tweet.id, user = current_user.id)
        db.session.add(tag)
        db.session.commit()
        # redirect(url_for('home'))
        return redirect(url_for('analysis', analysis=analysis_id))
    if len(analysis.robots) < 1: #TODO: move the creation of a robot to the creation of an analysis.
        robot = BayesianRobot(name =current_user.username + "s robot", analysis=analysis.id)
        db.session.add(robot)
        db.session.flush()
        db.session.commit()
        return redirect(url_for('analysis', analysis=analysis_id))
    ## check if user has access to this.
    ## either it is a shared project. In that case the user needs to be a member of 
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
    categories = TweetTagCategory.query.filter(TweetTagCategory.id.in_([p.id for p in project.categories])).all() # TODO: pretty sure we can just get project.categories
    tweets = project.tweets
    the_tweet = None
    if analysis.shared:
        completed_tweets = [t.tweet for t in analysis.tags if t.user == current_user.id]
        uncompleted_tweets = [t for t in analysis.tweets if t not in completed_tweets]
        if(len(uncompleted_tweets) > 0):
            the_tweet_id = uncompleted_tweets[0]
            the_tweet = Tweet.query.get(the_tweet_id)
        else:
            flash('Du er kommet igennem alle tweetsene. Vent på resten af klassen nu :)', 'success')
            the_tweet = Tweet(full_text = "", words = [])
    else:
        the_tweet = sample(tweets, 1)[0]
    form = TaggingForm()
    form.choices.choices  = [( str(c.id), c.name ) for c in categories]
    number_of_tagged = len(analysis.tags)
    data = {}
    data['number_of_tagged']  = number_of_tagged
    data['words'], data['predictions'] = analysis.get_predictions_and_words(set(the_tweet.words))
    data['word_tuples'] = nlp4all.utils.create_css_info(data['words'], the_tweet.full_text, categories)
    data['chart_data'] = nlp4all.utils.create_bar_chart_data(data['predictions'], "Computeren gætter på...")
    # filter robots that are retired, and sort them alphabetically
    # data['robots'] = sorted(robots, key= lambda r: r.name)
    data['analysis_data'] = analysis.data
    data['user'] = current_user
    data['user_role'] = current_user.roles
    data['tag_options'] = project.categories

    if form.validate_on_submit() and form.data:
        category = TweetTagCategory.query.get(int(form.choices.data))
        analysis.data = analysis.updated_data(the_tweet, category)
        ## all this  stuff is necessary  because the database backend doesnt resgister
        ## changes on JSON
        flag_modified(analysis, "data")
        db.session.add(analysis)
        db.session.merge(analysis)
        db.session.flush()
        db.session.commit()
        tag = TweetTag (category = category.id, analysis = analysis.id, tweet=the_tweet.id, user = current_user.id)
        db.session.add(tag)
        db.session.commit()
        # redirect(url_for('home'))
        return redirect(url_for('analysis', analysis=analysis_id))
    return render_template('analysis.html', analysis=analysis, tweet = the_tweet, form = form, **data)

@app.route("/log_analysis")
def log_analysis():
    # get current project
    project = Project.query.get(1)

    cats =project.categories
    cat_list =[]
    for i in range(len(cats)):
        cat_list.append(cats[i].name)
    analysis=LogRegAnalysis()
    tweet_data = analysis.get_tweets(cat_list)
    #analysis_id = request.args.get('analysis', 1, type=int)
    #analysis = BayesianAnalysis.query.get(analysis_id)
    ## change to get tweets from the project instead
    #tweets = project.query.get(tweets).all()
    results, logreg_matrix, logreg_class, logreg_accuracy, total = analysis.logreg_alltweets(tweet_data)
    db.session.add(analysis)
    db.session.merge(analysis)
    db.session.flush()
    db.session.commit()
    return render_template('log_analysis.html', title='Logistic Analysis', analysis=analysis, total=total, lg_matrix=logreg_matrix, lg_class = logreg_class, lg_acc=logreg_accuracy, results=results)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    form.organizations.choices = [(str(o.id), o.name) for o in Organization.query.all()]
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        org = Organization.query.get(int(form.organizations.data))
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, organizations=[org])
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/bar_chart")
def bar_chart():
    values = [0, 1, 2, 3, 4, 5]
    labels = ['0', '1', '2', '3', '4', '5']
    return render_template('bar_chart.html', title="test chart", values=values, labels=labels)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

@app.route("/manage_categories", methods=['GET', 'POST'])
@login_required
def manage_categories():
    form = AddTweetCategoryForm()
    categories = [cat.name for cat in TweetTagCategory.query.all()]
    if form.validate_on_submit():
        nlp4all.utils.add_tweets_from_account(form.twitter_handle.data)
        flash('Added tweets from the twitter handle', 'success')
        return redirect(url_for('manage_categories'))
    return render_template('manage_categories.html', form=form, categories=categories)

@app.route("/add_org", methods=['GET', 'POST'])
@login_required
def add_org():
    form = AddOrgForm()
    orgs = Organization.query.all()
    if form.validate_on_submit():
        org = Organization(name=form.name.data)
        db.session.add(org)
        db.session.commit()
        flash('Your organization has been created!', 'success')
        return redirect(url_for('add_org'))
    return render_template('add_org.html', form=form, orgs=orgs)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


# @app.route("/user/<string:username>")
# def user_posts(username):
#     page = request.args.get('page', 1, type=int)
#     user = User.query.filter_by(username=username).first_or_404()
#     posts = Post.query.filter_by(author=user)\
#         .order_by(Post.date_posted.desc())\
#         .paginate(page=page, per_page=5)
#     return render_template('user_posts.html', posts=posts, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
