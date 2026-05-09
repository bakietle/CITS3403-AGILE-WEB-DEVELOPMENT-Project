from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(message="Please enter a valid email address."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Please enter your password.")],
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Enter the Stage")


class SignupForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Please choose a username."),
            Length(
                min=3,
                max=64,
                message="Username must be between 3 and 64 characters.",
            ),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(message="Please enter a valid email address."),
            Length(max=120, message="Email must be 120 characters or fewer."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please enter a password."),
            Length(min=8, message="Password must be at least 8 characters."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Join Movie Star")
