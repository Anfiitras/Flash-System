from flask import Flask, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

app = Flask(__name__)
app.secret_key = 'minha_super_senha_123'

JSON_FILE = 'checklists.json'

# Funções de salvar/carregar
def carregar_dados():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            return json.load(f)
    return {'usuarios': {}, 'checklists': {}}

def salvar_dados(data):
    with open(JSON_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Dados globais
dados = carregar_dados()
usuarios = dados.get('usuarios', {})
checklists = dados.get('checklists', {})

STYLE = '''
<style>
  body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: url('/static/fundo.jpg') no-repeat center center fixed;
    background-size: cover;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
  }
  .container {
    background: white;
    padding: 30px 40px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgb(0 0 0 / 0.1);
    width: 320px;
    text-align: center;
  }
  h1 {
    font-weight: 700;
    margin-bottom: 24px;
    color: #333;
    font-size: 28px;
  }
  input, button {
    width: 100%;
    padding: 10px 12px;
    margin: 8px 0;
    border-radius: 5px;
    font-size: 15px;
  }
  input[type=submit], button {
    background-color: #4a90e2;
    border: none;
    color: white;
    font-weight: bold;
    cursor: pointer;
  }
  input[type=submit]:hover, button:hover {
    background-color: #357ABD;
  }
</style>
'''

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        if email in usuarios:
            return 'Usuário já existe. Tente outro email.'
        usuarios[email] = {
            'nome': nome,
            'senha': generate_password_hash(senha)
        }
        checklists[email] = []
        salvar_dados({'usuarios': usuarios, 'checklists': checklists})
        return redirect(url_for('login'))
    return f'''
        {STYLE}
        <div class="container">
          <h1>Cadastro</h1>
          <form method="post">
              <input type="text" name="nome" placeholder="Nome de Usuário" required><br>
              <input type="email" name="email" placeholder="Email" required><br>
              <input type="password" name="senha" placeholder="Senha" required><br>
              <input type="submit" value="Cadastrar">
          </form>
          <br>
          <a href="/login">Já tenho conta</a>
        </div>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = usuarios.get(email)
        if user and check_password_hash(user['senha'], senha):
            session['usuario'] = email
            return redirect(url_for('dashboard'))
        return 'Credenciais inválidas.'
    return f'''
        {STYLE}
        <div class="container">
          <h1>Login</h1>
          <form method="post">
              <input type="email" name="email" placeholder="Email" required><br>
              <input type="password" name="senha" placeholder="Senha" required><br>
              <input type="submit" value="Entrar">
          </form>
          <br>
          <a href="/cadastro">Criar nova conta</a>
        </div>
    '''

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    email = session['usuario']
    nome_usuario = usuarios[email]['nome']

    if request.method == 'POST':
        nome_cl = request.form.get('nome_checklist')
        if nome_cl:
            checklists[email].append({'nome': nome_cl, 'passos': []})
            salvar_dados({'usuarios': usuarios, 'checklists': checklists})

    html = f"<h1>Bem-vindo, {nome_usuario}</h1><ul>"
    for i, c in enumerate(checklists[email]):
        html += f"<li><a href='/checklist/{i}'>{c['nome']}</a> " \
                f"<form method='post' action='/excluir_checklist/{i}' style='display:inline;'>" \
                f"<button type='submit'>🗑️</button></form></li>"
    html += "</ul><form method='post'>Novo checklist: " \
            "<input type='text' name='nome_checklist' required><input type='submit' value='Adicionar'></form>"
    html += "<br><a href='/logout'>Sair</a>"
    return html

@app.route('/checklist/<int:cid>', methods=['GET', 'POST'])
def ver_checklist(cid):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    email = session['usuario']
    cl = checklists[email][cid]

    if request.method == 'POST':
        novo = request.form.get('novo_passo')
        if novo:
            cl['passos'].append({'texto': novo, 'feito': False})
            salvar_dados({'usuarios': usuarios, 'checklists': checklists})

    html = f"<h1>{cl['nome']}</h1><ul>"
    for i, passo in enumerate(cl['passos']):
        marcado = 'X' if passo['feito'] else ' '
        html += f"<li><a href='/checklist/{cid}/toggle/{i}'>[{marcado}]</a> {passo['texto']}" \
                f"<form method='post' action='/checklist/{cid}/delete/{i}' style='display:inline;'>" \
                f"<button type='submit'>🗑️</button></form></li>"
    html += f"</ul><form method='post'>Novo passo: " \
            "<input type='text' name='novo_passo' required><input type='submit' value='Adicionar'></form>" \
            "<br><a href='/dashboard'>← Voltar</a>"
    return html

@app.route('/checklist/<int:cid>/toggle/<int:pid>')
def toggle(cid, pid):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    email = session['usuario']
    passo = checklists[email][cid]['passos'][pid]
    passo['feito'] = not passo['feito']
    salvar_dados({'usuarios': usuarios, 'checklists': checklists})
    return redirect(url_for('ver_checklist', cid=cid))

@app.route('/checklist/<int:cid>/delete/<int:pid>', methods=['POST'])
def del_passo(cid, pid):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    email = session['usuario']
    del checklists[email][cid]['passos'][pid]
    salvar_dados({'usuarios': usuarios, 'checklists': checklists})
    return redirect(url_for('ver_checklist', cid=cid))

@app.route('/excluir_checklist/<int:cid>', methods=['POST'])
def excluir_checklist(cid):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    email = session['usuario']
    del checklists[email][cid]
    salvar_dados({'usuarios': usuarios, 'checklists': checklists})
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
