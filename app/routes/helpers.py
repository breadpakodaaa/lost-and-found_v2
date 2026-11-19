"""Small access-control helpers shared by route modules."""

from functools import wraps

from flask import abort, flash, g, redirect, url_for


def login_required(view):
    """Send visitors to sign in before a protected action."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    """Allow only signed-in users whose role is administrator."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("auth.login"))
        if g.user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped
