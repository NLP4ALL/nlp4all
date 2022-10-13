"""
Updates the robot accuracy in the database.
"""
from sqlalchemy.orm.attributes import flag_modified
from nlp4all import db
from nlp4all.models import BayesianAnalysis, BayesianRobot

robots = [r for r in BayesianRobot.query.all() if r.retired]

for r in robots:
    username = BayesianAnalysis.query.get(r.analysis).name
    r.accuracy = BayesianRobot.calculate_accuracy(r)
    flag_modified(r, "accuracy")
    db.session.add(r)
    db.session.merge(r)
    db.session.flush()
    db.session.commit()
