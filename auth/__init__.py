from functools import wraps
from typing import Dict
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
    "force-logout": "Force logout done!"
}

msg_warning = {
    "login_first": "Please, login first before access internal pages",
    "already_login": """    
    Sorry, there is another user using your credentials.<br />
    <a onclick="forceLogout()">Click here</a>, to force logout. 
    If you don't recognize who are using, we do recommend you to change your password now.
    """
}

msg_error = {
    "login_fail": "E-mail and Password are wrong, please try again."
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
    sql = "SELECT email, password, token FROM users WHERE email = ?"
    sql_params = (email, )
    
    with db.create_connection() as connection:
        db_cursor = connection.cursor()
        db_cursor.execute(sql, sql_params)
        result = db_cursor.fetchone()
        
    return {
        "email": result[0],
        "password": result[1],
        "token": result[2]
    } if result else {}
    
        
def create_user(email: str, password: str) -> None:
    with db.create_connection() as connection:
        db_cursor = connection.cursor()
        db_cursor.execute("insert into users (email, password) values (?, ?)", (email, password))
        
        
def delete_user():
    with db.create_connection() as connection:
        db_cursor = connection.cursor()
        db_cursor.execute("delete from users where token = ?", (session["token"],))
       

def logout_user(email: str | None = None):
    with db.create_connection() as connection:
        db_cursor = connection.cursor()
        if email:
            db_cursor.execute("update users set token = null where email = ?", (email,))
        else:
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


def validate_user_logged_in(email: str) -> bool:
    user = search_user_by_email(email)
    
    try:
        if user["token"]:
            jwt.decode(user["token"], app.config["JWT_SECRET"], algorithms="HS256")
            return True
    except jwt.ExpiredSignatureError:
        with db.create_connection() as connection:
            db_cursor = connection.cursor()
            db_cursor.execute("update users set token = null where token = ?", (user["token"],))
    
    return False
    

def create_token(email: str):
    jwt_payload = {
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=10)
    }
    token = jwt.encode(jwt_payload, app.config["JWT_SECRET"], algorithm="HS256")
    
    set_token_for_user_by_email(email, token)
    session["token"] = token
    
def validate_session() -> bool:
    if not "token" in session or not session["token"]:
        return False
    
    try:
        jwt.decode(session["token"], app.config["JWT_SECRET"], algorithms="HS256")
    except jwt.ExpiredSignatureError:
        return False
    
    return True


def login_required(fn):
    @wraps(fn)
    def wrapper():
        if validate_session():
            return fn()
        
        return redirect(url_for("login_page", msg="login_first"))
    
    return wrapper


@app.route("/")
def index():
    if validate_session():
        return redirect(url_for("welcome"))
    
    return redirect(url_for("login_page"))
    
    
@app.route("/welcome")
@login_required
def welcome():
    return render_template("welcome.html")

    
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        if validate_session():
            return redirect(url_for("welcome"))
        return render_template(
            "login.html", 
            msg_success=msg_success.get(request.args.get("msg")),
            msg_warning=msg_warning.get(request.args.get("msg")),
        )

    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return render_template(
            "login.html",
            msg_error="E-mail and Password are required to login in platform.",
        )

    if validate_authentication(email, password):
        if not validate_user_logged_in(email):
            create_token(email)
            return redirect(url_for("welcome"))
        else:
            return render_template(
                "login.html", 
                msg_warning=msg_warning["already_login"]
            )
            
    return render_template(
        "login.html", 
        msg_error=msg_error["login_fail"]
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

    return redirect(url_for("login_page", msg="new_user"))


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session["token"] = ""
    return redirect(url_for("login_page", msg="logout_user"))


@app.route("/delete", methods=["POST"])
@login_required
def delete_user_route():
    delete_user()
    session["token"] = ""
    return redirect(url_for("login_page", msg="delete_user"))


@app.route("/change-password", methods=["POST"])
@login_required
def change_passwd():
    
    return redirect(url_for("welcome", msg="change-pw-success"))


@app.route("/force-logout", methods=["POST"])
def force_logout():
    logout_user(request.form["email"])
    return redirect(url_for("login_page", msg="force-logout"))
