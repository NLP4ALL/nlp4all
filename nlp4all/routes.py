import os
import secrets
import nlp4all.utils
from random import sample
from PIL import Image
from nlp4all.utils import add_css_class
from flask import render_template, url_for, flash, redirect, request, abort
from nlp4all import app, db, bcrypt, mail
from nlp4all.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm, AddOrgForm, AddBayesianAnalysisForm, AddProjectForm, TaggingForm
from nlp4all.models import User, Organization, Project, BayesianAnalysis, TweetTagCategory, TweetTag
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import json
from sqlalchemy.orm.attributes import flag_modified


@app.route("/")
@app.route("/home")
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    user_orgs = [org.id for org in current_user.organizations]
    my_projects = Project.query.filter(Project.organization.in_(user_orgs)).all()
    return render_template('home.html', projects=my_projects)


@app.route("/add_project", methods=['GET', 'POST'])
def add_project():
    form = AddProjectForm()
    # find forst alle mulige organizations
    form.organization.choices = [( str(o.id), o.name ) for o in Organization.query.all()]
    form.categories.choices = [( str(s.id), s.name ) for s in TweetTagCategory.query.all()]
    if form.validate_on_submit():
        # orgs = [int(n) for n in form.organization.data]
        # orgs_objs = Organization.query.filter(Organization.id.in_(orgs)).all()
        org = Organization.query.get(int(form.organization.data))
        cats = [int(n) for n in form.categories.data]
        cats_objs = TweetTagCategory.query.filter(TweetTagCategory.id.in_(cats)).all()
        new_project = Project(name=form.title.data, description=form.description.data, organization=org.id, categories=cats_objs)
        db.session.add(new_project)
        db.session.commit()
        flash('New Project Created!', 'success')
    return render_template('add_project.html', title='Add New Projec5', form=form)

@app.route("/project", methods=['GET', "POST"])
def project():
    project_id = request.args.get('project', None, type=int)
    project = Project.query.get(project_id)
    form = AddBayesianAnalysisForm()
    analyses = BayesianAnalysis.query.filter_by(user = current_user.id).filter_by(project=project_id).all()
    if form.validate_on_submit():
        userid = current_user.id
        name = form.name.data
        filters = []
        features = []
        filters = json.dumps([])
        features = json.dumps([])
        tags = project.categories
        analysis = BayesianAnalysis(user = userid, name=name, filters=filters, features=features,project=project.id, data = {"counts" : 0, "words" : {}})
        db.session.add(analysis)
        db.session.commit()
        return(redirect(url_for('project', project=project_id)))
    return render_template('project.html', title='About', project=project, analyses=analyses, form=form)


@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/analysis", methods=['GET', 'POST'])
def analyis():
    analysis_id = request.args.get('analysis', 1, type=int)
    analysis = BayesianAnalysis.query.get(analysis_id)
    project = Project.query.get(analysis.project)
    categories = TweetTagCategory.query.filter(TweetTagCategory.id.in_([p.id for p in project.categories])).all()
    tweets = [t for cat in categories for t in cat.tweets]
    the_tweet = sample(tweets, 1)[0]
    form = TaggingForm()
    form.choices.choices  = [( str(c.id), c.name ) for c in categories]
    number_of_tagged = len(analysis.tags)
    data = {}
    data['number_of_tagged']  = number_of_tagged
    data['words'], data['predictions'] = analysis.get_predictions_and_words(set(the_tweet.words))
    data['word_tuples'] = add_css_class(data['words'], the_tweet.full_text)
    if form.validate_on_submit():
        category = TweetTagCategory.query.get(int(form.choices.data))
        analysis.data = analysis.updated_data(the_tweet, category)
        ## all this  stuff is necessary  because the database backend doesnt resgister
        ## changes on JSON
        flag_modified(analysis, "data")
        db.session.add(analysis)
        db.session.merge(analysis)
        db.session.flush()
        db.session.commit()
        tag = TweetTag (category = category.id, analysis = analysis.id, tweet=the_tweet.id)
        db.session.add(tag)
        db.session.commit()
    return render_template('analysis.html', analysis=analysis, tweet = the_tweet, form = form, **data)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    form.organization.choices = [(str(o.id), o.name) for o in Organization.query.all()]
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        org = Organization.query.get(int(form.organization.data)).id
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, organization=org)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

@app.route("/add_org", methods=['GET', 'POST'])
@login_required
def add_org():
    form = AddOrgForm()
    orgs = Organization.query.all()
    if form.validate_on_submit():
        print(form.name.data)
        org = Organization(name=form.name.data)
        db.session.add(org)
        db.session.commit()
        flash('Your organization has been created!', 'success')
        return redirect(url_for('add_org'))
    return render_template('add_org.html', form=form, orgs=orgs)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@app.route("/analysis")
def analysis():
    return redirect(url_for('home'))

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
