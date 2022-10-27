"""
Updates the robot accuracy in the database.
"""
from sqlalchemy.orm.attributes import flag_modified

from nlp4all.models.database import db_session
from nlp4all.models import BayesianAnalysis, BayesianRobot

robots = [r for r in BayesianRobot.query.all() if r.retired]

for r in robots:
    username = BayesianAnalysis.query.get(r.analysis).name
    r.accuracy = BayesianRobot.calculate_accuracy(r)
    flag_modified(r, "accuracy")
    db_session.add(r)
    db_session.merge(r)
    db_session.flush()
    db_session.commit()
