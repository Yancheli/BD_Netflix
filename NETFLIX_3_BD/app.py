from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config
from models import db, Usuario, Perfil, Contenido, Favorito
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


# ---------------- PÁGINA PRINCIPAL (PELÍCULAS / SERIES) ----------------
@app.route('/main')
def main():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    perfil_nombre = request.args.get('perfil')
    categoria_id = request.args.get('categoria', type=int)
    
    # Obtener todas las categorías
    from models import Category
    categorias = Category.query.all()
    
    # Filtrar contenido por categoría si se especifica
    if categoria_id:
        contenidos = Contenido.query.filter_by(category_id=categoria_id).all()
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
                         perfil=perfil_nombre)


# ---------------- FAVORITOS ----------------
@app.route('/agregar_favorito/<int:contenido_id>', methods=['POST'])
def agregar_favorito(contenido_id):
    if 'usuario_id' not in session:
        return {'success': False, 'error': 'No autenticado'}, 401
    
    perfil_nombre = request.form.get('perfil')
    if not perfil_nombre:
        return {'success': False, 'error': 'Perfil no especificado'}, 400
    
    # Obtener el perfil
    usuario = Usuario.query.get(session['usuario_id'])
    perfil = Perfil.query.filter_by(nombre=perfil_nombre, usuario_id=usuario.id).first()
    
    if not perfil:
        return {'success': False, 'error': 'Perfil no encontrado'}, 404
    
    # Verificar si ya existe en favoritos
    favorito_existente = Favorito.query.filter_by(
        perfil_id=perfil.id,
        contenido_id=contenido_id
    ).first()
    
    if favorito_existente:
        return {'success': False, 'error': 'Ya está en favoritos'}, 400
    
    # Agregar a favoritos
    nuevo_favorito = Favorito(
        perfil_id=perfil.id,
        contenido_id=contenido_id
    )
    db.session.add(nuevo_favorito)
    db.session.commit()
    
    return {'success': True, 'message': 'Agregado a favoritos'}, 200


@app.route('/eliminar_favorito/<int:contenido_id>', methods=['POST'])
def eliminar_favorito(contenido_id):
    if 'usuario_id' not in session:
        return {'success': False, 'error': 'No autenticado'}, 401
    
    perfil_nombre = request.form.get('perfil')
    if not perfil_nombre:
        return {'success': False, 'error': 'Perfil no especificado'}, 400
    
    # Obtener el perfil
    usuario = Usuario.query.get(session['usuario_id'])
    perfil = Perfil.query.filter_by(nombre=perfil_nombre, usuario_id=usuario.id).first()
    
    if not perfil:
        return {'success': False, 'error': 'Perfil no encontrado'}, 404
    
    # Buscar y eliminar el favorito
    favorito = Favorito.query.filter_by(
        perfil_id=perfil.id,
        contenido_id=contenido_id
    ).first()
    
    if not favorito:
        return {'success': False, 'error': 'No está en favoritos'}, 404
    
    db.session.delete(favorito)
    db.session.commit()
    
    return {'success': True, 'message': 'Eliminado de favoritos'}, 200


@app.route('/favoritos')
def favoritos():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    perfil_nombre = request.args.get('perfil')
    if not perfil_nombre:
        flash('Debes seleccionar un perfil')
        return redirect(url_for('perfiles'))
    
    # Obtener el perfil
    usuario = Usuario.query.get(session['usuario_id'])
    perfil = Perfil.query.filter_by(nombre=perfil_nombre, usuario_id=usuario.id).first()
    
    if not perfil:
        flash('Perfil no encontrado')
        return redirect(url_for('perfiles'))
    
    # Obtener favoritos del perfil
    favoritos = Favorito.query.filter_by(perfil_id=perfil.id).all()
    contenidos_favoritos = [f.contenido for f in favoritos]
    
    # Separar películas y series
    peliculas = [c for c in contenidos_favoritos if c.tipo == 'movie']
    series = [c for c in contenidos_favoritos if c.tipo == 'series']
    
    return render_template('favoritos.html',
                         peliculas=peliculas,
                         series=series,
                         perfil=perfil_nombre,
                         es_infantil=perfil.es_infantil)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)