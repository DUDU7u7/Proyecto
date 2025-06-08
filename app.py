from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'clave_secreta' 

#CONEXIÓN A BD
def conectar():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='dudulist'
    )

#INGRESO DE USUARIO
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

#REGISTRO DE USUARIO
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

#EDITAR USUARIO
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

#ELIMINAR USUARIO
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

#REGISTRO DE TAREA
@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    error = None
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT id, nombre FROM categorias")
    categorias = cursor.fetchall()

    cursor.execute("SELECT id, nombre FROM prioridades")
    prioridades = cursor.fetchall()

    cursor.execute("SELECT id, nombre FROM estados")
    estados = cursor.fetchall()

    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_limite = request.form['fecha_limite']
        categoria_id = request.form['categoria']
        prioridad_id = request.form['prioridad']
        estado_id = 1

        usuario_id = session.get('usuario_id')
        if not usuario_id:
            error = "Debes iniciar sesión para agregar una tarea."
        else:
            try:
                cursor.execute("""
                    INSERT INTO tareas 
                    (usuario_id, categoria_id, prioridad_id, estado_id, titulo, descripcion, fecha_limite)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (usuario_id, categoria_id, prioridad_id, estado_id, titulo, descripcion, fecha_limite))
                conexion.commit()
                return redirect(url_for('dashboard'))  # Redirige a la lista de tareas, por ejemplo
            except mysql.connector.Error as e:
                error = f"Error al registrar tarea: {str(e)}"
    cursor.close()
    conexion.close()
    return render_template('add_task.html', error=error,
                           categorias=categorias, prioridades=prioridades, estados=estados)

#MOSTRAR TAREA
@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario_id = session.get('usuario_id')
    filtro = request.args.get('filtro', 'todas') 
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT t.id, t.titulo, t.descripcion, t.fecha_limite,
               c.nombre AS categoria,
               p.nombre AS prioridad,
               e.nombre AS estado
        FROM tareas t
        JOIN categorias c ON t.categoria_id = c.id
        JOIN prioridades p ON t.prioridad_id = p.id
        JOIN estados e ON t.estado_id = e.id
        WHERE t.usuario_id = %s AND t.visible = TRUE
    """, (usuario_id,))

    tareas = cursor.fetchall()
    cursor.close()
    conexion.close()

    ahora = datetime.now()
    tareas_filtradas = []

    for tarea in tareas:
        fecha_limite = tarea['fecha_limite']
        if isinstance(fecha_limite, str):
            try:
                fecha_limite = datetime.strptime(fecha_limite, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                fecha_limite = datetime.strptime(fecha_limite, '%Y-%m-%d')

        diferencia = fecha_limite - ahora
        if diferencia.total_seconds() > 0:
            dias = diferencia.days
            horas, resto = divmod(diferencia.seconds, 3600)
            minutos = resto // 60
            tarea['tiempo_restante'] = f"{dias}d {horas}h {minutos}m"
            tarea['vencida'] = False
        else:
            tarea['tiempo_restante'] = "Vencida"
            tarea['vencida'] = True

        if (
            filtro == 'todas' or
            (filtro == 'vencidas' and tarea['vencida']) or
            (filtro == 'pendientes' and not tarea['vencida'] and tarea['estado'] != 'Completada') or
            (filtro == 'completas' and tarea['estado'] == 'Completada')
        ):
            tareas_filtradas.append(tarea)

    tareas_filtradas.sort(key=lambda t: t['fecha_limite'])

    return render_template('dashboard.html', tareas=tareas_filtradas, filtro=filtro)

#EDITAR TAREA
@app.route('/editar_tarea/<int:id>', methods=['GET', 'POST'])
def editar_tarea(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario_id = session.get('usuario_id')
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    # Obtener tarea y verificar que sea del usuario actual
    cursor.execute("SELECT * FROM tareas WHERE id = %s AND usuario_id = %s", (id, usuario_id))
    tarea = cursor.fetchone()
    if not tarea:
        cursor.close()
        conexion.close()
        return "Tarea no encontrada o acceso no autorizado", 403

    # Obtener opciones desplegables
    cursor.execute("SELECT id, nombre FROM categorias")
    categorias = cursor.fetchall()

    cursor.execute("SELECT id, nombre FROM prioridades")
    prioridades = cursor.fetchall()

    cursor.execute("SELECT id, nombre FROM estados")
    estados = cursor.fetchall()

    error = None
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_limite = request.form['fecha_limite']
        categoria_id = request.form['categoria']
        prioridad_id = request.form['prioridad']
        estado_id = request.form['estado']

        try:
            cursor.execute("""
                UPDATE tareas 
                SET titulo=%s, descripcion=%s, fecha_limite=%s, 
                    categoria_id=%s, prioridad_id=%s, estado_id=%s
                WHERE id=%s AND usuario_id=%s
            """, (titulo, descripcion, fecha_limite, categoria_id, prioridad_id, estado_id, id, usuario_id))
            conexion.commit()
            return redirect(url_for('dashboard'))
        except mysql.connector.Error as e:
            error = f"Error al actualizar la tarea: {str(e)}"

    cursor.close()
    conexion.close()
    return render_template('edit_task.html', tarea=tarea, categorias=categorias, prioridades=prioridades, estados=estados, error=error)

#COMPLETAR TAREA
@app.route('/completar_tarea/<int:id>')
def completar_tarea(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = conectar()
    cursor = conexion.cursor()

    # Verificar que la tarea pertenezca al usuario logueado
    cursor.execute("SELECT * FROM tareas WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
    tarea = cursor.fetchone()

    if tarea is None:
        cursor.close()
        conexion.close()
        return "No tienes permiso para completar esta tarea.", 403

    # Cambiar el estado_id de la tarea a 'Completada'
    cursor.execute("UPDATE tareas SET estado_id = %s WHERE id = %s", (3, id))  # Asegúrate que 3 sea el ID correcto
    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect(url_for('dashboard'))

#ELIMINAR TAREA
@app.route('/eliminar_tarea/<int:id>')
def eliminar_tarea(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = conectar()
    cursor = conexion.cursor()

    # Verificar que la tarea pertenezca al usuario logueado
    cursor.execute("SELECT * FROM tareas WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
    tarea = cursor.fetchone()

    if tarea is None:
        cursor.close()
        conexion.close()
        return "No tienes permiso para eliminar esta tarea.", 403

    # Eliminar la tarea
    cursor.execute("DELETE FROM tareas WHERE id = %s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()

    return redirect(url_for('tareas_ocultas')) 

#OCULTAR TAREA
@app.route('/ocultar_tarea/<int:id>')
def ocultar_tarea(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
    tarea = cursor.fetchone()

    if tarea is None:
        cursor.close()
        conexion.close()
        return "No tienes permiso para ocultar esta tarea.", 403

    cursor.execute("UPDATE tareas SET visible = FALSE WHERE id = %s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()

    return redirect(url_for('dashboard'))

#RESTAURAR TAREA
@app.route('/restaurar_tarea/<int:id>')
def restaurar_tarea(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
    tarea = cursor.fetchone()

    if tarea is None:
        cursor.close()
        conexion.close()
        return "No tienes permiso para ocultar esta tarea.", 403

    cursor.execute("UPDATE tareas SET visible = TRUE WHERE id = %s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()

    return redirect(url_for('dashboard'))

#MOSTRAR TAREAS OCULTAS
@app.route('/tareas_ocultas')
def tareas_ocultas():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario_id = session.get('usuario_id')
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT t.id, t.titulo, t.descripcion, t.fecha_limite,
               c.nombre AS categoria,
               p.nombre AS prioridad,
               e.nombre AS estado
        FROM tareas t
        JOIN categorias c ON t.categoria_id = c.id
        JOIN prioridades p ON t.prioridad_id = p.id
        JOIN estados e ON t.estado_id = e.id
        WHERE t.usuario_id = %s AND t.visible = FALSE
    """, (usuario_id,))

    tareas = cursor.fetchall()
    cursor.close()
    conexion.close()

    ahora = datetime.now()
    for tarea in tareas:
        fecha_limite = tarea['fecha_limite']
        if isinstance(fecha_limite, str):
            try:
                fecha_limite = datetime.strptime(fecha_limite, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                fecha_limite = datetime.strptime(fecha_limite, '%Y-%m-%d')
        diferencia = fecha_limite - ahora
        if diferencia.total_seconds() > 0:
            dias = diferencia.days
            horas, resto = divmod(diferencia.seconds, 3600)
            minutos = resto // 60
            tarea['tiempo_restante'] = f"{dias}d {horas}h {minutos}m"
        else:
            tarea['tiempo_restante'] = "Vencida"

    return render_template('tareas_ocultas.html', tareas=tareas)

#CERRA SESIÓN
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('usuario_id', None)
    return redirect(url_for('login'))

#EDITAR USUARIO
# @app.route('/editar_usuario', methods=['GET', 'POST'])
# def editar_usuario():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    usuario_id = session['usuario_id']

    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario = request.form['usuario']
        email = request.form['email']
        fecha_nacimiento = request.form.get('fdn')
        nueva_password = request.form.get('password')

        # Validar que no exista otro usuario con el mismo usuario o email (excepto el actual)
        cursor.execute(
            "SELECT * FROM usuarios WHERE (usuario=%s OR email=%s) AND id != %s",
            (usuario, email, usuario_id)
        )
        existe = cursor.fetchone()
        if existe:
            cursor.close()
            conexion.close()
            error = "El nombre de usuario o correo ya están en uso por otro usuario."
            # Recargar datos para el form
            conexion = conectar()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
            usuario_data = cursor.fetchone()
            cursor.close()
            conexion.close()
            return render_template('edit_user.html', usuario=usuario_data, error=error)

        # Actualizar datos
        if nueva_password:
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(nueva_password)
            cursor.execute(
                "UPDATE usuarios SET nombre=%s, usuario=%s, email=%s, password=%s, fdn=%s WHERE id=%s",
                (nombre, usuario, email, password_hash, fecha_nacimiento, usuario_id)
            )
        else:
            cursor.execute(
                "UPDATE usuarios SET nombre=%s, usuario=%s, email=%s, fdn=%s WHERE id=%s",
                (nombre, usuario, email, fecha_nacimiento, usuario_id)
            )

        conexion.commit()
        cursor.close()
        conexion.close()

        # Actualizar sesión si cambió el usuario
        session['usuario'] = usuario

        return redirect(url_for('dashboard'))

    # GET: obtener datos del usuario para mostrar en el formulario
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
    usuario_data = cursor.fetchone()
    cursor.close()
    conexion.close()

    return render_template('edit_user.html', usuario=usuario_data)
@app.route('/editar_usuario', methods=['GET', 'POST'])
@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id=None):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    usuario_id_actual = session['usuario_id']
    es_admin = session.get('admin')

    # Si es admin y se proporcionó un id, edita a ese usuario
    if es_admin and id is not None:
        usuario_id_editar = id
    else:
        usuario_id_editar = usuario_id_actual

    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario = request.form['usuario']
        email = request.form['email']
        fecha_nacimiento = request.form.get('fdn')
        nueva_password = request.form.get('password')

        # Validar que no exista otro usuario con mismo usuario o email (excepto el actual)
        cursor.execute(
            "SELECT * FROM usuarios WHERE (usuario=%s OR email=%s) AND id != %s",
            (usuario, email, usuario_id_editar)
        )
        existe = cursor.fetchone()
        if existe:
            cursor.close()
            conexion.close()
            error = "El nombre de usuario o correo ya están en uso por otro usuario."
            conexion = conectar()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id_editar,))
            usuario_data = cursor.fetchone()
            cursor.close()
            conexion.close()
            return render_template('edit_user.html', usuario=usuario_data, error=error)

        # Actualizar datos
        if nueva_password:
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(nueva_password)
            cursor.execute(
                "UPDATE usuarios SET nombre=%s, usuario=%s, email=%s, password=%s, fdn=%s WHERE id=%s",
                (nombre, usuario, email, password_hash, fecha_nacimiento, usuario_id_editar)
            )
        else:
            cursor.execute(
                "UPDATE usuarios SET nombre=%s, usuario=%s, email=%s, fdn=%s WHERE id=%s",
                (nombre, usuario, email, fecha_nacimiento, usuario_id_editar)
            )

        conexion.commit()
        cursor.close()
        conexion.close()

        # Si está editando su propio usuario, actualizar sesión
        if usuario_id_actual == usuario_id_editar:
            session['usuario'] = usuario

        return redirect(url_for('dashboard') if not es_admin else url_for('admin'))

    # GET: obtener datos del usuario para mostrar en el formulario
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id_editar,))
    usuario_data = cursor.fetchone()
    cursor.close()
    conexion.close()

    return render_template('edit_user.html', usuario=usuario_data)


@app.route('/admin')
def admin():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT id, nombre, usuario, email, fdn FROM usuarios")
    usuarios = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template('admin.html', usuarios=usuarios)

@app.route('/admin/editar_usuario/<int:id>', methods=['GET', 'POST'])
def admin_editar_usuario(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    # Obtener datos actuales del usuario
    if request.method == 'GET':
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
        usuario = cursor.fetchone()

        if not usuario:
            cursor.close()
            conexion.close()
            return "Usuario no encontrado", 404

        cursor.close()
        conexion.close()
        return render_template('edit_user.html', usuario=usuario)

    # POST: Actualizar los datos
    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario_nombre = request.form['usuario']
        email = request.form['email']
        fdn = request.form['fdn']
        password = request.form['password']

        # Validaciones opcionales
        if not nombre or not usuario_nombre or not email or not fdn:
            cursor.close()
            conexion.close()
            return render_template('edit_user.html', usuario=request.form, error="Todos los campos excepto contraseña son obligatorios.")

        if password:
            password_hash = generate_password_hash(password)
            cursor.execute("""
                UPDATE usuarios SET nombre=%s, usuario=%s, email=%s, fdn=%s, password=%s WHERE id=%s
            """, (nombre, usuario_nombre, email, fdn, password_hash, id))
        else:
            cursor.execute("""
                UPDATE usuarios SET nombre=%s, usuario=%s, email=%s, fdn=%s WHERE id=%s
            """, (nombre, usuario_nombre, email, fdn, id))

        conexion.commit()
        cursor.close()
        conexion.close()
        return redirect(url_for('admin'))

@app.route('/eliminar_usuario/<int:id>', methods=['POST', 'GET'])
def eliminar_usuario(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect(url_for('admin'))



if __name__ == '__main__':
    app.run(debug=True)
