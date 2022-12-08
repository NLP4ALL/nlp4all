"""Admin controller.""" # pylint: disable=invalid-name

from flask import flash, redirect, url_for

from nlp4all import db
from nlp4all.models import Organization, DataTagCategory
from nlp4all.forms.admin import AddOrgForm
from nlp4all.forms.analyses import AddTweetCategoryForm
from nlp4all.helpers.tweets import add_tweets_from_account

from .BaseController import BaseController


class AdminController(BaseController):
    """Admin Controller"""

    view_subdir = "admin"

    @classmethod
    def manage_categories(cls):
        """Manage categories page"""
        form = AddTweetCategoryForm()
        categories = [cat.name for cat in DataTagCategory.query.all()]
        if form.validate_on_submit():
            add_tweets_from_account(form.twitter_handle.data)
            flash("Added tweets from the twitter handle", "success")
            return redirect(url_for("admin_controller.manage_categories"))
        return cls.render_template("manage_categories.html", form=form, categories=categories)

    @classmethod
    def add_org(cls):
        """Add organization page"""
        form = AddOrgForm()
        orgs = Organization.query.all()
        if form.validate_on_submit():
            org = Organization(name=form.name.data)
            db.add(org)
            db.session.commit()
            flash("Your organization has been created!", "success")
            return redirect(url_for("admin_controller.add_org"))
        return cls.render_template("add_org.html", form=form, orgs=orgs)
