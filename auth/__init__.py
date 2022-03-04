from crypt import methods
from flask import Flask, render_template, request
from sassutils.wsgi import SassMiddleware

app = Flask(__name__)

users = [
    {
        "email": "test@domain.com",
        "password": "123"
    }
]

app.wsgi_app = SassMiddleware(
    app.wsgi_app, {"auth": ("static/sass", "static/css", "/static/css")}
)


def validate_authentication(email, password):
    return email == "test.email@domain.com" and password == "123"


@app.route("/", methods=["GET", "POST"])
def auth_page():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return render_template(
            "login.html",
            msg_error="E-mail and Password are required to login in platform.",
        )

    if validate_authentication(email, password):
        return render_template("welcome.html")

    return render_template(
        "login.html", msg_error="E-mail and Password are wrong, please try again."
    )


@app.route("/page/<page>")
def go_to_page(page: str):
    return render_template(f"{page}.html")


@app.route("/signup", methods=["POST"])
def signup():
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
        
    if email and email in [user["email"] for user in users]:
        msg_errors.append("E-mail already in use, please choose another one")
    
    if password and confirm_password and password != confirm_password:
        msg_errors.append("Password and its confirmation are different")
        
    if msg_errors:
        return render_template("signup.html", msg_errors=msg_errors)
    
    return render_template("login.html", msg_success="User created successfully")
        