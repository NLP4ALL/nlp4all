"""Bayesian Analysis Model"""  # pylint: disable=invalid-name

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from ..database import Base, MutableJSON


class BayesianAnalysis(Base):
    """BayesianAnalysis model."""

    __tablename__ = "bayesian_analysis"
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey("user.id"))
    name = Column(String(50))
    tags = relationship("DataTag")  # this also tells us which tweets
    data = Column(MutableJSON)
    project_id = Column(Integer, ForeignKey("project.id"))
    project = relationship("Project")
    robots = relationship("BayesianRobot")
    shared = Column(Boolean, default=False)
    shared_model = Column(Boolean, default=False)
    tweets = Column(MutableJSON, default=[])
    annotate = Column(Boolean, default=False)
    annotations = relationship("TweetAnnotation")
    annotation_tags = Column(MutableJSON)
    annotate = Column(Integer, default=1)  # type: ignore

    def get_project(self):
        """Get project."""
        return self.project

    # pylint: disable=unsupported-assignment-operation, unsubscriptable-object
    def updated_data(self, tweet, category):
        """Update data."""
        self.data["counts"] = self.data["counts"] + 1  # type: ignore
        if category.name not in self.data.keys():  # type: ignore # pylint: disable=no-member
            self.data[category.name] = {"counts": 0, "words": {}}  # type: ignore
        self.data[category.name]["counts"] = (self.data[category.name].get("counts", 0)) + 1  # type: ignore
        for word in set(tweet.words):  # type: ignore
            val = self.data[category.name]["words"].get(word, 0)
            self.data[category.name]["words"][word] = val + 1  # type: ignore
        return self.data

    # pylint: enable=unsupported-assignment-operation, unsubscriptable-object

    # pylint: disable=unsupported-assignment-operation, unsubscriptable-object
    def updated_a_tags(self, atag, tweet):
        """Update annotation tags."""
        if atag not in self.annotation_tags.keys():  # type: ignore # pylint: disable=no-member
            self.annotation_tags[atag] = {"counts": 0, "category": tweet.handle, "tweets": []}  # type: ignore
        self.annotation_tags[atag]["counts"] = self.annotation_tags[atag]["counts"] + 1  # type: ignore
        if tweet.id not in self.annotation_tags[atag]["tweets"]:
            self.annotation_tags[atag]["tweets"].append(tweet.id)
        return self.annotation_tags

    # pylint: enable=unsupported-assignment-operation, unsubscriptable-object

    # pylint: disable=unsupported-assignment-operation, unsubscriptable-object
    def get_predictions_and_words(self, words):
        """Get predictions and words."""
        # take each word  and  calculate a probabilty for each category
        categories = self.project.categories
        # type: ignore # pylint: disable=no-member
        category_names = [c.name for c in categories if c.name in self.data.keys()]
        preds = {}
        predictions = {}
        if self.data["counts"] == 0:  # type: ignore
            predictions = {c: {w: 0} for w in words for c in category_names}
            # predictions = {word : {category : 0 for category in category_names} for word in words}
        else:
            for word in words:  # only categorize each word once
                preds[word] = {c: 0 for c in category_names}
                for cat in category_names:
                    predictions[cat] = predictions.get(cat, {})
                    prob_ba = self.data[cat]["words"].get(word, 0) / self.data[cat]["counts"]
                    prob_a = self.data[cat]["counts"] / self.data["counts"]  # type: ignore
                    prob_b = (
                        sum(  # pylint: disable=consider-using-generator
                            [self.data[c]["words"].get(word, 0) for c in category_names]
                        )  # pylint: disable=consider-using-generator
                        / self.data["counts"]  # type: ignore
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

    # pylint: enable=unsupported-assignment-operation, unsubscriptable-object
