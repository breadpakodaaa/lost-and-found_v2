"""Database tables for users, item reports, and claims."""

from datetime import date, datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def utc_now():
    """Return a timezone-aware UTC timestamp for newly created records."""
    return datetime.now(timezone.utc)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    items = db.relationship("Item", back_populates="reporter", cascade="all, delete-orphan")
    claims = db.relationship("Claim", back_populates="claimant", cascade="all, delete-orphan")

    def set_password(self, password):
        """Hash a password before it is stored; never save the original text."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check a submitted password against the saved hash."""
        return check_password_hash(self.password_hash, password)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True)
    colour = db.Column(db.String(50))
    location = db.Column(db.String(160), nullable=False, index=True)
    item_date = db.Column(db.Date, nullable=False, default=date.today)
    image_filename = db.Column(db.String(255))
    report_type = db.Column(db.String(10), nullable=False, index=True)  # lost or found
    status = db.Column(db.String(20), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    reporter = db.relationship("User", back_populates="items")
    claims = db.relationship("Claim", back_populates="item", cascade="all, delete-orphan")


class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    identifying_information = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    item = db.relationship("Item", back_populates="claims")
    claimant = db.relationship("User", back_populates="claims")
