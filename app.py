from datetime import datetime
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


def ban_client(client_id):
    query = f"UPDATE nsd.Client SET is_banned=TRUE WHERE id={client_id}"
    db_cursor.execute(query)
    connection.commit()


def approve_client(client_id):
    query = f"UPDATE nsd.Client SET is_approved=TRUE WHERE id={client_id}"
    db_cursor.execute(query)
    connection.commit()


def unban_client(client_id):
    query = f"UPDATE nsd.Client SET is_banned=FALSE WHERE id={client_id}"
    db_cursor.execute(query)
    connection.commit()


def ban_asset(asset_id):
    query = f"UPDATE nsd.DigitalAsset SET is_banned=TRUE WHERE id={asset_id}"
    db_cursor.execute(query)
    connection.commit()


def approve_asset(asset_id):
    query = f"UPDATE nsd.DigitalAsset SET is_approved=TRUE WHERE id={asset_id}"
    db_cursor.execute(query)
    connection.commit()
    asset = get_digital_asset_by_id(asset_id)
    owner = get_client_by_id(asset['owner_id'])
    query = f"UPDATE nsd.Client SET balance={float(owner['balance']) - float(asset['balance'])} WHERE id={owner['id']}"
    db_cursor.execute(query)
    connection.commit()


def unban_asset(asset_id):
    query = f"UPDATE nsd.DigitalAsset SET is_banned=FALSE WHERE id={asset_id}"
    db_cursor.execute(query)
    connection.commit()


def get_client_for_approval(operator_id):
    query = f"SELECT * FROM nsd.Client WHERE is_approved=FALSE " \
            f"AND is_banned=FALSE AND who_approve={operator_id} LIMIT 1"
    db_cursor.execute(query)
    result = db_cursor.fetchone()
    connection.commit()
    if result:
        return {
            "id": result[0],
            "name": result[1],
            "inn": result[2],
            "address": result[3],
            "email": result[4],
            "password_hash": result[5],
            "balance": result[6],
            "is_issuer": result[7],
            "is_approved": result[8],
            "is_banned": result[9],
            "who_approve": result[10]
        }
    else:
        return None


def get_digital_asset_for_approval(operator_id):
    query = f"SELECT * FROM nsd.DigitalAsset WHERE is_approved=FALSE " \
            f"AND is_banned=FALSE AND who_approve={operator_id} LIMIT 1"
    db_cursor.execute(query)
    result = db_cursor.fetchone()
    connection.commit()
    if result:
        return {
            "id": result[0],
            "name": result[1],
            "who_approve": result[2],
            "balance": result[3],
            "percent": result[4],
            "quantity": result[5],
            "due_to": result[6],
            "is_approved": result[7],
            "is_banned": result[8],
            "owner_id": result[9]
        }
    else:
        return None


def get_client_by_id(ident):
    db_cursor.execute(f"SELECT * FROM nsd.Client WHERE id={ident} LIMIT 1;")
    client_data = db_cursor.fetchone()
    connection.commit()
    if client_data:
        return {
            "id": client_data[0],
            "name": client_data[1],
            "inn": client_data[2],
            "address": client_data[3],
            "email": client_data[4],
            "password_hash": client_data[5],
            "balance": client_data[6],
            "is_issuer": client_data[7],
            "is_approved": client_data[8],
            "is_banned": client_data[9],
            "who_approve": client_data[10]
        }

    else:
        return None


def get_operator_by_id(ident):
    db_cursor.execute(f"SELECT * FROM nsd.Operator WHERE id={ident} LIMIT 1;")
    operator_data = db_cursor.fetchone()
    connection.commit()
    if operator_data:
        return {
            "id": operator_data[0],
            "name": operator_data[1],
            "email": operator_data[2],
            "password_hash": operator_data[3],
            "is_banned": operator_data[4]
        }
    else:
        return None


def get_digital_asset_by_id(ident):
    query = f"SELECT * FROM nsd.DigitalAsset WHERE id={ident} LIMIT 1;"
    db_cursor.execute(query)
    asset_data = db_cursor.fetchone()
    connection.commit()
    if asset_data:
        return {
            "id": asset_data[0],
            "name": asset_data[1],
            "who_approve": asset_data[2],
            "balance": asset_data[3],
            "percent": asset_data[4],
            "quantity": asset_data[5],
            "due_to": asset_data[6],
            "is_approved": asset_data[7],
            "is_banned": asset_data[8],
            "owner_id": asset_data[9]
        }
    else:
        return None


