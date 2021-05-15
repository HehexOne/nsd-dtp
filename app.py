from functools import wraps
from flask import Flask, session, request, render_template, redirect, url_for
import hashlib
from mysql.connector import connect
from keychain import *


app = Flask(__name__)
app.config['SECRET_KEY'] = "nsdh@ckT3chath0n"
connection = connect(host=db_host, port=db_port, user=db_user, password=db_password, ssl_ca=db_ca_cert)
db_cursor = connection.cursor()
db_cursor.execute("USE nsd;")


def get_client_by_id(id):
    db_cursor.execute(f"SELECT * FROM Client WHERE id={id} LIMIT 1;")
    client_data = db_cursor.fetchone()
    connection.commit()
    return {
        "id": client_data[0],
        "name": client_data[1],
        "inn": client_data[2],
        "email": client_data[3],
        "password_hash": client_data[4],
        "balance": client_data[5],
        "is_issuer": client_data[6],
        "is_approved": client_data[7],
        "is_banned": client_data[8]
    }


def get_operator_by_id(id):
    db_cursor.execute(f"SELECT * FROM Operator WHERE id={id} LIMIT 1;")
    operator_data = db_cursor.fetchone()
    connection.commit()
    return {
        "id": operator_data[0],
        "name": operator_data[1],
        "surname": operator_data[2],
        "email": operator_data[3],
        "password_hash": operator_data[4]
    }


def clientIssuer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        acc_type = session.get("account_type", None)
        if acc_type is None:
            return redirect(url_for("authorization"))
        elif acc_type == "client" or acc_type == "issuer":
            return f(*args, **kwargs)
        else:
            if acc_type == "issuer":
                acc_type = "client"
            return redirect(url_for(f'{acc_type}_index'))

    return decorated_function


def operator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        acc_type = session.get("account_type", None)
        if acc_type is None:
            return redirect(url_for("authorization"))
        elif acc_type != "operator":
            if acc_type == "issuer":
                acc_type = "client"
            return redirect(url_for(f'{acc_type}_index'))
        else:
            return f(*args, **kwargs)

    return decorated_function


def agent(f):
    @wraps(f)
    def deocrated_function(*args, **kwargs):
        acc_type = session.get("account_type", None)
        if acc_type is None:
            return redirect(url_for("authorization"))
        elif acc_type != "agent":
            if acc_type == "issuer":
                acc_type = "client"
            return redirect(url_for(f'{acc_type}_index'))
        else:
            return f(*args, **kwargs)
    return deocrated_function


@app.route("/", methods=["GET", "POST"])
@app.route("/authorization", methods=["GET", "POST"])
def authorization():
    if session.get("account_type") is not None:
        return redirect(url_for("client_index"))
    error = None
    if request.method == "POST":
        if request.form.get("type") == "login_form":
            email = request.form.get("email", False)
            password = request.form.get("password", False)
            if all([email, password]):
                password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
                db_cursor.execute(
                    f"SELECT id, is_issuer FROM Client WHERE email='{email}' AND password_hash='{password_hash}' LIMIT 1")
                client_user = db_cursor.fetchone()
                db_cursor.execute(
                    f"SELECT id FROM Operator WHERE email='{email}' AND password_hash='{password_hash}' LIMIT 1")
                operator_user = db_cursor.fetchone()
                db_cursor.execute(f"SELECT id FROM Agent WHERE email='{email}' AND password_hash='{password_hash}'")
                agent_user = db_cursor.fetchone()
                connection.commit()
                if client_user:
                    session['id'] = client_user[0]
                    session['account_type'] = "issuer" if client_user[1] else "client"
                    return redirect(url_for("client_index"))
                elif operator_user:
                    session['id'] = operator_user[0]
                    session['account_type'] = "operator"
                    return redirect(url_for("operator_index"))
                elif agent_user:
                    session['id'] = agent_user[0]
                    session['account_type'] = "agent"
                    return redirect(url_for("agent_index"))
                else:
                    error = "Пользователя с такими данными не найдено!"
            else:
                error = "Заполните все поля!"
        else:
            error = "Ошибка запроса, повторите попытку."
    return render_template("login.html", error=error)


@app.route("/registration", methods=["GET", "POST"])
def registration():
    if session.get("account_type") is not None:
        return redirect(url_for("client_index"))
    error = None
    if request.method == "POST":
        if request.form.get("type") == "registration_form":
            name = request.form.get("name", False)
            inn = request.form.get("inn", False)
            email = request.form.get("email", False)
            password = request.form.get("password", False)
            password_repeat = request.form.get("password_repeat", False)
            account_type = request.form.get("account_type", False)
            if all([name, inn, email, password, password_repeat, account_type]) and\
                    password == password_repeat and\
                    (len(inn) == 10 or len(inn) == 12):
                name = name.replace("'", "''")
                if account_type == "client":
                    account_type_id = 0
                elif account_type == "issuer":
                    account_type_id = 1
                else:
                    return render_template("registration.html", error="Неверный тип аккаунта!")
                password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
                query = f"INSERT INTO Client (name, inn, email, password_hash, is_issuer) VALUES " \
                        f"('{name}', '{inn}', '{email}', '{password_hash}', {account_type_id});"
                try:
                    db_cursor.execute(query)
                    connection.commit()
                    db_cursor.execute("SELECT LAST_INSERT_ID();")
                    session['id'] = db_cursor.fetchone()[0]
                    connection.commit()
                    session['account_type'] = account_type
                    return redirect(url_for(f"approval"))
                except Exception as e:
                    print(e)
                    error = "Ошибка создания пользователя, возможно, такой пользователь уже существует!"
            else:
                error = "Проверьте правильность введённых данных!"
    return render_template("registration.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("authorization"))


@app.route("/client/")
@clientIssuer
def client_index():
    client_data = get_client_by_id(session.get("id"))
    if not client_data['is_approved']:
        return redirect(url_for("approval"))
    return render_template("client_index.html", account_data=get_client_by_id(session['id']))


@app.route("/agent/")
@agent
def agent_index():
    return render_template("agent_index.html")


@app.route("/operator/")
@operator
def operator_index():
    return render_template("operator_index.html")


@app.route("/approval")
@clientIssuer
def approval():
    client_data = get_client_by_id(session.get("id"))
    if client_data["is_approved"]:
        return redirect(url_for("client_index"))
    return render_template("approval_sent.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=9000)
