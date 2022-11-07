"""Project controller""" # pylint: disable=invalid-name

from random import sample, shuffle
from flask import redirect, request, url_for
from flask_login import current_user

from nlp4all.models.database import db_session
from nlp4all.models import BayesianAnalysis, Organization, TweetTagCategory, Project, BayesianRobot

from nlp4all.forms.admin import AddProjectForm
from nlp4all.forms.analyses import AddBayesianAnalysisForm

from nlp4all.helpers.analyses import (
    add_project,
    get_user_projects,
)  # @TODO: this add_project CLEARLY belongs on the model, not in helpers

from .BaseController import BaseController

# from flask_mail import Message


class ProjectController(BaseController):
    """Project controller"""

    view_subdir = "project"

    @classmethod
    def home(cls):
        """Project list page"""
        my_projects = get_user_projects(current_user)
        return cls.render_template("projects.html", projects=my_projects)

    @classmethod
    def add_project(cls):
        """Add project page"""
        form = AddProjectForm()
        # find forst alle mulige organizations
        form.organization.choices = [(str(o.id), o.name) for o in Organization.query.all()]
        form.categories.choices = [(str(s.id), s.name) for s in TweetTagCategory.query.all()]
        if form.validate_on_submit():
            # orgs = [int(n) for n in form.organization.data]
            # orgs_objs = Organization.query.filter(Organization.id.in_(orgs)).all()
            org = Organization.query.get(int(form.organization.data))
            cats = [int(n) for n in form.categories.data]
            a_project = add_project(
                name=form.title.data, description=form.description.data, org=org.id, cat_ids=cats
            )
            project_id = a_project.id
            return redirect(url_for("project_controller.home", project=project_id))
        return cls.render_template("add_project.html", title="Add New Project", form=form)

    # @TODO: refactor this, i moved this function here
    # because it was in utils, which imported models which imported utils
    @classmethod
    def get_user_project_analyses(cls, a_user, a_project):  # pylint: disable=unused-argument
        """Get user project analyses"""
        analyses = BayesianAnalysis.query.filter_by(project=a_project.id)
        if current_user.admin:
            return analyses
        return [a for a in analyses if a.shared or a.shared_model or a.user == a_user.id]

    @classmethod
    def project(cls):  # pylint: disable=too-many-locals
        """Project page"""
        project_id = request.args.get("project", None, type=int)
        a_project = Project.query.get(project_id)
        form = AddBayesianAnalysisForm()
        analyses = (
            BayesianAnalysis.query.filter_by(user=current_user.id)
            .filter_by(project=project_id)
            .all()
        )
        analyses = cls.get_user_project_analyses(current_user, a_project)
        form.annotate.choices = [(1, "No Annotations"), (2, "Category names"), (3, "add own tags")]
        if form.validate_on_submit():
            userid = current_user.id
            name = form.name.data
            number_per_category = form.number.data
            analysis_tweets = []
            annotate = form.annotate.data
            if form.shared.data:
                tweets_by_cat = {
                    cat: [t.id for t in a_project.tweets if t.category == cat.id]
                    for cat in a_project.categories
                }
                for cat, tweets in tweets_by_cat.items():
                    analysis_tweets.extend(sample(tweets, number_per_category))
            # make sure all students see tweets in the same order. So shuffle them now, and then
            # put them in the database
            shuffle(analysis_tweets)
            bayes_analysis = BayesianAnalysis(
                user=userid,
                name=name,
                project=a_project.id,
                data={"counts": 0, "words": {}},
                shared=form.shared.data,
                tweets=analysis_tweets,
                annotation_tags={},
                annotate=annotate,
                shared_model=form.shared_model.data,
            )
            db_session.add(bayes_analysis)
            db_session.commit()
            # this is where robot creation would go. Make one for everyone in
            # the org if it is a shared model, but not if it is a "shared",
            # meaning everyone tags the same tweets
            # @TODO: pretty sure this is broken
            org = Organization.query.get(a_project.organization)
            for _ in org.users:
                bayes_robot = BayesianRobot(
                    name=current_user.first_name +
                    current_user.last_name +
                    "s robot", analysis=bayes_analysis.id
                )
                db_session.add(bayes_robot)
                db_session.flush()
                db_session.commit()
            # return(redirect(url_for('project', project=project_id)))
        return cls.render_template(
            "project.html",
            title="About",
            project=a_project,
            analyses=analyses,
            form=form,
            user=current_user,
        )
