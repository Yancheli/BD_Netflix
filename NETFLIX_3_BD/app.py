from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config
from models import db, Usuario, Perfil, Contenido, Favorito, Category
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar la base de datos
db.init_app(app)

# Crear las tablas si no existen
with app.app_context():
    db.create_all()

# ---------------- RUTAS PRINCIPALES ----------------

@app.route('/')
def index():
    return render_template('index.html')


# ---------------- REGISTRO ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            return render_template('register.html', error="Completa todos los campos")

        # Verificar si el usuario ya existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            return render_template('register.html', error="El email ya está registrado")

        # Crear nuevo usuario
        nuevo_usuario = Usuario(
            email=email,
            contraseña=generate_password_hash(password)
        )
        db.session.add(nuevo_usuario)
        db.session.commit()

        session['usuario_id'] = nuevo_usuario.id
        return redirect(url_for('planes'))

    return render_template('register.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.contraseña, password):
            session['usuario_id'] = usuario.id
            
            # Verificar si tiene perfiles creados
            if usuario.perfiles:
                return redirect(url_for('perfiles'))
            return redirect(url_for('planes'))
        else:
            return render_template('login.html', error="Email o contraseña incorrectos")

    return render_template('login.html')


# ---------------- PLANES ----------------
@app.route('/planes')
def planes():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('planes.html')


@app.route('/guardar_plan', methods=['POST'])
def guardar_plan():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    plan = request.form.get('plan')
    session['plan_pending'] = plan
    return redirect(url_for('pagar'))


@app.route('/pagar', methods=['GET', 'POST'])
def pagar():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    plan = session.get('plan_pending', 'basico')

    if request.method == 'POST':
        card_number = request.form.get('card_number')
        name = request.form.get('name')
        exp = request.form.get('exp')
        cvv = request.form.get('cvv')

        if not card_number or not name or not exp or not cvv:
            return render_template('pagar.html', plan=plan, error='Completa los datos de la tarjeta')

        session['plan'] = plan
        session.pop('plan_pending', None)

        # Crear perfil por defecto
        usuario = Usuario.query.get(session['usuario_id'])
        if not usuario.perfiles:
            perfil_default = Perfil(
                nombre=usuario.email.split('@')[0],
                usuario_id=usuario.id
            )
            db.session.add(perfil_default)
            db.session.commit()

        flash(f'Pago simulado correctamente. Plan activado: {plan}')
        return redirect(url_for('perfiles'))

    return render_template('pagar.html', plan=plan)


# ---------------- PERFILES ----------------
@app.route('/perfiles')
def perfiles():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    plan = session.get('plan', 'basico')
    plan_limits = {'basico': 1, 'estandar': 2, 'premium': 4}
    max_perfiles = plan_limits.get(plan, 1)

    return render_template('perfiles.html', 
                         perfiles=usuario.perfiles, 
                         max_perfiles=max_perfiles)


@app.route('/crear_perfil', methods=['POST'])
def crear_perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    plan = session.get('plan', 'basico')
    plan_limits = {'basico': 1, 'estandar': 2, 'premium': 4}
    max_perfiles = plan_limits.get(plan, 1)

    if len(usuario.perfiles) >= max_perfiles:
        flash('No puedes crear más perfiles con el plan actual')
        return redirect(url_for('perfiles'))

    nombre = request.form.get('nombre')
    es_infantil = bool(request.form.get('es_infantil'))
    
    if not nombre:
        flash('El nombre del perfil es requerido')
        return redirect(url_for('perfiles'))

    nuevo_perfil = Perfil(
        nombre=nombre,
        es_infantil=es_infantil,
        usuario_id=usuario.id
    )
    db.session.add(nuevo_perfil)
    db.session.commit()
    
    flash('Perfil creado exitosamente')
    return redirect(url_for('perfiles'))


# ---------------- GESTIÓN DE PERFILES ----------------
@app.route('/gestionar_perfiles')
def gestionar_perfiles():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    plan = session.get('plan', 'basico')
    plan_limits = {'basico': 1, 'estandar': 2, 'premium': 4}
    max_perfiles = plan_limits.get(plan, 1)
    
    return render_template('gestionar_perfiles.html', 
                         perfiles=usuario.perfiles,
                         max_perfiles=max_perfiles)


@app.route('/editar_perfil/<int:perfil_id>', methods=['GET', 'POST'])
def editar_perfil(perfil_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    perfil = Perfil.query.get_or_404(perfil_id)
    
    # Verificar que el perfil pertenece al usuario
    if perfil.usuario_id != session['usuario_id']:
        flash('No tienes permiso para editar este perfil')
        return redirect(url_for('gestionar_perfiles'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        es_infantil = bool(request.form.get('es_infantil'))
        
        if not nombre:
            flash('El nombre del perfil es requerido')
            return render_template('editar_perfil.html', perfil=perfil)
        
        perfil.nombre = nombre
        perfil.es_infantil = es_infantil
        db.session.commit()
        
        flash('Perfil actualizado exitosamente')
        return redirect(url_for('gestionar_perfiles'))
    
    return render_template('editar_perfil.html', perfil=perfil)


@app.route('/eliminar_perfil/<int:perfil_id>', methods=['POST'])
def eliminar_perfil(perfil_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    perfil = Perfil.query.get_or_404(perfil_id)
    
    # Verificar que el perfil pertenece al usuario
    if perfil.usuario_id != session['usuario_id']:
        flash('No tienes permiso para eliminar este perfil')
        return redirect(url_for('gestionar_perfiles'))
    
    # Verificar que no sea el último perfil
    usuario = Usuario.query.get(session['usuario_id'])
    if len(usuario.perfiles) <= 1:
        flash('No puedes eliminar el último perfil')
        return redirect(url_for('gestionar_perfiles'))
    
    db.session.delete(perfil)
    db.session.commit()
    
    flash('Perfil eliminado exitosamente')
    return redirect(url_for('gestionar_perfiles'))


# ---------------- PÁGINA PRINCIPAL (PELÍCULAS / SERIES) ----------------
@app.route('/main')
def main():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    perfil_nombre = request.args.get('perfil')
    categoria_id = request.args.get('categoria', type=int)
    
    # Obtener el perfil actual
    usuario = Usuario.query.get(session['usuario_id'])
    perfil_actual = None
    if perfil_nombre:
        perfil_actual = Perfil.query.filter_by(
            nombre=perfil_nombre, 
            usuario_id=usuario.id
        ).first()
    
    # Obtener todas las categorías
    categorias = Category.query.all()
    
    # Si es perfil infantil, filtrar solo categorías permitidas
    if perfil_actual and perfil_actual.es_infantil:
        categorias_permitidas = ['Infantil', 'Romance']
        categorias = [c for c in categorias if c.name in categorias_permitidas]
        
        # Si se seleccionó una categoría no permitida, redirigir
        if categoria_id:
            categoria_seleccionada = Category.query.get(categoria_id)
            if categoria_seleccionada and categoria_seleccionada.name not in categorias_permitidas:
                flash('Este contenido no está disponible en perfiles infantiles')
                return redirect(url_for('main', perfil=perfil_nombre))
    
    # Filtrar contenido por categoría si se especifica
    if categoria_id:
        contenidos = Contenido.query.filter_by(category_id=categoria_id).all()
    else:
        # Si es perfil infantil, mostrar solo contenido permitido
        if perfil_actual and perfil_actual.es_infantil:
            categorias_permitidas_ids = [c.id for c in categorias]
            contenidos = Contenido.query.filter(
                Contenido.category_id.in_(categorias_permitidas_ids)
            ).all()
        else:
            contenidos = Contenido.query.all()
    
    # Separar películas y series
    peliculas = [c for c in contenidos if c.tipo == 'movie']
    series = [c for c in contenidos if c.tipo == 'series']
    
    return render_template('main.html', 
                         peliculas=peliculas, 
                         series=series,
                         categorias=categorias,
                         categoria_seleccionada=categoria_id,
                         perfil=perfil_nombre,
                         es_infantil=perfil_actual.es_infantil if perfil_actual else False)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)