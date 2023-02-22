"""Bayesian Robot Model"""  # pylint: disable=invalid-name

import collections
import functools
import operator
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from ..database import Base, MutableJSON


class BayesianRobotModel(Base):
    """BayesianRobot model."""

    __tablename__ = "bayesian_robot"

    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey("user.id"))
    name = Column(String(25))
    parent = Column(Integer, ForeignKey("bayesian_robot.id"), default=None)
    child = Column(Integer, ForeignKey("bayesian_robot.id"), default=None)
    analysis_id = Column(Integer, ForeignKey("bayesian_analysis.id"))
    analysis = relationship("BayesianAnalysisModel")
    features = Column(MutableJSON, default={})
    accuracy = Column(MutableJSON, default={})
    retired = Column(Boolean, default=False)
    time_retired = Column(DateTime)

    def clone(self):
        """Clones a BayesianRobot object.

        Returns:
            BayesianRobot: A new BayesianRobot object.
        """
        new_robot = BayesianRobotModel()
        new_robot.name = self.name
        new_robot.analysis = self.analysis
        new_robot.features = self.features
        new_robot.parent = self.id
        new_robot.user = self.user
        return new_robot

    def get_analysis(self):
        """Gets the BayesianAnalysis object associated with the robot.

        Returns:
            BayesianAnalysis: The BayesianAnalysis object associated with the robot.
        """
        return self.analysis

    def word_in_features(self, word):
        """Checks if a word is in the features of the robot.

        Args:
            word (str): The word to check.

        Returns:
            bool: True if the word is in the features of the robot, False otherwise.
        """
        for feature in self.features.keys():  # type: ignore
            feature_string = feature.lower()
            if feature_string.startswith("*") and feature_string.endswith("*"):
                if feature_string[1:-1] in word:
                    return True
            elif feature_string.startswith("*"):
                if word.endswith(feature_string[1:]):
                    return True
            elif feature_string.endswith("*"):
                if word.startswith(feature_string[:1]):
                    return True
            else:
                if word == feature_string:
                    return True
        return False

    def calculate_accuracy(
        self,
    ):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Calculates the accuracy of the robot.

        Returns:
            dict: A dictionary containing the accuracy of the robot.
        """
        # @TODO: This function is too long and needs to be refactored.
        analysis_obj = self.analysis
        proj_obj = analysis_obj.project
        tf_idf = proj_obj.tf_idf
        feature_words = {}
        for feature in self.features:
            feature_words[feature] = [
                word for word in tf_idf.get("words") if BayesianRobotModel.matches(word, feature)
            ]
        # relevant_words = [w for words in feature_words.values() for w in words]
        # first calculate the predictions, based on the training sets.
        predictions_by_feature = {}
        # initialize test_set_tweets so we dont need to calculate it twice
        test_set_tweets = set()
        cats = [c.id for c in proj_obj.categories]

        # make one for individual words too so we can more easily access them
        # later, and make a  list of category names for viewing
        word_category_predictions = {}
        cat_names = {cat.id: cat.name for cat in analysis_obj.project.categories}

        for (
            feature
        ) in (
            feature_words
        ):  # pylint: disable=consider-iterating-dictionary,consider-using-dict-items
            predictions_by_feature[feature] = {}
            for word in feature_words[feature]:
                for dataset in proj_obj.training_and_test_sets[:1]:
                    train_set = dataset[0]
                    tweets = tf_idf.get("words").get(word)
                    train_set_tweets = []
                    for tweet in tweets:
                        if str(tweet[0]) in train_set.keys():
                            train_set_tweets.append(tweet)
                        else:
                            test_set_tweets.add(tweet[0])
                    categories_in_dataset = [
                        dataset[0].get(str(tweet[0])) for tweet in train_set_tweets
                    ]
                    cat_counts = {c: categories_in_dataset.count(c) for c in cats}
                    total_cats = sum(cat_counts.values())
                    predictions = 0
                    # if there are no words in the training set to learn from,
                    # we simply ignore the word and do not append anything here
                    if total_cats > 0:
                        predictions = {c: cat_counts[c] / sum(cat_counts.values()) for c in cats}
                        category_dict = {
                            "category_prediction": cat_names[
                                max(predictions.items(), key=operator.itemgetter(1))[0]
                            ]
                        }
                        word_category_predictions[word] = category_dict
                        predictions_by_feature[feature][word] = predictions
        # now for each word, figure out which tweets contain them, and build -
        # for each tweet - a classification, that we can then compare to the
        # real value

        test_set = proj_obj.training_and_test_sets[0][1]
        tweet_predictions = {}

        for word_prediction in predictions_by_feature.values():
            for word, predictions in word_prediction.items():
                word_tweets = tf_idf.get("words").get(word)
                test_set_tweets = [
                    tweet for tweet in word_tweets if str(tweet[0]) in test_set.keys()
                ]
                for tweet in test_set_tweets:
                    preds = tweet_predictions.get(
                        tweet[0], {"predictions": [], "words": [], "category": tweet[1]}
                    )
                    preds["predictions"].append(predictions)
                    preds["words"].append(word)
                    tweet_predictions[tweet[0]] = preds
        # now finally evaluate how well we did, in general and by word
        word_accuracy = {}
        for (
            tweet_key
        ) in (
            tweet_predictions
        ):  # pylint: disable=consider-iterating-dictionary,consider-using-dict-items
            prediction_dict = tweet_predictions[tweet_key].copy()

            summed_prediction = dict(
                functools.reduce(
                    operator.add, map(collections.Counter, prediction_dict["predictions"])
                )
            )
            # the old code that makes summed_prediction also includes the newly
            # added "category_prediction". Since we don't want to
            # sum that, we remove it first
            # it can happen that we evaluate a word that we have no information
            # on. In that
            cat_prediction = max(summed_prediction.items(), key=operator.itemgetter(1))[0]
            tweet_predictions[tweet_key]["correct"] = test_set[str(tweet_key)] == cat_prediction
            # save a per-word accuracy
            for word in prediction_dict["words"]:
                acc = word_accuracy.get(word, [])
                acc.append(tweet_predictions[tweet_key]["correct"])
                word_accuracy[word] = acc
        # and then build a nice dict full of info
        feature_info = {}
        for (
            feature
        ) in (
            feature_words
        ):  # pylint: disable=consider-iterating-dictionary,consider-using-dict-items
            feature_info[feature] = {}
            feature_info[feature]["words"] = {}
            for word in feature_words[feature]:
                word_dict = feature_info[feature].get(word, {})
                if (
                    word in word_accuracy
                ):  # the word is only in the word_accuracy dict if it was in the test set
                    word_dict["tweets_targeted"] = len(word_accuracy[word])
                    word_dict["accuracy"] = round(
                        len([x for x in word_accuracy[word] if x]) / len(word_accuracy[word]), 2
                    )
                    feature_info[feature]["words"][word] = word_dict
                # else:
                #     # if it's not in the test set, we just take it out.
                #     word_dict['tweets_targeted'] = 0
                #     word_dict['accuracy'] = 0
                # feature_info[feature]['words'][word] = word_dict

            accuracy_values = [d["accuracy"] for d in feature_info[feature]["words"].values()]
            targeted_values = [
                d["tweets_targeted"] for d in feature_info[feature]["words"].values()
            ]
            if len(accuracy_values) > 0:
                feature_info[feature]["accuracy"] = sum(accuracy_values) / len(accuracy_values)
                feature_info[feature]["tweets_targeted"] = sum(targeted_values)
            else:
                feature_info[feature]["accuracy"] = 0
                feature_info[feature]["tweets_targeted"] = 0
        tweets_targeted = 0
        table_data = []
        for (
            feature
        ) in (
            feature_info
        ):  # pylint: disable=consider-iterating-dictionary,consider-using-dict-items
            tweets_targeted = tweets_targeted + feature_info[feature]["tweets_targeted"]
            feat_dict = {}
            feat_dict["word"] = feature
            feat_dict["category_prediction"] = "N/A"
            feat_dict["accuracy"] = feature_info[feature]["accuracy"]
            feat_dict["tweets_targeted"] = feature_info[feature]["tweets_targeted"]
            score = feat_dict["accuracy"] * feat_dict["tweets_targeted"] - (
                (1 - feat_dict["accuracy"]) * feat_dict["tweets_targeted"]
            )
            print(score)
            feat_dict["score"] = round(score, 2)
            # calculate the most often predicted category. This isn't trivial -
            # should it be by total tweets in test set, or just the most common
            # category across its words? Well, it's obvious. Boo. It needs to be
            # weighted by how many tweets there are.
            # NO  NO NO! I thought about that wrong. We just want the average
            # of each of the category prediction for each word.
            print(feat_dict)
            table_data.append(feat_dict)
            for word in feature_info[feature]["words"]:
                feat_dict = {}
                feat_dict["word"] = word
                feat_dict["category_prediction"] = word_category_predictions[word][
                    "category_prediction"
                ]
                feat_dict["accuracy"] = feature_info[feature]["words"][word]["accuracy"]
                feat_dict["tweets_targeted"] = feature_info[feature]["words"][word][
                    "tweets_targeted"
                ]  # pylint: disable=line-too-long
                score = feat_dict["accuracy"] * feat_dict["tweets_targeted"] - (
                    (1 - feat_dict["accuracy"]) * feat_dict["tweets_targeted"]
                )
                print(score)
                feat_dict["score"] = round(score, 2)
                table_data.append(feat_dict)
        if len(tweet_predictions) == 0:
            accuracy = 0
        else:
            accuracy = len([d for d in tweet_predictions.values() if d["correct"]]) / len(
                tweet_predictions
            )
        accuracy_info = {"accuracy": round(accuracy, 2), "tweets_targeted": tweets_targeted}
        accuracy_info["features"] = feature_info
        accuracy_info["table_data"] = table_data
        return accuracy_info

    @staticmethod
    def matches(aword, afeature):
        """Check if a word matches a feature."""
        feature_string = afeature.lower()
        if feature_string.startswith("*") and feature_string.endswith("*"):
            if feature_string[1:-1] in aword:
                return True
        elif feature_string.startswith("*"):
            if aword.endswith(feature_string[1:]):
                return True
        elif feature_string.endswith("*"):
            # if aword.startswith(feature_string[:1]): ## this was a bug. Leave
            # it in if people want to see it.
            if aword.startswith(feature_string[:-1]):
                return True
        else:
            if aword == feature_string:
                return True
        return False

    def feature_words(self, a_feature, tf_idf):
        """Return a list of words that match a feature."""
        return_list = []
        words = tf_idf.get("words")
        feature_string = a_feature.lower()
        for word in words:
            if feature_string.startswith("*") and feature_string.endswith("*"):
                if feature_string[1:-1] in word:
                    return_list.append(word)
            elif feature_string.startswith("*"):
                if word.endswith(feature_string[1:]):
                    return_list.append(word)
            elif feature_string.endswith("*"):
                if word.startswith(feature_string[:1]):
                    return_list.append(word)
            else:
                if word == feature_string:
                    return_list.append(word)
        return return_list
