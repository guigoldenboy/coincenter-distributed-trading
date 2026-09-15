import ssl
from flask import Flask, request, jsonify
from kazoo.client import KazooClient
from coincenter_data import *

zk = KazooClient(hosts='127.0.0.1:2181')
zk.start()
zk.ensure_path("/assets")

app = Flask(__name__)

@app.route("/login", methods=["POST"])
def login_route():
    data = request.get_json()
    user_id = data.get("id")
    is_manager = data.get("is_manager", 0)
    login(user_id, is_manager)
    return jsonify({"message": "utilizador registado ou já existente"})

@app.route("/asset", methods=["POST"])
def add_asset_route():
    data = request.get_json()
    add_asset(data["symbol"], data["name"], data["price"], data["supply"])


    # notificação do zookeeper para novos ativos
    path = f"/assets/{data['symbol']}"
    if zk.exists(path):
        zk.set(path, b"updated")
    else:
        zk.create(path, b"new")

    return jsonify({"message": "ativo adicionado com sucesso"})

@app.route("/asset", methods=["GET"])
def get_asset_route():
    symbol = request.args.get("symbol")
    asset = get_asset(symbol)
    if asset:
        return jsonify(asset)
    return jsonify({"error": "ativo não encontrado"}), 404

@app.route("/assetset", methods=["GET"])
def list_all_assets():
    assets = list_assets()
    return jsonify(assets)

@app.route("/user", methods=["GET"])
def user_balance_route():
    user_id = int(request.args.get("id"))
    conn = get_db()
    user = conn.execute("SELECT * FROM Clients WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return jsonify({"error": "Utilizador não encontrado"}), 404
    info = get_user_balance(user_id)
    info["is_manager"] = user["is_manager"]
    return jsonify(info)


@app.route("/buy", methods=["POST"])
def buy_route():
    data = request.get_json()
    success = buy_asset(data["id"], data["symbol"], float(data["qty"]))
    return jsonify({"success": success})

@app.route("/sell", methods=["POST"])
def sell_route():
    data = request.get_json()
    success = sell_asset(data["id"], data["symbol"], float(data["qty"]))
    return jsonify({"success": success})

@app.route("/deposit", methods=["POST"])
def deposit_route():
    data = request.get_json()
    success = deposit(data["id"], float(data["amount"]))
    return jsonify({"success": success})

@app.route("/withdraw", methods=["POST"])
def withdraw_route():
    data = request.get_json()
    success = withdraw(data["id"], float(data["amount"]))
    return jsonify({"success": success})

@app.route("/transactions", methods=["GET"])
def transactions_route():
    start = request.args.get("start")
    end = request.args.get("end")
    txs = get_transactions(start, end)
    return jsonify(txs)

if __name__ == "__main__":
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="certs/server.crt", keyfile="certs/server.key")
    app.run(debug=True, ssl_context=context)