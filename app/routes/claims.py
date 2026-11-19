"""Claim submission by users who believe a found item is theirs."""

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from sqlalchemy import select

from app import db
from app.models import Claim, Item
from app.routes.helpers import login_required

claims_bp = Blueprint("claims", __name__, url_prefix="/claims")


@claims_bp.route("/new/<int:item_id>", methods=("GET", "POST"))
@login_required
def new(item_id):
    item = db.get_or_404(Item, item_id)
    if item.report_type != "found" or item.status != "available":
        abort(404)
    if item.user_id == g.user.id:
        abort(403)

    previous = db.session.scalar(
        select(Claim).where(
            Claim.item_id == item.id,
            Claim.user_id == g.user.id,
            Claim.status.in_(["pending", "approved"]),
        )
    )
    if previous:
        flash("You already have a pending or approved claim for this item.", "error")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        description = request.form.get("description", "").strip()
        identifying_information = request.form.get("identifying_information", "").strip()
        if not description or len(description) > 2000:
            flash("Explain why you believe the item is yours (up to 2,000 characters).", "error")
        elif not identifying_information or len(identifying_information) > 2000:
            flash("Add identifying details only the owner is likely to know (up to 2,000 characters).", "error")
        else:
            claim = Claim(
                item=item,
                claimant=g.user,
                description=description,
                identifying_information=identifying_information,
            )
            db.session.add(claim)
            db.session.commit()
            flash("Your claim was submitted for review.", "success")
            return redirect(url_for("dashboard.index"))

    return render_template("claims/new.html", item=item)
