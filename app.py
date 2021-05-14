from flask import Flask, session, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
# login = LoginManager(app)
# db = SQLAlchemy(app)


@app.route("/authorization", methods=["GET", "POST"])
def authorization():
    error = None
    if request.method == "POST":
        if request.form.get("type") == "login_form":
            email = request.form.get("email", False)
            password = request.form.get("password", False)
            if all([email, password]):
                error = "Успешный вход!"
            else:
                error = "Заполние все поля!"
        else:
            error = "Ошибка запроса, повторите попытку."
    return render_template("login.html", error=error)


@app.route("/registration", methods=["GET", "POST"])
def registration():
    return render_template("registration.html", error=None)


if __name__ == '__main__':
    app.run()
