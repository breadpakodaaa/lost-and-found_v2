"""Routes for reporting, browsing, and searching item reports."""

from datetime import date
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import select
from werkzeug.utils import secure_filename

from app import db
from app.models import Item
from app.routes.helpers import login_required
from app.services.matching import score_label, score_pair

items_bp = Blueprint("items", __name__, url_prefix="/items")

CATEGORIES = [
    "Electronics", "Clothing", "Books & stationery", "Keys & cards",
    "Personal belongings", "Sports equipment", "Other",
]


def save_image(upload):
    """Validate an optional image and save it under a safe, unique filename."""
    if upload is None or upload.filename == "":
        return None

    safe_original_name = secure_filename(upload.filename)
    if "." not in safe_original_name:
        raise ValueError("Choose a PNG, JPG, GIF, or WEBP image.")

    extension = safe_original_name.rsplit(".", 1)[1].lower()
    if extension not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        raise ValueError("Choose a PNG, JPG, GIF, or WEBP image.")
    if upload.mimetype not in {"image/png", "image/jpeg", "image/gif", "image/webp"}:
        raise ValueError("The selected file does not look like a supported image.")

    # The browser-supplied MIME type and filename can be forged, so also check
    # the file's leading bytes against the image format it claims to use.
    header = upload.stream.read(12)
    upload.stream.seek(0)
    signatures = {
        "png": header.startswith(b"\x89PNG\r\n\x1a\n"),
        "jpg": header.startswith(b"\xff\xd8\xff"),
        "jpeg": header.startswith(b"\xff\xd8\xff"),
        "gif": header.startswith((b"GIF87a", b"GIF89a")),
        "webp": header.startswith(b"RIFF") and header[8:12] == b"WEBP",
    }
    if not signatures[extension]:
        raise ValueError("The image contents do not match the selected file type.")

    filename = f"{uuid4().hex}.{extension}"
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    upload.save(upload_folder / filename)
    return filename


@items_bp.route("/report/<report_type>", methods=("GET", "POST"))
@login_required
def report(report_type):
    if report_type not in {"lost", "found"}:
        abort(404)

    form_values = request.form if request.method == "POST" else {}
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        location = request.form.get("location", "").strip()
        colour = request.form.get("colour", "").strip()
        date_text = request.form.get("item_date", "")
        error = None

        if not name or len(name) > 120:
            error = "Enter an item name of up to 120 characters."
        elif not description or len(description) > 3000:
            error = "Add a description (up to 3,000 characters)."
        elif category not in CATEGORIES:
            error = "Choose a category from the list."
        elif not location or len(location) > 160:
            error = "Enter a location of up to 160 characters."
        elif len(colour) > 50:
            error = "Colour must be 50 characters or fewer."

        try:
            item_date = date.fromisoformat(date_text)
            if item_date > date.today():
                error = "The item date cannot be in the future."
        except ValueError:
            item_date = None
            error = "Enter a valid date."

        image_filename = None
        if error is None:
            try:
                image_filename = save_image(request.files.get("image"))
            except ValueError as exc:
                error = str(exc)

        if error:
            flash(error, "error")
        else:
            item = Item(
                reporter=g.user,
                name=name,
                description=description,
                category=category,
                location=location,
                colour=colour or None,
                item_date=item_date,
                image_filename=image_filename,
                report_type=report_type,
                status="active" if report_type == "lost" else "available",
            )
            db.session.add(item)
            db.session.commit()
            flash("Your report has been posted. Review any suggested matches below.", "success")
            return redirect(url_for("items.matches", item_id=item.id))

    return render_template(
        "items/report.html",
        report_type=report_type,
        categories=CATEGORIES,
        today=date.today().isoformat(),
        form_values=form_values,
    )


@items_bp.get("/<int:item_id>/matches")
@login_required
def matches(item_id):
    """Show eligible opposite-type suggestions to the report's owner."""
    item = db.get_or_404(Item, item_id)
    if item.user_id != g.user.id:
        abort(403)

    if item.report_type == "lost" and item.status == "active":
        candidates = db.session.scalars(
            select(Item).where(Item.report_type == "found", Item.status == "available")
        ).all()
        pairs = [(item, candidate) for candidate in candidates]
    elif item.report_type == "found" and item.status == "available":
        candidates = db.session.scalars(
            select(Item).where(Item.report_type == "lost", Item.status == "active")
        ).all()
        pairs = [(candidate, item) for candidate in candidates]
    else:
        pairs = []

    weights = current_app.config["MATCH_WEIGHTS"]
    scored_matches = []
    for lost_item, found_item in pairs:
        result = score_pair(
            lost_item, found_item, weights,
            current_app.config["MATCH_DATE_WINDOW_DAYS"],
        )
        if result["score"] >= current_app.config["MATCH_MIN_SCORE"]:
            other_item = found_item if item.report_type == "lost" else lost_item
            scored_matches.append({
                "item": other_item,
                "score": result["score"],
                "label": score_label(
                    result["score"],
                    current_app.config["MATCH_POSSIBLE_SCORE"],
                    current_app.config["MATCH_STRONG_SCORE"],
                ),
                "components": result["components"],
            })
    scored_matches.sort(key=lambda entry: entry["score"], reverse=True)
    return render_template("items/matches.html", item=item, matches=scored_matches)


