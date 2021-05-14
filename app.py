from functools import wraps

from flask import Flask, session, request, render_template, redirect, url_for
import hashlib
from mysql.connector import connect
from keychain import *

app = Flask(__name__)
app.config['SECRET_KEY'] = "nsdh@ckT3chath0n"
connection = connect(host=db_host, port=db_port, user=db_user, password=db_password, db=db_name)
db_cursor = connection.cursor()


# TODO MySQL
# class Client(db.Model):
#     id = db.Column(db.Integer(), autoincrement=True, primary_key=True)
#     name = db.Column(db.String(256), nullable=True)
#     inn = db.Column(db.String(12), nullable=False, unique=True)
#     email = db.Column(db.String(128), nullable=False, unique=True)
#     password_hash = db.Column(db.String(256), nullable=False)
#     balance = db.Column(db.Float(), default=0.0, nullable=False)
#     is_issuer = db.Column(db.Boolean, default=False, nullable=False)
#     assets = db.relationship('DigitalAsset',
#                              backref=db.backref('Owner',
#                                                 lazy=True))
#     assets_created = db.relationship('DigitalAssets',
#                                      backref=db.backref('Creator',
#                                                         lazy=True))
#
#
# class DigitalAsset(db.Model):
#     id = db.Column(db.Integer(), autoincrement=True, primary_key=True)
#     name = db.Column(db.String(128), nullable=False)
#     balance = db.Column(db.Float, nullable=False)
#     token = db.Column(db.String(512), nullable=True)
#     is_approved = db.Column(db.Boolean, default=False, nullable=False)
#
#
# class Operator(db.Model):
#     id = db.Column(db.Integer(), autoincrement=True, primary_key=True)
#     name = db.Column(db.String(128), nullable=False)
#     surname = db.Column(db.String(128), nullable=False)
#     email = db.Column(db.String(128), unique=True, nullable=False)
#     password_hash = db.Column(db.String(256), nullable=False)


def clientIssuer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        acc_type = session.get("account_type", None)
        if acc_type is None:
            return redirect(url_for("/authorization"))
        elif acc_type == "client" or acc_type == "issuer":
            return f(*args, **kwargs)
        else:
            return redirect(url_for(f'/operator', next=request.url))
    return decorated_function


def operator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        acc_type = session.get("account_type", None)
        if acc_type is None:
            return redirect(url_for("/authorization"))
        elif acc_type != "operator":
            return redirect(url_for(f'/{session.get("account_type")}', next=request.url))
        else:
            return f(*args, **kwargs)
    return decorated_function


@app.route("/authorization", methods=["GET", "POST"])
def authorization():
    error = None
    if request.method == "POST":
        if request.form.get("type") == "login_form":
            email = request.form.get("email", False)
            password = request.form.get("password", False)
            if all([email, password]):
                password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
                # TODO MySQL
                # client_user = Client.query.filter_by(email=email, password_hash=password_hash).first()
                # operator_user = Operator.query.filter_by(email=email, password_hash=password_hash).first()
                if client_user:
                    session['id'] = client_user.id
                    session['account_type'] = "issuer" if client_user.account_type == 0 else "client"
                    return redirect(f"/{session['account_type']}/")
                elif operator_user:
                    session['id'] = operator_user.id
                    session['account_type'] = "operator"
                    return redirect("/operator/")
                else:
                    error = "Пользователя с такими данными не найдено!"
            else:
                error = "Заполние все поля!"
        else:
            error = "Ошибка запроса, повторите попытку."
    return render_template("login.html", error=error)


@app.route("/registration", methods=["GET", "POST"])
def registration():
    return render_template("registration.html", error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("/authorization"))


if __name__ == '__main__':
    db.create_all()
    app.run(host="0.0.0.0", port=9000)
