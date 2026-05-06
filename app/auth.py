from flask import render_template, redirect, url_for
from flask_login import logout_user

from app import app


@app.route("/auth")
def auth():
    return render_template("auth.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))
