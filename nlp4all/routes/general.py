
@app.route("/")
@app.route("/home")
@app.route("/home/", methods=["GET", "POST"])

@login_required
def home():
    """Home page"""
    my_projects = get_user_projects(current_user)
    return render_template("home.html", projects=my_projects)


@app.route("/about")
def about():
    """About page"""
    return render_template("about.html", title="About")
