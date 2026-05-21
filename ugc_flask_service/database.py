import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Инициализация БД для Flask"""
    database_url = os.getenv("DATABASE_URL", "sqlite:///ugc.db")

    if database_url.startswith("sqlite"):
        database_url = database_url.replace("sqlite:///", "sqlite:////app/")

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = os.getenv("DEBUG", "False") == "True"

    db.init_app(app)

    with app.app_context():
        db.create_all()