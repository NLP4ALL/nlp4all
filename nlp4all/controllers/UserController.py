"""User / Login related controller."""

import os
import secrets
from PIL import Image
from flask_bcrypt import check_password_hash, generate_password_hash

from flask import flash, redirect, render_template, request, url_for, Blueprint
from flask_login import current_user, login_user, logout_user

from nlp4all.models.database import db_session
from nlp4all.models import Organization, User

from nlp4all.forms.user import LoginForm, UpdateAccountForm, RegistrationForm


class UserController:
    """User Controller"""

    blueprint: Blueprint

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
            return redirect(url_for("account"))
        if request.method == "GET":
            form.username.data = current_user.username
            form.email.data = current_user.email
        image_file = url_for(
            "static", filename="profile_pics/" + current_user.image_file)
        return render_template("account.html", title="Account", image_file=image_file, form=form)

    @classmethod
    def save_picture(cls, form_picture):
        """Save picture"""
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(
            cls.blueprint.root_path, "static/profile_pics", picture_fn)

        output_size = (125, 125)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)

        return picture_fn
    
    @classmethod
    def login(cls):
        """Login page"""
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get("next")
                return redirect(next_page) if next_page else redirect(url_for("home"))
            flash("Login Unsuccessful. Please check email and password", "danger")
        return render_template("login.html", title="Login", form=form)

    @classmethod
    def logout(cls):
        """Logout page"""
        logout_user()
        return redirect(url_for("home"))

    @classmethod
    def register(cls):
        """Register page"""
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        form = RegistrationForm()
        form.organizations.choices = [(str(o.id), o.name)
                                    for o in Organization.query.all()]
        if form.validate_on_submit():
            hashed_password = generate_password_hash(
                form.password.data).decode("utf-8")
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
        return render_template("register.html", title="Register", form=form)

    @classmethod
    def reset_request():
        """Reset password request page"""
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        form = RequestResetForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            send_reset_email(user)
            flash("An email has been sent with instructions to reset your password.", "info")
            return redirect(url_for("login"))
        return render_template("reset_request.html", title="Reset Password", form=form)