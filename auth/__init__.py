from flask import Flask, render_template
from sassutils.wsgi import SassMiddleware

app = Flask(__name__)

app.wsgi_app = SassMiddleware(app.wsgi_app, {
    "auth": ('static/sass', 'static/css', '/static/css')
})

@app.route("/")
def home():
    return render_template("index.html")
