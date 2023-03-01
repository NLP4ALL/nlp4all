"""Admin controller."""  # pylint: disable=invalid-name

from flask import flash, redirect, url_for
from celery.result import AsyncResult
from nlp4all import db
from ..models import UserGroupModel, DataTagCategoryModel
from ..forms.admin import AddOrgForm
from ..forms.analyses import AddTweetCategoryForm
from ..helpers.tweets import add_tweets_from_account
from ..helpers.celery import add_test

from .base import BaseController


class AdminController(BaseController):
    """Admin Controller"""

    view_subdir = "admin"

    @classmethod
    def manage_categories(cls):
        """Manage categories page"""
        form = AddTweetCategoryForm()
        categories = [cat.name for cat in DataTagCategoryModel.query.all()]
        if form.validate_on_submit():
            add_tweets_from_account(form.twitter_handle.data)
            flash("Added tweets from the twitter handle", "success")
            return redirect(url_for("admin_controller.manage_categories"))
        return cls.render_template("manage_categories.html", form=form, categories=categories)

    @classmethod
    def add_org(cls):
        """Add organization page"""
        form = AddOrgForm()
        orgs = UserGroupModel.query.all()
        if form.validate_on_submit():
            org = UserGroupModel(name=form.name.data)
            db.add(org)
            db.session.commit()
            flash("Your group has been created!", "success")
            return redirect(url_for("admin_controller.add_org"))
        return cls.render_template("add_org.html", form=form, orgs=orgs)

    @classmethod
    def celery_test(cls, x: int, y: int):
        result = add_test.delay(x, y)
        return redirect(url_for("admin_controller.celery_result", task_id=result.id))

    @classmethod
    def celery_result(cls, task_id: str):
        result = AsyncResult(task_id)
        return cls.render_template("celery_result.html", result=result)
