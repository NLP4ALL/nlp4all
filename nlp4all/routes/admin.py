
@app.route("/manage_categories", methods=["GET", "POST"])
@login_required
def manage_categories():
    """Manage categories page"""
    form = AddTweetCategoryForm()
    categories = [cat.name for cat in TweetTagCategory.query.all()]
    if form.validate_on_submit():
        nlp4all.utils.add_tweets_from_account(form.twitter_handle.data)
        flash("Added tweets from the twitter handle", "success")
        return redirect(url_for("manage_categories"))
    return render_template("manage_categories.html", form=form, categories=categories)


@app.route("/add_org", methods=["GET", "POST"])
@login_required
def add_org():
    """Add organization page"""
    form = AddOrgForm()
    orgs = Organization.query.all()
    if form.validate_on_submit():
        org = Organization(name=form.name.data)
        db.session.add(org)
        db.session.commit()
        flash("Your organization has been created!", "success")
        return redirect(url_for("add_org"))
    return render_template("add_org.html", form=form, orgs=orgs)

def send_reset_email(user):
    """Send reset email"""
    token = user.get_reset_token()
    msg = Message("Password Reset Request",
                  sender="noreply@demo.com", recipients=[user.email])
    msg.body = f"""To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
"""
    mail.send(msg)

