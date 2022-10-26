"""User info, registration, etc, routes."""


@app.route("/ATU", methods=["GET", "POST"])
def imc():
    """IMC registration start page"""
    return redirect(url_for("register_imc"))


@app.route("/register_imc", methods=["GET", "POST"])
def register_imc():
    """IMC registration page"""
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = IMCRegistrationForm()
    if form.validate_on_submit():
        fake_id = randint(0, 99999999999)
        fake_email = str(fake_id) + "@arthurhjorth.com"
        fake_password = str(fake_id)
        hashed_password = bcrypt.generate_password_hash(
            fake_password).decode("utf-8")
        imc_org = Organization.query.filter_by(name="ATU").all()
        a_project = imc_org[0].projects[0] #error when no project. out of range TODO
        the_name = form.username.data
        if any(User.query.filter_by(username=the_name)):
            the_name = the_name + str(fake_id)
        user = User(
            username=the_name, email=fake_email, password=hashed_password, organizations=imc_org
        )
        db.session.add(user)
        db.session.commit()
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
        db.session.add(bayes_analysis)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("register_imc.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register page"""
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    form.organizations.choices = [(str(o.id), o.name)
                                  for o in Organization.query.all()]
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode("utf-8")
        org = Organization.query.get(int(form.organizations.data))
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            organizations=[org],
        )
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created! You are now able to log in", "success")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)



@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    """Account page"""
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated!", "success")
        return redirect(url_for("account"))
    if request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for(
        "static", filename="profile_pics/" + current_user.image_file)
    return render_template("account.html", title="Account", image_file=image_file, form=form)



@app.route("/reset_password", methods=["GET", "POST"])
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


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    """Reset password token page"""
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    user = User.verify_reset_token(token)
    if user in ('Expired', 'Invalid'):
        flash(f"That is an {user} token", "warning")
        return redirect(url_for("reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode("utf-8")
        user.password = hashed_password
        db.session.commit()
        flash("Your password has been updated! You are now able to log in", "success")
        return redirect(url_for("login"))
    return render_template("reset_token.html", title="Reset Password", form=form)

