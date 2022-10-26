@app.route("/add_project", methods=["GET", "POST"])
def add_project():
    """Add project page"""
    form = AddProjectForm()
    # find forst alle mulige organizations
    form.organization.choices = [(str(o.id), o.name)
                                 for o in Organization.query.all()]
    form.categories.choices = [(str(s.id), s.name)
                               for s in TweetTagCategory.query.all()]
    if form.validate_on_submit():
        # orgs = [int(n) for n in form.organization.data]
        # orgs_objs = Organization.query.filter(Organization.id.in_(orgs)).all()
        org = Organization.query.get(int(form.organization.data))
        cats = [int(n) for n in form.categories.data]
        a_project = nlp4all.utils.add_project(
            name=form.title.data, description=form.description.data, org=org.id, cat_ids=cats
        )
        project_id = a_project.id
        return redirect(url_for("home", project=project_id))
    return render_template("add_project.html", title="Add New Project", form=form)

# @TODO: refactor this, i moved this function here
# because it was in utils, which imported models which imported utils
def get_user_project_analyses(a_user, a_project): # pylint: disable=unused-argument
    """Get user project analyses"""
    analyses = BayesianAnalysis.query.filter_by(project=a_project.id)
    if current_user.admin:
        return analyses
    return [a for a in analyses if a.shared or a.shared_model or a.user == a_user.id]

@app.route("/project", methods=["GET", "POST"])
def project(): # pylint: disable=too-many-locals
    """Project page"""
    project_id = request.args.get("project", None, type=int)
    a_project = Project.query.get(project_id)
    form = AddBayesianAnalysisForm()
    analyses = (
        BayesianAnalysis.query.filter_by(
            user=current_user.id).filter_by(project=project_id).all()
    )
    analyses = get_user_project_analyses(current_user, a_project)
    form.annotate.choices = [(1, "No Annotations"),
                             (2, "Category names"), (3, "add own tags")]
    if form.validate_on_submit():
        userid = current_user.id
        name = form.name.data
        number_per_category = form.number.data
        analysis_tweets = []
        annotate = form.annotate.data
        if form.shared.data:
            tweets_by_cat = {
                cat: [t.id for t in a_project.tweets if t.category == cat.id]
                for cat in a_project.categories
            }
            for cat, tweets in tweets_by_cat.items():
                analysis_tweets.extend(sample(tweets, number_per_category))
        # make sure all students see tweets in the same order. So shuffle them now, and then
        # put them in the database
        shuffle(analysis_tweets)
        bayes_analysis = BayesianAnalysis(
            user=userid,
            name=name,
            project=a_project.id,
            data={"counts": 0, "words": {}},
            shared=form.shared.data,
            tweets=analysis_tweets,
            annotation_tags={},
            annotate=annotate,
            shared_model=form.shared_model.data,
        )
        db.session.add(bayes_analysis)
        db.session.commit()
        # this is where robot creation would go. Make one for everyone in
        # the org if it is a shared model, but not if it is a "shared",
        # meaning everyone tags the same tweets
        # @TODO: pretty sure this is broken
        org = Organization.query.get(a_project.organization)
        for _ in org.users:
            bayes_robot = BayesianRobot(
                name=current_user.username + "s robot", analysis=bayes_analysis.id)
            db.session.add(bayes_robot)
            db.session.flush()
            db.session.commit()
        # return(redirect(url_for('project', project=project_id)))
    return render_template(
        "project.html",
        title="About",
        project=a_project,
        analyses=analyses,
        form=form,
        user=current_user,
    )