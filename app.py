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
    database="dudulist"
)

# Página principal (login)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['usuario']
        password = request.form['contrasena']

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['usuario'] = user['email']  # También puedes usar user['id'] o user['email']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Credenciales incorrectas")

    return render_template('login.html')


# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        fdn = request.form['fdn']  # Espera un formato de fecha válido: 'YYYY-MM-DD'

        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (nombre, email, password, fdn) VALUES (%s, %s, %s, %s)",
                (nombre, email, password, fdn)
            )
            db.commit()
            return redirect(url_for('login'))
        except Exception as e:
            print(e)  # Útil para depurar
            return render_template('register.html', error="El nombre o el correo ya están registrados")

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
