from flask import render_template

from app import app


@app.route("/")
@app.route("/home")
def home():
    return render_template("home_page.html")


@app.route("/watchlist")
def watchlist():
    return render_template("watchlist_page.html")


@app.route("/search")
def search():
    return render_template("searchresult_page.html")


@app.route("/movie/<int:movie_id>")
def movie(movie_id):
    return render_template("movie_page.html")


@app.route("/profile")
def profile():
    return render_template("my_profile.html")


@app.route("/user/<int:user_id>")
def user_profile(user_id):
    return render_template("other_profile.html")
