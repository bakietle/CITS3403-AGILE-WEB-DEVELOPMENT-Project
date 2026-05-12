from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from app.config import Config


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Global CSRF protection for all state-changing requests (POST/PUT/PATCH/DELETE).
# Forms built with FlaskForm already include a token via {{ form.hidden_tag() }};
# AJAX callers must send the token as X-CSRFToken header (the templates expose
# it via <meta name="csrf-token" content="{{ csrf_token() }}">).
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = "auth"

from app import auth, models, routes, seed
