# pylint: disable=too-many-lines
"""Routing for flask

This module contains the routing for the flask app.
"""
# @TODO: break out into smaller chunks
import os
import datetime
import ast
import secrets
import re

from random import sample, shuffle, randint
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

from sqlalchemy.orm.attributes import flag_modified


from nlp4all import app, db, bcrypt, mail
import nlp4all.utils

from nlp4all.forms import (
    IMCRegistrationForm,
    RegistrationForm,
    LoginForm,
    UpdateAccountForm,
    RequestResetForm,
    ResetPasswordForm,
    AddOrgForm,
    AddBayesianAnalysisForm,
    AddProjectForm,
    TaggingForm,
    AddTweetCategoryForm,
    BayesianRobotForms,
    CreateMatrixForm,
    ThresholdForm,
)
from nlp4all.models import (
    BayesianRobot,
    User,
    Organization,
    Project,
    BayesianAnalysis,
    TweetTagCategory,
    TweetTag,
    Tweet,
    ConfusionMatrix,
    TweetAnnotation,
)

from nlp4all.utils import get_user_projects


