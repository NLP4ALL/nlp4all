"""User / Login related controller."""  # pylint: disable=invalid-name

import os
import secrets
import typing as t
from PIL import Image

from werkzeug.local import LocalProxy
from flask import flash, redirect, request, url_for, abort, current_app
from flask_login import current_user, login_user, logout_user, confirm_login
from flask_mail import Message
from nlp4all import db
from ..helpers.site import is_safe_url
from ..helpers.pyutil import classproperty


from ..models import OrganizationModel, UserModel

from ..forms.user import (
    LoginForm,
    UpdateAccountForm,
    RegistrationForm,
    RequestResetForm,
    ResetPasswordForm,
)

from .base import BaseController

if t.TYPE_CHECKING:
    from werkzeug.wrappers import Response
    from flask_bcrypt import Bcrypt
    current_user: LocalProxy[UserModel] = current_user


class UserController(BaseController):
    """User Controller"""

    view_subdir = "user"

    @classproperty[Bcrypt]
    def bcrypt(cls) -> "Bcrypt":
        """Bcrypt"""
        if current_app is None:
            raise RuntimeError("No application found")
        if "bcrypt" not in current_app.extensions:
            raise RuntimeError("Bcrypt not initialized")
        return current_app.extensions["bcrypt"]

    @classmethod
    def account(cls):
        """Account page"""
        form = UpdateAccountForm()
        if form.validate_on_submit():
            if form.picture.data:
                picture_file = cls.save_picture(form.picture.data)
                current_user.image_file = picture_file
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash("Your account has been updated!", "success")
            return redirect(url_for("user_controller.account"))
        if request.method == "GET":
            form.username.data = current_user.username
            form.email.data = current_user.email
        image_file = request.host_url + "static/profile_pics/" + current_user.image_file
        return cls.render_template("account.html", title="Account",
                                   image_file=image_file, form=form)

    @classmethod
    def save_picture(cls, form_picture):
        """Save picture"""
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(cls.blueprint.root_path, "static/profile_pics", picture_fn)

        output_size = (125, 125)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)

        return picture_fn

    @classmethod
    def next_or_home(cls) -> 'Response':
        """Redirect to next or home"""
        next_page = request.args.get("next")
        if next_page:
            if not is_safe_url(next_page, request):
                abort(400)
            return redirect(next_page)
        return redirect(url_for("project_controller.home"))

    @classmethod
    def login(cls):
        """Login page"""
        if current_user.is_authenticated:
            return redirect(url_for("project_controller.home"))
        form = LoginForm()
        if form.validate_on_submit():
            user = UserModel.query.filter_by(email=form.email.data).first()
            if user and cls.bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return cls.next_or_home()
            flash("Login Unsuccessful. Please check email and password", "danger")
        return cls.render_template("login.html", title="Login", form=form)

    @classmethod
    def reauth(cls):
        form = LoginForm()
        if form.validate_on_submit():
            if current_user and check_password_hash(current_user.password, form.password.data):
                flash("Reauthenticated.", "info")
                confirm_login()
                return cls.next_or_home()
            flash("Login Unsuccessful. Please check email and password", "danger")
        return cls.render_template("reauth.html", title="Reauthenticate", form=form)

    @classmethod
    def logout(cls):
        """Logout page"""
        if current_user.is_authenticated:
            logout_user()
        return redirect(url_for("site_controller.home"))

    @classmethod
    def register(cls):
        """Register page"""
        if current_user.is_authenticated:
            return redirect(url_for("project_controller.home"))
        form = RegistrationForm()
        form.organizations.choices = [(str(o.id), o.name) for o in OrganizationModel.query.all()]
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data).decode("utf-8")
            org = OrganizationModel.query.get(int(form.organizations.data))
            user = UserModel(
                username=form.username.data,
                email=form.email.data,
                password=hashed_password,
                organizations=[org],
            )
            db.add(user)
            db.session.commit()
            flash("Your account has been created! You are now able to log in", "success")
            return redirect(url_for("login"))
        return cls.render_template("register.html", title="Register", form=form)

    @classmethod
    def reset_request(cls):
        """Reset password request page"""
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        form = RequestResetForm()
        if form.validate_on_submit():
            user = UserModel.query.filter_by(email=form.email.data).first()
            cls.send_reset_email(user)
            flash("An email has been sent with instructions to reset your password.", "info")
            return redirect(url_for("login"))
        return cls.render_template("reset_request.html", title="Reset Password", form=form)

    @classmethod
    def reset_token(cls, token):
        """Reset password token page"""
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        user = UserModel.verify_reset_token(token, cls.blueprint.secret_key)
        if user in ("Expired", "Invalid"):
            flash(f"That is an {user} token", "warning")
            return redirect(url_for("reset_request"))
        form = ResetPasswordForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data).decode("utf-8")
            user.password = hashed_password
            db.session.commit()
            flash("Your password has been updated! You are now able to log in", "success")
            return redirect(url_for("login"))
        return cls.render_template("reset_token.html", title="Reset Password", form=form)

    @classmethod
    def send_reset_email(cls, user):
        """Send reset email"""
        token = user.get_reset_token()
        msg = Message("Password Reset Request", sender="noreply@demo.com", recipients=[user.email])
        msg.body = f"""To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
"""
        # @TODO implement mail server
        # mail.send(msg)
