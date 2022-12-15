"""Confusion Matrix model"""  # pylint: disable=invalid-name

from __future__ import annotations

import operator
from typing import TYPE_CHECKING
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base, data_matrices_table, matrix_categories_table, MutableJSONB
from .data_tag_category import DataTagCategory

if TYPE_CHECKING:
    from .data import Data

from ..helpers.datasets import create_n_split_tnt_sets


class ConfusionMatrix(Base):  # pylint: disable=too-many-instance-attributes
    """Confusion matrix."""

    __tablename__ = "confusion_matrix"
    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[int] = mapped_column(ForeignKey("user.id"))
    categories: Mapped[list[DataTagCategory]] = relationship(secondary=matrix_categories_table)
    source_data: Mapped[list[Data]] = relationship(secondary=data_matrices_table)
    matrix_data: Mapped[dict] = mapped_column(MutableJSONB)  # here to save the TP/TN/FP/FN
    train_data: Mapped[dict] = mapped_column(MutableJSONB)  # word counts from the training set
    tf_idf: Mapped[dict] = mapped_column(MutableJSONB)
    training_and_test_sets: Mapped[dict] = mapped_column(MutableJSONB)
    threshold: Mapped[float] = mapped_column()
    ratio: Mapped[float] = mapped_column()
    data: Mapped[dict] = mapped_column(MutableJSONB)  # accuracy etc resuts from the matrix
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("confusion_matrix.id"),
        default=None)  # for cloning purposes
    child: Mapped[Optional[int]] = mapped_column(ForeignKey("confusion_matrix.id"), default=None)

    def clone(self):
        """Clone confusion matrix."""
        new_matrix = ConfusionMatrix()
        new_matrix.parent_id = self.id
        new_matrix.categories = self.categories
        new_matrix.data = self.data
        new_matrix.tf_idf = self.tf_idf
        new_matrix.training_and_test_sets = self.training_and_test_sets
        new_matrix.ratio = self.ratio
        new_matrix.train_data = {"counts": 0, "words": {}}
        return new_matrix

    def updated_data(self, tweet, category):
        """Update data."""
        # update the train_data when you change tnt set, this is mostly copied
        # from a Bayesian analysis function above
        self.train_data["counts"] = self.train_data["counts"] + 1  # type: ignore
        if category.name not in self.train_data:
            self.train_data[category.name] = {"counts": 0, "words": {}}
        self.train_data[category.name]["counts"] = (
            self.train_data[category.name].get("counts", 0)
        ) + 1
        for word in set(tweet.words):
            val = self.train_data[category.name]["words"].get(word, 0)
            self.train_data[category.name]["words"][word] = val + 1
        return self.train_data

    def update_tnt_set(self):
        """Update the training and test sets."""
        tweet_id_and_cat = {t.id: t.category for t in self.data}
        self.training_and_test_sets = create_n_split_tnt_sets(30, self.ratio, tweet_id_and_cat)  # type: ignore
        return self.training_and_test_sets

    def get_predictions_and_words(self, words):
        """Get predictions and words."""
        # works the same way as for bayesian analysis
        categories = self.categories
        category_names = [c.name for c in categories]
        preds = {}
        predictions = {}
        if self.train_data["counts"] == 0:  # type: ignore
            predictions = {c: {w: 0} for w in words for c in category_names}
            # predictions = {word : {category : 0 for category in category_names} for word in words}
        else:
            for word in words:  # only categorize each word once
                preds[word] = {c: 0 for c in category_names}
                for cat in category_names:
                    predictions[cat] = predictions.get(cat, {})
                    prob_ba = (
                        self.train_data[cat]["words"].get(word, 0) / self.train_data[cat]["counts"]
                    )
                    prob_a = (
                        self.train_data[cat]["counts"] /
                        self.train_data["counts"])  # type: ignore
                    prob_b = (
                        sum(  # pylint: disable=consider-using-generator
                            [self.train_data[c]["words"].get(word, 0) for c in category_names]
                        )
                        / self.train_data["counts"]  # type: ignore
                    )
                    if prob_b == 0:
                        preds[word][cat] = 0
                        predictions[cat][word] = 0
                    else:
                        preds[word][cat] = round(prob_ba * prob_a / prob_b, 2)
                        predictions[cat][word] = round(prob_ba * prob_a / prob_b, 2)

        return (
            preds,
            {k: round(sum(v.values()) / len(set(words)), 2) for k, v in predictions.items()},
        )

    def train_model(self, train_tweet_ids):
        """Train model."""
        # reinitialize the training data
        self.train_data = {"counts": 0, "words": {}}
        train_data = self.train_data
        # trains the model with the training data tweets
        for tweet_id in train_tweet_ids:
            tweet = Data.query.get(tweet_id)
            category_id = tweet.category
            category = DataTagCategory.query.get(category_id)
            train_data = self.updated_data(tweet, category)
        return train_data

    def make_matrix_data(self, test_tweets, cat_names):  # pylint: disable=unused-argument
        """Make matrix data."""
        # classifies the tweets according to the calculated prediction
        # probabilities
        matrix_data = {
            t.id: {"predictions": 0, "pred_cat": "", "probability": 0, "relative probability": 0}
            for t in test_tweets
        }
        words = {t.id: "" for t in test_tweets}

        for a_tweet in test_tweets:
            (
                words[a_tweet.id],  # type: ignore
                matrix_data[a_tweet.id]["predictions"],
            ) = self.get_predictions_and_words(set(a_tweet.words))
            # if no data
            if bool(matrix_data[a_tweet.id]["predictions"]) is False:
                matrix_data[a_tweet.id]["pred_cat"] = "none"
            # if all prob == 0
            elif sum(matrix_data.get(a_tweet.id)["predictions"].values()) == 0:  # type: ignore
                matrix_data[a_tweet.id]["pred_cat"] = "none"
            # else select the biggest prob
            else:
                matrix_data[a_tweet.id]["pred_cat"] = max(
                    matrix_data[a_tweet.id]["predictions"].items(), key=operator.itemgetter(1)
                )[0]
                # bayesian p
                matrix_data[a_tweet.id]["probability"] = max(
                    matrix_data[a_tweet.id]["predictions"].items(), key=operator.itemgetter(1)
                )[1]
                # relative p compared to other cats
                max_prob = max(
                    matrix_data[a_tweet.id]["predictions"].items(), key=operator.itemgetter(1)
                )[1]
                matrix_data[a_tweet.id]["relative probability"] = round(
                    max_prob / sum(matrix_data[a_tweet.id]["predictions"].values()), 3
                )
            # add the real category
            matrix_data[a_tweet.id]["real_cat"] = a_tweet.handle

        matrix_data = sorted(
            list(matrix_data.items()), key=lambda x: x[1]["probability"], reverse=True
        )  # add matrix classes/quadrants
        for tweet in matrix_data:  # this is just for indexing tweets
            for cat in self.categories:
                # if correct prediction
                if (
                    tweet[1]["pred_cat"] == tweet[1]["real_cat"]
                    and tweet[1]["pred_cat"] == cat.name
                ):  # pylint: disable=line-too-long
                    tweet[1]["class"] = "Pred_" + str(cat.name) + "_Real_" + tweet[1]["real_cat"]
                # if uncorrect prediction
                elif (
                    tweet[1]["pred_cat"] != tweet[1]["real_cat"]
                    and tweet[1]["pred_cat"] == cat.name
                ):  # pylint: disable=line-too-long
                    # predicted 'no', although was 'yes'
                    tweet[1]["class"] = "Pred_" + str(cat.name) + "_Real_" + tweet[1]["real_cat"]
                # if no prediction
                elif tweet[1]["pred_cat"] == "none":
                    tweet[1]["class"] = "undefined"
        return matrix_data

    def make_table_data(self, cat_names):
        """Make table data."""
        # this function is a manual way to create confusion matrix data rows
        # type: ignore # pylint: disable=unsubscriptable-object, no-member
        current_data_class = [self.matrix_data[i].get("real_cat") for i in self.matrix_data.keys()]
        # type: ignore # pylint: disable=unsubscriptable-object, no-member
        predicted_class = [self.matrix_data[i].get("pred_cat") for i in self.matrix_data.keys()]
        number_list = list(range(len(cat_names)))
        # change cat names to numbers 1,2,...
        for i in number_list:
            for j in range(len(current_data_class)):  # pylint: disable=consider-using-enumerate
                if current_data_class[j] == cat_names[i]:
                    current_data_class[j] = i + 1
        for i in number_list:
            for j in range(len(predicted_class)):  # pylint: disable=consider-using-enumerate
                if predicted_class[j] == cat_names[i]:
                    predicted_class[j] = i + 1
        # find number of classes
        classes = int(max(current_data_class) - min(current_data_class)) + 1
        counts = [
            [
                sum(  # pylint: disable=consider-using-generator
                    [
                        (current_data_class[i] == true_class) and (predicted_class[i] == pred_class)
                        for i in range(len(current_data_class))
                    ]
                )
                for pred_class in range(1, classes + 1)
            ]
            for true_class in range(1, classes + 1)
        ]

        return counts
