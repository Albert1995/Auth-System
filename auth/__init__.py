from uuid import uuid4
from flask import Flask, redirect, render_template, request, session, url_for
from sassutils.wsgi import SassMiddleware

app = Flask(__name__)
app.secret_key = str(uuid4())

users = {}

msg_success = {
    "new_user": "User created successfully",
    "logout_user": "You logout the system",
    "delete_user": "You deleted your account successfully",
}

if app.config["ENV"] == "development":
    app.wsgi_app = SassMiddleware(
        app.wsgi_app, {"auth": ("static/sass", "static/css", "/static/css")}
    )


def validate_authentication(email, password) -> bool:
    return email in users and users[email]["password"] == password


def create_token_for(email: str):
    session["token"] = str(uuid4())
    users[email]["token"] = session["token"]


@app.route("/", methods=["GET", "POST"])
def auth_page():
    if request.method == "GET":
        if session.get("token"):
            return render_template("welcome.html")
        return render_template(
            "login.html", msg_success=msg_success.get(request.args.get("msg"))
        )

    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return render_template(
            "login.html",
            msg_error="E-mail and Password are required to login in platform.",
        )

    if validate_authentication(email, password):
        create_token_for(email)
        return render_template("welcome.html")

    return render_template(
        "login.html", msg_error="E-mail and Password are wrong, please try again."
    )


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    if request.form.get("act") == "cancel":
        return redirect("/")

    email = request.form.get("email")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm-password")

    msg_errors = []

    if not email:
        msg_errors.append("E-mail is required")

    if not password:
        msg_errors.append("Password is required")

    if not confirm_password:
        msg_errors.append("Confirm Password is required")

    if email and email in users:
        msg_errors.append("E-mail already in use, please choose another one")

    if password and confirm_password and password != confirm_password:
        msg_errors.append("Password and its confirmation are different")

    if msg_errors:
        return render_template("signup.html", msg_errors=msg_errors)

    users[email] = {"password": password, "email": email}

    return redirect(url_for("auth_page", msg="new_user"))


@app.route("/logout", methods=["POST"])
def logout():
    for user in users.items():
        if user[1]["token"] == session["token"]:
            user[1]["token"] = ""
            break

    session["token"] = ""
    return redirect(url_for("auth_page", msg="logout_user"))


@app.route("/delete", methods=["POST"])
def delete_user():
    for user in users.values():
        if user["token"] == session["token"]:
            email_to_del = user["email"]
            break

    del users[email_to_del]
    session["token"] = ""
    return redirect(url_for("auth_page", msg="delete_user"))
