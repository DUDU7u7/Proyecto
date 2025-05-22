from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'
bcrypt = Bcrypt(app)

# Conexión con la base de datos
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="flask_app"
)

# Página principal (login)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user['contrasena'], contrasena):
            session['usuario'] = user['usuario']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Credenciales incorrectas")

    return render_template('login.html')

# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario = request.form['usuario']
        correo = request.form['correo']
        contrasena = bcrypt.generate_password_hash(request.form['contrasena']).decode('utf-8')

        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nombre, usuario, correo, contrasena) VALUES (%s, %s, %s, %s)",
                           (nombre, usuario, correo, contrasena))
            db.commit()
            return redirect(url_for('login'))
        except:
            return render_template('register.html', error="Usuario ya existe")

    return render_template('register.html')

# Página principal después de login
@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    return render_template('dashboard.html', usuarios=usuarios)

# Editar usuario
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        cursor.execute("UPDATE usuarios SET nombre = %s, correo = %s WHERE id = %s", (nombre, correo, id))
        db.commit()
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    usuario = cursor.fetchone()
    return render_template('edit_user.html', usuario=usuario)

# Eliminar usuario
@app.route('/eliminar/<int:id>')
def eliminar(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    db.commit()
    return redirect(url_for('dashboard'))

# Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
