from typing import Dict
from uuid import uuid4
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
from flask import Flask, redirect, render_template, request, session, url_for
from sassutils.wsgi import SassMiddleware

from auth import config, database

msg_success = {
    "new_user": "User created successfully",
    "logout_user": "You logout the system",
    "delete_user": "You deleted your account successfully",
}

app = Flask(__name__)
env = app.config["ENV"] or "production"

app.config.from_object(config.config[env])

db = database.DatabaseManager(app)

# Convert SASS into CSS on the fly only in development mode
if env == "development":
    app.wsgi_app = SassMiddleware(
        app.wsgi_app, {"auth": ("static/sass", "static/css", "/static/css")}
    )


def search_user_by_email(email: str) -> Dict:
    sql = "SELECT email, password FROM users WHERE email = ?"
    sql_params = (email, )
    
    with db.create_connection() as connection:
        db_cursor = connection.cursor()
        db_cursor.execute(sql, sql_params)
        result = db_cursor.fetchone()
        
    return {
        "email": result[0],
        "password": result[1]
    } if result else {}
    
        
def create_user(email: str, password: str) -> None:
    with db.create_connection() as connection:
        db_cursor = connection.cursor()
        db_cursor.execute("insert into users (email, password) values (?, ?)", (email, password))
        
        
def delete_user():
    with db.create_connection() as connection:
        db_cursor = connection.cursor()
        db_cursor.execute("delete from users where token = ?", (session["token"],))
       

def logout_user():
    with db.create_connection() as connection:
        db_cursor = connection.cursor()
        db_cursor.execute("update users set token = null where token = ?", (session["token"],))
        
def set_token_for_user_by_email(email: str, token: str):
    with db.create_connection() as connection:
        db_cursor = connection.cursor()
        db_cursor.execute("update users set token = ? where email = ?", (token, email))
    

def validate_authentication(email: str, password: str) -> bool:
    user = search_user_by_email(email)
    
    if not user: 
        return False
    
    return bcrypt.checkpw(password.encode(), user["password"])


def create_token(email: str):
    jwt_payload = {
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=10)
    }
    token = jwt.encode(jwt_payload, app.config["JWT_SECRET"], algorithm="HS256")
    
    set_token_for_user_by_email(email, token)
    session["token"] = token

    
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
        create_token(email)
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

    if search_user_by_email(email):
        msg_errors.append("E-mail already in use, please choose another one")

    if password and confirm_password and password != confirm_password:
        msg_errors.append("Password and its confirmation are different")

    if msg_errors:
        return render_template("signup.html", msg_errors=msg_errors)

    create_user(email, bcrypt.hashpw(password.encode(), bcrypt.gensalt()))

    return redirect(url_for("auth_page", msg="new_user"))


@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    session["token"] = ""
    return redirect(url_for("auth_page", msg="logout_user"))


@app.route("/delete", methods=["POST"])
def delete_user_route():
    delete_user()
    session["token"] = ""
    return redirect(url_for("auth_page", msg="delete_user"))
