from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta'  # Cambiar en producción

# Conexión a la base de datos
def conectar():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='dudulist'
    )

# Página de inicio (login)
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        identificador = request.form['usuario']  # Ahora se llama 'usuario' en el form
        contrasena = request.form['password']

        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario = %s OR email = %s",
            (identificador, identificador)
        )
        user = cursor.fetchone()
        cursor.close()
        conexion.close()

        if user and check_password_hash(user['password'], contrasena):
            session['usuario'] = user['usuario']
            session['usuario_id'] = user['id']  # Guardamos id para control
            return redirect(url_for('dashboard'))
        else:
            error = 'Usuario o contraseña incorrectos'
    return render_template('login.html', error=error)

# Registro de nuevos usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario = request.form['usuario']
        email = request.form['email']
        contrasena = request.form['password']
        fdn = request.form['fdn']

        hashed_pw = generate_password_hash(contrasena)

        conexion = conectar()
        cursor = conexion.cursor()
        # Validar si usuario o email existen antes de insertar
        cursor.execute("SELECT * FROM usuarios WHERE usuario=%s OR email=%s", (usuario, email))
        existe = cursor.fetchone()
        if existe:
            error = "El nombre de usuario o correo ya están registrados."
            cursor.close()
            conexion.close()
            return render_template('register.html', error=error)
        try:
            cursor.execute(
                "INSERT INTO usuarios (nombre, usuario, email, password, fdn) VALUES (%s, %s, %s, %s, %s)",
                (nombre, usuario, email, hashed_pw, fdn)
            )
            conexion.commit()
            return redirect(url_for('login'))
        except mysql.connector.Error as e:
            error = f"Error al registrar: {str(e)}"
        finally:
            cursor.close()
            conexion.close()
    return render_template('register.html', error=error)

# Panel principal
@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template('dashboard.html', usuarios=usuarios)

# Editar usuario (solo puede editar su propio perfil)
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    # Verificar que el id sea el del usuario logueado
    if id != session.get('usuario_id'):
        return "No tienes permiso para editar este usuario.", 403

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario = request.form['usuario']
        email = request.form['email']

        # Validar que no exista otro usuario con ese usuario o email (excluyendo este mismo id)
        cursor.execute("SELECT * FROM usuarios WHERE (usuario=%s OR email=%s) AND id != %s", (usuario, email, id))
        existe = cursor.fetchone()
        if existe:
            cursor.close()
            conexion.close()
            error = "El nombre de usuario o correo ya están en uso por otro usuario."
            # Recargar datos para el form
            conexion = conectar()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
            usuario_data = cursor.fetchone()
            cursor.close()
            conexion.close()
            return render_template('edit_user.html', usuario=usuario_data, error=error)

        cursor.execute("UPDATE usuarios SET nombre=%s, usuario=%s, email=%s WHERE id=%s",
                       (nombre, usuario, email, id))
        conexion.commit()
        cursor.close()
        conexion.close()
        # Actualizar sesión si cambió el usuario
        session['usuario'] = usuario
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    usuario_data = cursor.fetchone()
    cursor.close()
    conexion.close()
    return render_template('edit_user.html', usuario=usuario_data)

# Eliminar usuario (solo puede eliminar su propio perfil)
@app.route('/eliminar/<int:id>')
def eliminar(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if id != session.get('usuario_id'):
        return "No tienes permiso para eliminar este usuario.", 403

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    session.pop('usuario')
    session.pop('usuario_id')
    return redirect(url_for('login'))

# Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('usuario_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
