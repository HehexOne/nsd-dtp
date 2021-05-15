from funtools import wraps
from flask import Flask, session, request, render_template, redirect, url_for
import hashlib
from mysql.connector import connect
from keychain import *


app = Flask(__name__)
app.config['SECRET_KEY'] = "nsdh@ckT3chath0n"
connection = connect(host=db_host, port=db_port, user=db_user, password=db_password, db=db_name, ssl_ca=db_ca_cert)
db_cursor = connection.cursor()


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
                db_cursor.execute(
                    f"SELECT id, is_issuer CLIENT WHERE email='{email}' AND password='{password_hash}' LIMIT 1")
                client_user = db_cursor.fetchone()
                db_cursor.execute(
                    f"SELECT id FROM Operator WHERE email='{email}' AND password='{password_hash}' LIMIT 1")
                operator_user = db_cursor.fetchone()
                if client_user:
                    session['id'] = client_user[0]
                    session['account_type'] = "issuer" if client_user[1] == 0 else "client"
                    return redirect(f"/{session['account_type']}/")
                elif operator_user:
                    session['id'] = operator_user[0]
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
    app.run(host="0.0.0.0", port=9000)
