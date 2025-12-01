from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "barbearia@2025"

# ==========================
# FUNÇÕES AUXILIARES
# ==========================
def criar_tabelas():
    with sqlite3.connect("barbearia.db") as conn:
        cursor = conn.cursor()

        # Tabela de clientes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
        """)

        # Tabela de agendamentos
        # Corrigido: Certificando que 'pagamento' está na declaração da tabela
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            servico TEXT NOT NULL,
            pagamento TEXT, -- Coluna adicionada para guardar a forma de pagamento
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
        """)
        
    print("Tabelas criadas com sucesso!")


def buscar_cliente(email):
    with sqlite3.connect("barbearia.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE email = ?", (email,))
        return cursor.fetchone()

# ==========================
# ROTAS
# ==========================
@app.route('/')
def home():
    if "user_id" in session:
        return redirect(url_for("cliente"))
    return render_template("login.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])
        
        try:
            with sqlite3.connect("barbearia.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO clientes (nome, email, senha) VALUES (?, ?, ?)",
                    (nome, email, senha)
                )
                conn.commit()
            return redirect("/")
        except sqlite3.IntegrityError:
            return "Email já cadastrado!"
    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        cliente = buscar_cliente(email)
        
        if cliente and check_password_hash(cliente[3], senha):
            session["user_id"] = cliente[0]
            session["user_nome"] = cliente[1]
            return redirect(url_for("cliente"))
        else:
            return "Email ou senha incorretos!"
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return f"Olá, {session['user_nome']}! Bem-vindo ao painel da barbearia."


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/agendar", methods=["GET", "POST"])
def agendar():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        data = request.form["data"]
        horario = request.form["horario"]
        servico = request.form["servico"]

        with sqlite3.connect("barbearia.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agendamentos (cliente_id, data, horario, servico)
                VALUES (?, ?, ?, ?)
            """, (session["user_id"], data, horario, servico))
            conn.commit()

        return "Agendamento realizado com sucesso!"

    return render_template("agendar.html")


@app.route("/finalizar", methods=["GET", "POST"])
def finalizar():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        # Lógica para processar o formulário POST (salvar agendamento)
        data = request.form["data-agendamento"]
        horario = request.form["hora-agendamento"]
        pagamento = request.form["tipo-pagamento"]
        servico = request.form["servico-nome"]
        
        try:
            with sqlite3.connect("barbearia.db") as conn:
                cursor = conn.cursor()
                
                # CORREÇÃO 1: Adicionado 'pagamento' à lista de colunas e valores
                cursor.execute("""
                    INSERT INTO agendamentos (cliente_id, data, horario, servico, pagamento)
                    VALUES (?, ?, ?, ?, ?)
                    """, (session["user_id"], data, horario, servico, pagamento))
                conn.commit()  
            
            # CORREÇÃO 2: Redirecionado após sucesso, melhor que retornar uma string
            return redirect(url_for("cliente")) 
        except Exception as e:
            # Tratamento básico de erro para depuração
            return f"Erro ao agendar: {e}", 500
    
    # Lógica para o método GET (mostrar a tela de finalização)
    # CORREÇÃO 3: Removida a indentação incorreta. 
    # Este bloco só será executado se request.method != "POST"
    servico_selecionado = request.args.get("servico")
    return render_template("finalizar.html", servico_url=servico_selecionado)


@app.route("/cliente")
def cliente():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("cliente_dashboard.html", nome=session["user_nome"])

# ==========================
# INICIALIZAÇÃO
# ==========================
if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)