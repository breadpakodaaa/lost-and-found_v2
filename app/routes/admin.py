"""Administrator tools for reviewing claims and managing reports."""

from pathlib import Path

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from sqlalchemy import select

from app import db
from app.models import Claim, Item, User
from app.routes.helpers import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
@admin_required
def index():
    users = db.session.scalars(select(User).order_by(User.created_at.desc())).all()
    items = db.session.scalars(select(Item).order_by(Item.created_at.desc())).all()
    claims = db.session.scalars(select(Claim).order_by(Claim.created_at.desc())).all()
    return render_template("admin/index.html", users=users, items=items, claims=claims)


@admin_bp.post("/claims/<int:claim_id>/<decision>")
@admin_required
def review_claim(claim_id, decision):
    claim = db.get_or_404(Claim, claim_id)
    if decision not in {"approved", "rejected"} or claim.status != "pending":
        abort(400)
    if decision == "approved" and (
        claim.item.report_type != "found"
        or claim.item.status not in {"available", "claimed"}
    ):
        abort(400)

    claim.status = decision
    if decision == "approved":
        claim.item.status = "claimed"
        # Only one claim should remain approved for a found item.
        other_pending = db.session.scalars(
            select(Claim).where(
                Claim.item_id == claim.item_id,
                Claim.id != claim.id,
                Claim.status == "pending",
            )
        ).all()
        for other in other_pending:
            other.status = "rejected"
    db.session.commit()
    flash(f"Claim {decision}.", "success")
    return redirect(url_for("admin.index"))


@admin_bp.post("/items/<int:item_id>/status")
@admin_required
def update_status(item_id):
    item = db.get_or_404(Item, item_id)
    status = request.form.get("status", "")
    allowed = {"lost": {"active", "matched", "resolved"},
               "found": {"available", "claimed", "returned"}}
    if item.report_type not in allowed or status not in allowed[item.report_type]:
        abort(400)
    item.status = status
    db.session.commit()
    flash("Listing status updated.", "success")
    return redirect(url_for("admin.index"))


@admin_bp.post("/items/<int:item_id>/delete")
@admin_required
def remove_item(item_id):
    item = db.get_or_404(Item, item_id)
    if item.image_filename:
        image_path = Path(current_app.config["UPLOAD_FOLDER"]) / item.image_filename
        image_path.unlink(missing_ok=True)
    db.session.delete(item)
    db.session.commit()
    flash("Listing removed.", "success")
    return redirect(url_for("admin.index"))
