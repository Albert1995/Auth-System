from flask import Flask, render_template, request
from sassutils.wsgi import SassMiddleware

app = Flask(__name__)

app.wsgi_app = SassMiddleware(app.wsgi_app, {
    "auth": ('static/sass', 'static/css', '/static/css')
})

def validate_authentication(email, password):
    return email == "test.email@domain.com" and password == "123"

@app.route("/", methods=['GET', 'POST'])
def auth_page():
    if request.method == 'GET': 
        return render_template("login.html")
    
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        return render_template("login.html", msg_error="E-mail and Password are required to login in platform.")
    
    if validate_authentication(email, password):
        return render_template("welcome.html")
    
    return render_template("login.html", msg_error="E-mail and Password are wrong, please try again.")    
    