def get_asset_token_by_id(ident):
    query = f"SELECT * FROM nsd.DigitalAssetToken WHERE id={ident} LIMIT 1"
    db_cursor.execute(query)
    result = db_cursor.fetchone()
    connection.commit()
    if result:
        return {
            "id": result[0],
            "token": result[1],
            "holder_id": result[2],
            "parent_asset": result[3]
        }
    else:
        return None


def get_asset_token_by_token(token):
    query = f"SELECT * FROM nsd.DigitalAssetToken WHERE token='{token}' LIMIT 1"
    db_cursor.execute(query)
    result = db_cursor.fetchone()
    connection.commit()
    if result:
        return {
            "id": result[0],
            "token": result[1],
            "holder_id": result[2],
            "parent_asset": result[3]
        }
    else:
        return None


def clientIssuer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        acc_type = session.get("account_type", None)
        if acc_type is None:
            return redirect(url_for("authorization"))
        elif acc_type == "client" or acc_type == "issuer":
            if get_client_by_id(session.get("id"))['is_banned']:
                return redirect(url_for("banned"))
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
            if get_operator_by_id(session.get("id"))['is_banned']:
                return redirect(url_for("banned"))
            return f(*args, **kwargs)

    return decorated_function


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
                    f"SELECT id, is_issuer FROM nsd.Client WHERE email='{email}' AND password_hash='{password_hash}' LIMIT 1")
                client_user = db_cursor.fetchone()
                db_cursor.execute(
                    f"SELECT id FROM nsd.Operator WHERE email='{email}' AND password_hash='{password_hash}' LIMIT 1")
                operator_user = db_cursor.fetchone()
                connection.commit()
                if client_user:
                    session['id'] = client_user[0]
                    session['account_type'] = "issuer" if client_user[1] else "client"
                    return redirect(url_for("client_index"))
                elif operator_user:
                    session['id'] = operator_user[0]
                    session['account_type'] = "operator"
                    return redirect(url_for("operator_index"))
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
            address = request.form.get("address", False)
            if all([name, inn, email, password, password_repeat, account_type, address]) and \
                    password == password_repeat and \
                    (len(inn) == 10 or len(inn) == 12):
                name = name.replace("'", "''")
                address = address.replace("'", "''")
                if account_type == "client":
                    account_type_id = 0
                elif account_type == "issuer":
                    account_type_id = 1
                else:
                    return render_template("registration.html", error="Неверный тип аккаунта!")
                password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
                query = f"INSERT INTO nsd.Client (name, inn, email, password_hash, is_issuer," \
                        f" who_approve, address) VALUES " \
                        f"('{name}', '{inn}', '{email}', '{password_hash}', {account_type_id}," \
                        f" (SELECT id FROM nsd.Operator WHERE is_banned=FALSE ORDER BY RAND() LIMIT 1), '{address}');"
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


@app.route("/operator/")
@operator
def operator_index():
    operator_data = get_operator_by_id(session.get("id"))
    return render_template("operator_index.html", name=operator_data['name'])


@app.route("/operator/clients", methods=["GET", "POST"])
@operator
def operator_clients():
    if request.method == "POST":
        client_id = request.form.get("client_id", None)
        solution = request.form.get("solution", None)
        if solution and client_id:
            client_data = get_client_by_id(client_id)
            if client_data['who_approve'] == session.get("id"):
                if solution == "approve":
                    approve_client(client_id)
                    # TODO Открытие счёта в Blockchain
                else:
                    ban_client(client_id)
    client = get_client_for_approval(session.get("id"))
    return render_template("operator_clients.html", client=client)


