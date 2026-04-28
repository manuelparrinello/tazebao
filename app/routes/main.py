from flask import Blueprint, current_app, render_template


bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template(
        "index.html",
        title="Home",
        description="Welcome to the Home Page",
        path=current_app.config["DB_PATH"],
    )


@bp.route("/test")
def test():
    return render_template("base.html")
