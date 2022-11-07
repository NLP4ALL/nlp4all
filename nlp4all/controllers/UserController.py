"""User / Login related controller.""" # pylint: disable=invalid-name

import os
from random import randint
import secrets
from PIL import Image


from flask import flash, redirect, request, url_for, abort
from flask_login import current_user, login_user, logout_user
from flask_mail import Message
from flask_bcrypt import check_password_hash, generate_password_hash
from nlp4all.helpers.site import is_safe_url

from nlp4all.models.database import db_session
from nlp4all.models import BayesianAnalysis, Organization, User

from nlp4all.forms.user import (
    LoginForm,
    UpdateAccountForm,
    RegistrationForm,
    RequestResetForm,
    ResetPasswordForm,
    IMCRegistrationForm,
)

from .BaseController import BaseController

class UserController(BaseController):
    """User Controller"""

    view_subdir = "user"

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
            db_session.commit()
            flash("Your account has been updated!", "success")
            return redirect(url_for("user_controller.account"))
        if request.method == "GET":
            form.username.data = current_user.username
            form.email.data = current_user.email
        image_file = url_for("static", filename="profile_pics/" + current_user.image_file)
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
    def login(cls):
        """Login page"""
        if current_user.is_authenticated:
            return redirect(url_for("project_controller.home"))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get("next")
                if next_page:
                    if not is_safe_url(next_page, request):
                        return abort(400)
                    return redirect(next_page)
                return redirect(url_for("project_controller.home"))
            flash("Login Unsuccessful. Please check email and password", "danger")
        return cls.render_template("login.html", title="Login", form=form)

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
        form.organizations.choices = [(str(o.id), o.name) for o in Organization.query.all()]
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data).decode("utf-8")
            org = Organization.query.get(int(form.organizations.data))
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=hashed_password,
                organizations=[org],
            )
            db_session.add(user)
            db_session.commit()
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
            user = User.query.filter_by(email=form.email.data).first()
            cls.send_reset_email(user)
            flash("An email has been sent with instructions to reset your password.", "info")
            return redirect(url_for("login"))
        return cls.render_template("reset_request.html", title="Reset Password", form=form)

    @classmethod
    def reset_token(cls, token):
        """Reset password token page"""
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        user = User.verify_reset_token(token, cls.blueprint.secret_key)
        if user in ("Expired", "Invalid"):
            flash(f"That is an {user} token", "warning")
            return redirect(url_for("reset_request"))
        form = ResetPasswordForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data).decode("utf-8")
            user.password = hashed_password
            db_session.commit()
            flash("Your password has been updated! You are now able to log in", "success")
            return redirect(url_for("login"))
        return cls.render_template("reset_token.html", title="Reset Password", form=form)

    @classmethod
    def register_imc(cls):
        """IMC registration page"""
        if current_user.is_authenticated:
            return redirect(url_for("project_controller.home"))
        form = IMCRegistrationForm()
        if form.validate_on_submit():
            fake_id = randint(0, 99999999999)
            fake_email = str(fake_id) + "@arthurhjorth.com"
            fake_password = str(fake_id)
            hashed_password = generate_password_hash(fake_password).decode("utf-8")
            imc_org = Organization.query.filter_by(name="ATU").all()
            a_project = imc_org[0].projects[0]  # error when no project. out of range TODO
            the_name = form.username.data
            if any(User.query.filter_by(username=the_name)):
                the_name = the_name + str(fake_id)
            user = User(
                username=the_name, email=fake_email, password=hashed_password, organizations=imc_org
            )
            db_session.add(user)
            db_session.commit()
            login_user(user)
            userid = current_user.id
            name = current_user.username + "'s personal analysis"
            bayes_analysis = BayesianAnalysis(
                user=userid,
                name=name,
                project=a_project.id,
                data={"counts": 0, "words": {}},
                tweets=[],
                annotation_tags={},
                annotate=1,
            )
            db_session.add(bayes_analysis)
            db_session.commit()
            return redirect(url_for("project_controller.home"))
        return cls.render_template("register_imc.html", form=form)

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