@app.route("/operator/assets", methods=["GET", "POST"])
@operator
def operator_assets():
    if request.method == "POST":
        asset_id = request.form.get("asset_id", None)
        solution = request.form.get("solution", None)
        if solution and asset_id:
            client_data = get_digital_asset_by_id(asset_id)
            if client_data['who_approve'] == session.get("id"):
                if solution == "approve":
                    approve_asset(asset_id)
                    asset_data = get_digital_asset_by_id(asset_id)
                    for n in range(int(asset_data['quantity'])):
                        token = hashlib.sha512((asset_data['name'] + str(n)).encode("utf-8")).hexdigest()
                        query = f"INSERT INTO nsd.DigitalAssetToken (token, holder_id, parent_asset) VALUES " \
                                f"('{token}', {asset_data['owner_id']}, {asset_data['id']})"
                        db_cursor.execute(query)
                        connection.commit()
                else:
                    ban_asset(asset_id)
    asset = get_digital_asset_for_approval(session.get("id"))
    if asset:
        asset['owner'] = get_client_by_id(asset["owner_id"])['name']
    return render_template("operator_assets.html", asset=asset)


@app.route("/operator/clients-all")
@operator
def operator_clients_all():
    query = "SELECT id FROM nsd.Client"
    db_cursor.execute(query)
    result = db_cursor.fetchall()
    connection.commit()
    clients = []
    for client in result:
        clients.append(get_client_by_id(client[0]))
    return render_template("operator_clients_all.html", clients=clients)


@app.route("/operator/assets-all")
@operator
def operator_assets_all():
    query = "SELECT id FROM nsd.DigitalAsset"
    db_cursor.execute(query)
    result = db_cursor.fetchall()
    connection.commit()
    assets = []
    for asset in result:
        assets.append(get_digital_asset_by_id(asset[0]))
    return render_template("operator_assets_all.html", assets=assets)


@app.route("/operator/ban-client")
@operator
def operator_ban_user():
    client_id = request.args.get("client_id")
    next_url = request.args.get("next")
    if client_id:
        ban_client(client_id)
    if next_url:
        return redirect(next_url)
    return redirect(url_for("operator_clients_all"))


@app.route("/operator/ban-asset")
@operator
def operator_ban_asset():
    asset_id = request.args.get("asset_id")
    next_url = request.args.get("next")
    if asset_id:
        ban_asset(asset_id)
    if next_url:
        return redirect(next_url)
    return redirect(url_for("operator_assets_all"))


@app.route("/operator/unban-client")
@operator
def operator_unban_client():
    client_id = request.args.get("client_id")
    next_url = request.args.get("next")
    if client_id:
        unban_client(client_id)
    if next_url:
        return redirect(next_url)
    return redirect(url_for("operator_clients_all"))


@app.route("/operator/unban-asset")
@operator
def operator_unban_asset():
    asset_id = request.args.get("asset_id")
    next_url = request.args.get("next")
    if asset_id:
        unban_asset(asset_id)
    if next_url:
        return redirect(next_url)
    return redirect(url_for("operator_assets_all"))


@app.route("/operator/approve-client")
@operator
def operator_approve_client():
    client_id = request.args.get("client_id")
    next_url = request.args.get("next")
    if client_id:
        approve_client(client_id)
    if next_url:
        return redirect(next_url)
    return redirect(url_for("operator_clients_all"))


@app.route("/operator/approve-asset")
@operator
def operator_approve_asset():
    asset_id = request.args.get("asset_id")
    next_url = request.args.get("next")
    if asset_id:
        approve_asset(asset_id)
    if next_url:
        return redirect(next_url)
    return redirect(url_for("operator_assets_all"))


@app.route("/client/payment", methods=["GET", "POST"])
@clientIssuer
def client_payment():
    if request.method == "POST":
        amount = request.form.get("amount")
        if amount:
            client_data = get_client_by_id(session.get("id"))
            amount = float(amount)
            query = f"UPDATE nsd.Client SET balance={client_data['balance'] + amount} WHERE id={client_data['id']}"
            db_cursor.execute(query)
            connection.commit()
            return redirect(url_for("client_index"))
    return render_template("clients_payment.html")


