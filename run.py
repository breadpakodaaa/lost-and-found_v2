"""Local development entry point."""

import os

from app import create_app, db

app = create_app()


if __name__ == "__main__":
    # Convenient for Phase 2. Later, database migrations will manage schema changes.
    with app.app_context():
        db.create_all()
    # The interactive debugger is powerful; enable it only when explicitly asked.
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
