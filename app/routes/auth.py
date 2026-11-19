"""Registration, login, and logout routes."""

import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import select

from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


def valid_email(email):
    """A beginner-friendly format check; the database also enforces uniqueness."""
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email))


@auth_bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")
        error = None

        if not name or len(name) > 80:
            error = "Enter your name (up to 80 characters)."
        elif len(email) > 255 or not valid_email(email):
            error = "Enter a valid email address."
        elif len(password) < 8:
            error = "Choose a password with at least 8 characters."
        elif password != confirmation:
            error = "The passwords do not match."
        elif db.session.scalar(select(User).where(User.email == email)):
            error = "An account with that email already exists."

        if error:
            flash(error, "error")
            return render_template("auth/register.html", name=name, email=email)

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session.clear()
        session["user_id"] = user.id
        flash("Your account is ready. Welcome!", "success")
        return redirect(url_for("index"))

    return render_template("auth/register.html", name="", email="")


@auth_bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = db.session.scalar(select(User).where(User.email == email))

        if user is None or not user.check_password(password):
            flash("Check your email and password, then try again.", "error")
            return render_template("auth/login.html", email=email)

        session.clear()
        session["user_id"] = user.id
        flash("You are signed in.", "success")
        return redirect(url_for("index"))

    return render_template("auth/login.html", email="")


@auth_bp.post("/logout")
def logout():
    session.clear()
    flash("You are signed out.", "success")
    return redirect(url_for("index"))
