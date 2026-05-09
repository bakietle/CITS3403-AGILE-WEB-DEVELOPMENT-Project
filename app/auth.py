from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import app, db
from app.forms import LoginForm, SignupForm
from app.models import User


def flash_form_errors(form):
    for errors in form.errors.values():
        for error in errors:
            flash(error, "error")


@app.route("/auth")
def auth():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    login_form = LoginForm()
    signup_form = SignupForm()
    return render_template(
        "auth.html", login_form=login_form, signup_form=signup_form
    )


@app.route("/login", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    login_form = LoginForm()
    signup_form = SignupForm()

    if login_form.validate_on_submit():
        email = login_form.email.data.lower().strip()
        user = db.session.scalar(db.select(User).where(User.email == email))

        if user is None or not user.check_password(login_form.password.data):
            flash("Invalid email or password.", "error")
            return (
                render_template(
                    "auth.html", login_form=login_form, signup_form=signup_form
                ),
                401,
            )

        login_user(user, remember=login_form.remember_me.data)
        next_page = request.args.get("next")

        if not next_page or not next_page.startswith("/") or next_page.startswith("//"):
            next_page = url_for("home")

        return redirect(next_page)

    flash_form_errors(login_form)
    return (
        render_template("auth.html", login_form=login_form, signup_form=signup_form),
        400,
    )


@app.route("/signup", methods=["POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    login_form = LoginForm()
    signup_form = SignupForm()

    if signup_form.validate_on_submit():
        username = signup_form.username.data.strip()
        email = signup_form.email.data.lower().strip()

        username_exists = db.session.scalar(
            db.select(User).where(User.username == username)
        )
        email_exists = db.session.scalar(db.select(User).where(User.email == email))

        if username_exists or email_exists:
            if username_exists:
                flash("That username is already taken.", "error")
            if email_exists:
                flash("That email address is already registered.", "error")
            return (
                render_template(
                    "auth.html", login_form=login_form, signup_form=signup_form
                ),
                409,
            )

        user = User(username=username, email=email)
        user.set_password(signup_form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Welcome to Movie Star.", "success")
        return redirect(url_for("profile"))

    flash_form_errors(signup_form)
    return (
        render_template("auth.html", login_form=login_form, signup_form=signup_form),
        400,
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))
