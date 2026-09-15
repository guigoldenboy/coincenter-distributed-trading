from kazoo.client import KazooClient
import requests

BASE_URL = "https://127.0.0.1:5000"
CA_CERT = "certs/ca.crt"

def secure_post(endpoint, data):
    return requests.post(f"{BASE_URL}{endpoint}", json=data, verify=CA_CERT)

def secure_get(endpoint, params=None):
    return requests.get(f"{BASE_URL}{endpoint}", params=params, verify=CA_CERT)

def manager_menu(user_id):

    while True:
        print("\n[Gestor] Menu:")
        print("1. Adicionar ativo")
        print("2. Ver todos os ativos disponíveis")
        print("3. Ver transações")
        print("4. Ver saldo e ativos pessoais")
        print("5. Comprar ativo")
        print("6. Vender ativo")
        print("7. Depositar fundos")
        print("8. Levantar fundos")
        print("9. Pesquisar utilizador")
        print("0. Sair")

        choice = input("Escolha: ")

        if choice == "0":
            break

        elif choice == "1":
            name = input("Nome do ativo: ")
            symbol = input("Símbolo: ")
            price = float(input("Preço: "))
            supply = int(input("Quantidade disponível: "))
            r = secure_post("/asset", {
                "symbol": symbol,
                "name": name,
                "price": price,
                "supply": supply
            })
            print(r.json())

        elif choice == "2":
            r = secure_get("/assetset")
            print(r.json())

        elif choice == "3":
            start = input("Início (YYYY-MM-DD): ")
            end = input("Fim (YYYY-MM-DD): ")
            r = secure_get("/transactions", {"start": start, "end": end})
            print(r.json())

        elif choice == "4":
            r = secure_get("/user", {"id": user_id})
            print(r.json())

        elif choice == "5":
            symbol = input("Símbolo do ativo: ")
            qty = float(input("Quantidade: "))
            r = secure_post("/buy", {"id": user_id, "symbol": symbol, "qty": qty})
            print(r.json())

        elif choice == "6":
            symbol = input("Símbolo do ativo: ")
            qty = float(input("Quantidade: "))
            r = secure_post("/sell", {"id": user_id, "symbol": symbol, "qty": qty})
            print(r.json())

        elif choice == "7":
            amount = float(input("Quantia a depositar: "))
            r = secure_post("/deposit", {"id": user_id, "amount": amount})
            print(r.json())

        elif choice == "8":
            amount = float(input("Quantia a levantar: "))
            r = secure_post("/withdraw", {"id": user_id, "amount": amount})
            print(r.json())
        
        elif choice == "9":
            other_id = input("Número do utilizador a pesquisar: ")
            if not other_id.isdigit():
                print("ID inválido.")
                continue
            other_id = int(other_id)
            r = secure_get("/user", {"id": other_id})
            if r.status_code == 404:
                print("Utilizador não encontrado.")
            else:
                print("Informação do utilizador:")
                print(f"ID: {other_id}")
                print(f"É gestor? {'Sim' if r.json()['is_manager'] else 'Não'}")
                print(f"Saldo: {r.json()['balance']}")
                print("Ativos:")
                for a in r.json()['assets']:
                    print(f" - {a['asset_symbol']}: {a['quantity']}")

        else:
            print("Opção inválida.")

def user_menu(user_id):
    
    while True:
        print("\n[Utilizador] Menu:")
        print("1. Ver saldo e ativos pesoais")
        print("2. Ver todos os ativos disponíveis")
        print("3. Comprar ativo")
        print("4. Vender ativo")
        print("5. Depositar fundos")
        print("6. Levantar fundos")
        print("0. Sair")

        choice = input("Escolha: ")

        if choice == "0":
            break

        elif choice == "1":
            r = secure_get("/user", {"id": user_id})
            print(r.json())

        elif choice == "2":
            r = secure_get("/assetset")
            print(r.json())

        elif choice == "3":
            symbol = input("Símbolo do ativo: ")
            qty = float(input("Quantidade: "))
            r = secure_post("/buy", {"id": user_id, "symbol": symbol, "qty": qty})
            print(r.json())

        elif choice == "4":
            symbol = input("Símbolo do ativo: ")
            qty = float(input("Quantidade: "))
            r = secure_post("/sell", {"id": user_id, "symbol": symbol, "qty": qty})
            print(r.json())

        elif choice == "5":
            amount = float(input("Quantia a depositar: "))
            r = secure_post("/deposit", {"id": user_id, "amount": amount})
            print(r.json())

        elif choice == "6":
            amount = float(input("Quantia a levantar: "))
            r = secure_post("/withdraw", {"id": user_id, "amount": amount})
            print(r.json())

        else:
            print("Opção inválida.")


def start_asset_watch(is_manager):
    if is_manager:
        return

    zk = KazooClient(hosts='127.0.0.1:2181')
    zk.start()
    known_assets = set()

    @zk.ChildrenWatch("/assets")
    def watch_assets(children):
        nonlocal known_assets
        current_assets = set(children)
        new_assets = current_assets - known_assets
        for asset in new_assets:
            print(f"[NOTIFICAÇÃO] Novo ativo: {asset}")
        known_assets = current_assets

def main():
    user_id = input("Insira o seu ID de utilizador: ")
    if not user_id.isdigit():
        print("ID inválido.")
        return

    user_id = int(user_id)

    # ver se user já existe, se não, pergunta se é manager ou não e cria conta
    r = secure_get("/user", {"id": user_id})

    if r.status_code == 404:
        print("Utilizador não existe.")
        tipo = input("É gestor? (s/n): ").strip().lower()
        is_manager = 1 if tipo == "s" else 0

        r = secure_post("/login", {"id": user_id, "is_manager": is_manager})
        print(r.json()["message"])

        # Confirmar criação
        r = secure_get("/user", {"id": user_id})
        if r.status_code != 200:
            print("Erro ao criar utilizador.")
            return

    else:
        is_manager = r.json().get("is_manager", 0)

    start_asset_watch(is_manager)

    if is_manager:
        manager_menu(user_id)
    else:
        user_menu(user_id)


if __name__ == "__main__":
    main()
