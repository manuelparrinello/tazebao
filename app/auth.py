from functools import wraps

from flask import flash, g, jsonify, redirect, request, session, url_for

from .extensions import db
from .models import User


PUBLIC_ENDPOINTS = {
    "static",
    "login",
    "auth.login",
    "editorial_share.view_shared",
    "editorial_share.publication_detail",
}


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def is_api_request():
    return request.path.startswith("/api/")


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.get("current_user") is None:
            if is_api_request():
                return (
                    jsonify(
                        {
                            "success": False,
                            "data": None,
                            "error": "Authentication required",
                        }
                    ),
                    401,
                )
            return redirect(url_for("login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped_view


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            user = g.get("current_user")
            if user is None:
                if is_api_request():
                    return (
                        jsonify(
                            {
                                "success": False,
                                "data": None,
                                "error": "Authentication required",
                            }
                        ),
                        401,
                    )
                return redirect(url_for("login", next=request.full_path))
            if user.role not in roles:
                if is_api_request():
                    return (
                        jsonify({"success": False, "data": None, "error": "Forbidden"}),
                        403,
                    )
                flash("Accesso non autorizzato.", "warning")
                return redirect(url_for("main.app_shell"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def register_auth_guards(app):
    @app.before_request
    def load_logged_in_user():
        g.current_user = current_user()

        if request.endpoint in PUBLIC_ENDPOINTS:
            return None

        if request.endpoint is None:
            return None

        if g.current_user is None:
            if is_api_request():
                return (
                    jsonify(
                        {
                            "success": False,
                            "data": None,
                            "error": "Authentication required",
                        }
                    ),
                    401,
                )
            return redirect(url_for("login", next=request.full_path))

        return None

    @app.context_processor
    def inject_current_user():
        return {"current_user": g.get("current_user")}
