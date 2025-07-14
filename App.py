from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'minha_super_senha_123'

# Usuários e checklists em memória (temporário)
usuarios = {'user@example.com': '1234'}
checklists = {
    'user@example.com': [
        {'nome': 'Cadastrar cliente', 'passos': [
            {'texto': 'Abrir sistema', 'feito': False},
            {'texto': 'Clique em novo cliente', 'feito': False},
            {'texto': 'Preencher dados', 'feito': False},
            {'texto': 'Salvar', 'feito': False}
        ]}
    ]
}

STYLE = '''
<style>
  body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: url('/static/fundo.jpg') no-repeat center center fixed;
    background-size: cover;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
    margin: 0;
    padding-top: 40px;
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
  input[type=email], input[type=password], input[type=text] {
    width: 100%;
    padding: 10px 12px;
    margin: 8px 0 20px;
    border: 1px solid #ccc;
    border-radius: 5px;
    font-size: 15px;
  }
  input[type=submit], button {
    width: 100%;
    padding: 12px;
    background-color: #4a90e2;
    border: none;
    border-radius: 6px;
    color: white;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
  }
  input[type=submit]:hover, button:hover {
    background-color: #357ABD;
  }
  a {
    color: #4a90e2;
    text-decoration: none;
    font-weight: 600;
  }
  a:hover {
    text-decoration: underline;
  }
  ul {
    list-style-type: none;
    padding-left: 0;
  }
  li {
    margin-bottom: 12px;
    text-align: left;
  }
  form.inline {
    display: inline;
  }
  .passo-feito {
    text-decoration: line-through;
    color: gray;
  }
</style>
'''

def render_page(content):
    return f'''
    {STYLE}
    <div class="container">
      {content}
    </div>
    '''

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        if email in usuarios:
            return render_page('<h1>Cadastro</h1><p style="color:red;">Usuário já existe. Tente outro email.</p><a href="/cadastro">Voltar</a>')
        usuarios[email] = senha
        checklists[email] = []
        return redirect(url_for('login'))
    return render_page('''
      <h1>Cadastro</h1>
      <form method="post">
          <input type="email" name="email" placeholder="Email" required><br>
          <input type="password" name="senha" placeholder="Senha" required><br>
          <input type="submit" value="Cadastrar">
      </form>
      <br>
      <a href="/login">Já tenho conta, fazer login</a>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        if email in usuarios and usuarios[email] == senha:
            session['usuario'] = email
            return redirect(url_for('dashboard'))
        else:
            return render_page('<h1>Login</h1><p style="color:red;">Credenciais inválidas. Tente novamente.</p><a href="/login">Voltar</a>')
    return render_page('''
      <h1>Login</h1>
      <form method="post">
          <input type="email" name="email" placeholder="Email" required><br>
          <input type="password" name="senha" placeholder="Senha" required><br>
          <input type="submit" value="Entrar">
      </form>
      <br>
      <a href="/cadastro">Criar nova conta</a>
    ''')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    email = session['usuario']

    if request.method == 'POST':
        novo_nome = request.form.get('nome_checklist')
        if novo_nome:
            user_checklists = checklists.get(email, [])
            user_checklists.append({'nome': novo_nome, 'passos': []})
            checklists[email] = user_checklists

    user_checklists = checklists.get(email, [])
    lista_checklists = ''
    for i, c in enumerate(user_checklists):
        lista_checklists += f'''
            <li>
                <a href='/checklist/{i}'>{c['nome']}</a>
                <form method="post" action="/excluir_checklist/{i}" class="inline">
                    <button type="submit" onclick="return confirm('Excluir checklist {c['nome']}?')">Excluir</button>
                </form>
            </li>
        '''

    content = f'''
        <h1>Olá, {email}</h1>
        <h2>Seus checklists:</h2>
        <ul>{lista_checklists}</ul>

        <h3>Adicionar novo checklist</h3>
        <form method="post">
            Nome do checklist: <input type="text" name="nome_checklist" required>
            <input type="submit" value="Adicionar">
        </form>
        <br>
        <a href="/logout">Sair</a>
    '''
    return render_page(content)

@app.route('/checklist/<int:checklist_id>', methods=['GET', 'POST'])
def ver_checklist(checklist_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    email = session['usuario']
    user_checklists = checklists.get(email, [])

    if checklist_id >= len(user_checklists):
        return render_page('<p>Checklist não encontrado.</p><a href="/dashboard">Voltar</a>')

    checklist = user_checklists[checklist_id]

    if request.method == 'POST' and 'novo_passo' in request.form:
        novo_passo = request.form.get('novo_passo')
        if novo_passo:
            checklist['passos'].append({'texto': novo_passo, 'feito': False})

    passos_html = ''
    for i, passo in enumerate(checklist['passos']):
        classe_feito = 'passo-feito' if passo.get('feito', False) else ''
        marcado = 'X' if passo.get('feito', False) else ' '
        passos_html += f'''
        <li>
            <a href="/checklist/{checklist_id}/toggle/{i}" style="text-decoration:none; font-weight:bold;">[{marcado}]</a>
            <span class="{classe_feito}">{passo['texto']}</span>
            <form method="post" action="/checklist/{checklist_id}/delete/{i}" class="inline">
                <button type="submit" onclick="return confirm('Excluir passo?')">Excluir</button>
            </form>
        </li>
        '''

    content = f'''
        <h1>{checklist['nome']}</h1>
        <ul>{passos_html}</ul>

        <h3>Adicionar novo passo</h3>
        <form method="post">
            Passo: <input type="text" name="novo_passo" required>
            <input type="submit" value="Adicionar passo">
        </form>
        <br><a href="/dashboard">← Voltar</a>
    '''
    return render_page(content)

@app.route('/checklist/<int:checklist_id>/toggle/<int:passo_id>')
def toggle_passo(checklist_id, passo_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    email = session['usuario']
    user_checklists = checklists.get(email, [])

    if checklist_id >= len(user_checklists):
        return 'Checklist não encontrado.'

    checklist = user_checklists[checklist_id]

    if 0 <= passo_id < len(checklist['passos']):
        passo = checklist['passos'][passo_id]
        passo['feito'] = not passo.get('feito', False)

    return redirect(url_for('ver_checklist', checklist_id=checklist_id))

@app.route('/checklist/<int:checklist_id>/delete/<int:passo_id>', methods=['POST'])
def delete_passo(checklist_id, passo_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    email = session['usuario']
    user_checklists = checklists.get(email, [])

    if checklist_id >= len(user_checklists):
        return 'Checklist não encontrado.'

    checklist = user_checklists[checklist_id]

    if 0 <= passo_id < len(checklist['passos']):
        del checklist['passos'][passo_id]

    return redirect(url_for('ver_checklist', checklist_id=checklist_id))

@app.route('/excluir_checklist/<int:checklist_id>', methods=['POST'])
def excluir_checklist(checklist_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    email = session['usuario']
    user_checklists = checklists.get(email, [])

    if 0 <= checklist_id < len(user_checklists):
        del user_checklists[checklist_id]
        checklists[email] = user_checklists

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
    