@app.route("/client/assets-my")
@clientIssuer
def client_assets_my():
    account_data = get_client_by_id(session.get("id"))
    mao = None
    if account_data['is_issuer']:
        query = f"SELECT id FROM nsd.DigitalAsset WHERE owner_id={account_data['id']}"
        db_cursor.execute(query)
        result = db_cursor.fetchall()
        connection.commit()
        mao = []
        for asset in result:
            mao.append(get_digital_asset_by_id(asset[0]))
        query = f"SELECT nsd.DigitalAssetToken.id FROM nsd.DigitalAssetToken INNER JOIN nsd.DigitalAsset" \
                f" ON DigitalAssetToken.parent_asset = DigitalAsset.id WHERE owner_id={account_data['id']} " \
                f"AND holder_id={account_data['id']}"
    else:
        query = f"SELECT id FROM nsd.DigitalAssetToken WHERE holder_id={account_data['id']}"
    db_cursor.execute(query)
    result = db_cursor.fetchall()
    connection.commit()
    assets = []
    for asset in result:
        asset_token = get_asset_token_by_id(asset[0])
        asset_obj = get_digital_asset_by_id(asset_token['parent_asset'])
        parent = get_client_by_id(asset_obj['owner_id'])['name']
        asset_obj.update(asset_token)
        asset_obj['parent'] = parent
        assets.append(asset_obj)
    return render_template("client_assets_my.html", account_data=account_data, assets=assets, mao=mao)


@app.route("/client/assets-create", methods=["GET", "POST"])
@clientIssuer
def client_assets_create():
    client_data = get_client_by_id(session.get("id"))
    if not client_data['is_issuer']:
        return redirect(url_for("client_index"))
    if request.method == "POST":
        name = request.form.get("name", False)
        balance = request.form.get("balance", False)
        quantity = request.form.get("quantity", False)
        percent = request.form.get("percent", False)
        due_to = request.form.get("due_to", False)
        if all([name, balance, quantity, percent, due_to]):
            name = name.replace("'", "''")
            due_to = datetime.strptime(due_to, '%Y-%m-%dT%H:%M')
            query = f"INSERT INTO nsd.DigitalAsset (name, who_approve, balance, percent, quantity, due_to, owner_id)" \
                    f" VALUES ('{name}', (SELECT id FROM nsd.Operator WHERE is_banned=FALSE ORDER BY RAND() LIMIT 1)," \
                    f"{balance}, {percent}, {quantity}, '{due_to}', {client_data['id']})"
            db_cursor.execute(query)
            connection.commit()
            return redirect(url_for("client_assets_my"))
    return render_template("client_assets_create.html", client_data=client_data)


# /client/transfer?asset_token={{ asset['token'] }}
@app.route("/client/transfer", methods=["GET", "POST"])
@clientIssuer
def client_transfer():
    asset_token = request.args.get("asset_token", False)
    if not asset_token:
        return redirect(url_for("client_index"))
    if request.method == "POST":
        to_client_id = request.form.get("to_client", False)
        if to_client_id:
            token = get_asset_token_by_token(asset_token)
            parent = get_digital_asset_by_id(token['parent_asset'])
            from_client = get_client_by_id(session.get("id"))
            to_client = get_client_by_id(to_client_id)
            if token['holder_id'] == from_client['id'] and to_client and parent['is_approved']\
                    and not parent['is_banned'] \
                    and not from_client['is_banned'] and not to_client['is_banned'] \
                    and from_client['is_approved'] and to_client['is_approved']:
                query = f"UPDATE nsd.DigitalAssetToken SET holder_id={to_client['id']} WHERE token='{asset_token}'"
                db_cursor.execute(query)
                connection.commit()
                return redirect(url_for("client_assets_my"))
    return render_template("client_assets_transfer.html")


@app.route("/approval")
@clientIssuer
def approval():
    client_data = get_client_by_id(session.get("id"))
    if client_data["is_approved"]:
        return redirect(url_for("client_index"))
    return render_template("approval_sent.html")


@app.route("/banned")
def banned():
    user_id = session.get("id", None)
    if user_id:
        acc_type = session.get("account_type")
        if acc_type == "client" or acc_type == "issuer":
            user_data = get_client_by_id(session.get("id"))
        else:
            user_data = get_operator_by_id(session.get("id"))
        if user_data["is_banned"]:
            return render_template("banned.html")
    return redirect(url_for("authorization"))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=9000)
