"""Personal dashboard for a signed-in campus member."""

from flask import Blueprint, g, render_template
from sqlalchemy import select

from app import db
from app.models import Claim, Item
from app.routes.helpers import login_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.get("/")
@login_required
def index():
    items = db.session.scalars(
        select(Item).where(Item.user_id == g.user.id).order_by(Item.created_at.desc())
    ).all()
    claims = db.session.scalars(
        select(Claim).where(Claim.user_id == g.user.id).order_by(Claim.created_at.desc())
    ).all()
    received_claims = db.session.scalars(
        select(Claim).join(Item).where(Item.user_id == g.user.id)
        .order_by(Claim.created_at.desc())
    ).all()
    return render_template(
        "dashboard/index.html", items=items, claims=claims,
        received_claims=received_claims,
    )