@items_bp.route("/<int:item_id>/edit", methods=("GET", "POST"))
@login_required
def edit(item_id):
    """Let only the reporter edit their listing's descriptive fields."""
    item = db.get_or_404(Item, item_id)
    if item.user_id != g.user.id:
        abort(403)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        location = request.form.get("location", "").strip()
        colour = request.form.get("colour", "").strip()
        date_text = request.form.get("item_date", "")
        error = None
        if not name or len(name) > 120:
            error = "Enter an item name of up to 120 characters."
        elif not description or len(description) > 3000:
            error = "Add a description of up to 3,000 characters."
        elif category not in CATEGORIES:
            error = "Choose a category from the list."
        elif not location or len(location) > 160:
            error = "Enter a location of up to 160 characters."
        elif len(colour) > 50:
            error = "Colour must be 50 characters or fewer."
        try:
            item_date = date.fromisoformat(date_text)
            if item_date > date.today():
                error = "The item date cannot be in the future."
        except ValueError:
            item_date = None
            error = "Enter a valid date."

        new_image = None
        if error is None:
            try:
                new_image = save_image(request.files.get("image"))
            except ValueError as exc:
                error = str(exc)

        if error:
            flash(error, "error")
        else:
            item.name = name
            item.description = description
            item.category = category
            item.location = location
            item.colour = colour or None
            item.item_date = item_date
            if new_image:
                old_image = item.image_filename
                item.image_filename = new_image
                if old_image:
                    old_path = Path(current_app.config["UPLOAD_FOLDER"]) / old_image
                    old_path.unlink(missing_ok=True)
            elif request.form.get("remove_image") == "yes" and item.image_filename:
                old_path = Path(current_app.config["UPLOAD_FOLDER"]) / item.image_filename
                old_path.unlink(missing_ok=True)
                item.image_filename = None
            db.session.commit()
            flash("Your listing was updated.", "success")
            return redirect(url_for("dashboard.index"))

    return render_template(
        "items/edit.html", item=item, categories=CATEGORIES,
        today=date.today().isoformat(),
    )


@items_bp.post("/<int:item_id>/delete")
@login_required
def delete(item_id):
    """Delete a listing owned by the current user."""
    item = db.get_or_404(Item, item_id)
    if item.user_id != g.user.id:
        abort(403)
    if item.image_filename:
        image_path = Path(current_app.config["UPLOAD_FOLDER"]) / item.image_filename
        image_path.unlink(missing_ok=True)
    db.session.delete(item)
    db.session.commit()
    flash("Your listing was removed.", "success")
    return redirect(url_for("dashboard.index"))


@items_bp.get("/")
def browse():
    report_type = request.args.get("type", "all").lower()
    if report_type not in {"all", "lost", "found"}:
        report_type = "all"

    statement = select(Item).order_by(Item.created_at.desc())
    if report_type == "lost":
        statement = statement.where(Item.report_type == "lost")
    elif report_type == "found":
        statement = statement.where(Item.report_type == "found")

    name = request.args.get("name", "").strip()
    location = request.args.get("location", "").strip()
    category = request.args.get("category", "")
    date_text = request.args.get("date", "")
    if name:
        statement = statement.where(Item.name.ilike(f"%{name}%"))
    if location:
        statement = statement.where(Item.location.ilike(f"%{location}%"))
    if category in CATEGORIES:
        statement = statement.where(Item.category == category)
    if date_text:
        try:
            statement = statement.where(Item.item_date == date.fromisoformat(date_text))
        except ValueError:
            flash("The date filter was not a valid date.", "error")

    items = db.session.scalars(statement).all()
    return render_template(
        "items/browse.html", items=items, report_type=report_type,
        categories=CATEGORIES,
        filters={"name": name, "location": location, "category": category, "date": date_text},
    )
