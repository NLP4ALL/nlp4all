"""Admin controller."""

from flask import flash, redirect, render_template, url_for

from nlp4all.models.database import db_session
from nlp4all.models import Organization, TweetTagCategory
from nlp4all.forms.admin import AddTweetCategoryForm, AddOrgForm
from nlp4all.helpers.tweets import add_tweets_from_account


class AdminController:
    """Admin Controller"""

    @classmethod
    def manage_categories(cls):
      """Manage categories page"""
      form = AddTweetCategoryForm()
      categories = [cat.name for cat in TweetTagCategory.query.all()]
      if form.validate_on_submit():
          add_tweets_from_account(form.twitter_handle.data)
          flash("Added tweets from the twitter handle", "success")
          return redirect(url_for("manage_categories"))
      return render_template("manage_categories.html", form=form, categories=categories)

    @classmethod
    def add_org(cls):
      """Add organization page"""
      form = AddOrgForm()
      orgs = Organization.query.all()
      if form.validate_on_submit():
          org = Organization(name=form.name.data)
          db_session.add(org)
          db_session.commit()
          flash("Your organization has been created!", "success")
          return redirect(url_for("add_org"))
      return render_template("add_org.html", form=form, orgs=orgs)