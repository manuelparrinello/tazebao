from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..models import User


bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email).first()

        if user is None or not user.is_active or not user.check_password(password):
            flash("Credenziali non valide.", "danger")
            return render_template("login.html", email=email), 401

        session.clear()
        session["user_id"] = user.id

        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("index"))

    return render_template("login.html")


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
