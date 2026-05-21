import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Инициализация БД для Flask"""
    database_url = os.getenv("DATABASE_URL", "sqlite:///ugc.db")

    if database_url.startswith("sqlite"):
        if os.getenv("RUNNING_IN_DOCKER") or "/app/" in database_url:
            pass
        else:
            db_filename = database_url.replace("sqlite:///", "")
            if not os.path.isabs(db_filename):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(base_dir, db_filename)
                database_url = f"sqlite:///{db_path.replace(os.sep, '/')}"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = os.getenv("DEBUG", "False") == "True"

    db.init_app(app)

    with app.app_context():
        db.create_all()