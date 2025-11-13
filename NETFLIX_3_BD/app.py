from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "clave_secreta_segura"

# Diccionario para simular base de datos de usuarios
usuarios = {}

# Contenido simulado: películas y series con imágenes locales
peliculas = [
    {'id': 1, 'titulo': 'Inception', 'tipo': 'movie', 'imagen': 'images/inception.jpg', 'trailer_url': 'https://www.youtube.com/watch?v=YoHD9XEInc0', 'genre': 'Ciencia Ficción', 'duration_min': 148, 'trailer_duration': '2:28', 'rating': 'PG-13'},
    {'id': 2, 'titulo': 'Parásitos', 'tipo': 'movie', 'imagen': 'images/parasitos.jpg', 'trailer_url': 'https://www.youtube.com/watch?v=5xH0HfJHsaY', 'genre': 'Drama', 'duration_min': 132, 'trailer_duration': '2:10', 'rating': 'R'},
    {'id': 3, 'titulo': 'Your Name', 'tipo': 'movie', 'imagen': 'images/yourname.png', 'trailer_url': 'https://www.youtube.com/watch?v=xU47nhruN-Q', 'genre': 'Animación', 'duration_min': 107, 'trailer_duration': '1:55', 'rating': 'PG'},
]

series = [
    {'id': 1, 'titulo': 'Stranger Things', 'tipo': 'series', 'imagen': 'images/stranger.jpg', 'trailer_url': 'https://www.youtube.com/watch?v=mnd7sFt5c3A', 'genre': 'Ciencia Ficción', 'seasons': 4, 'trailer_duration': '1:50'},
    {'id': 2, 'titulo': 'La Casa de Papel', 'tipo': 'series', 'imagen': 'images/lcdp.jpg', 'trailer_url': 'https://www.youtube.com/watch?v=VyQA4K_Bd8Q', 'genre': 'Acción', 'seasons': 5, 'trailer_duration': '2:05'},
    {'id': 3, 'titulo': 'Narcos', 'tipo': 'series', 'imagen': 'images/narcos.jpg', 'trailer_url': 'https://www.youtube.com/watch?v=G3_2v5mQIOg', 'genre': 'Drama', 'seasons': 3, 'trailer_duration': '1:40'},
]

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

        if username in usuarios:
            return render_template('register.html', error="El usuario ya existe")

        usuarios[username] = {
            'email': email,
            'password': password,
            'plan': None,
            'perfiles': []
        }

        session['usuario'] = username
        return redirect(url_for('planes'))

    return render_template('register.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in usuarios and usuarios[username]['password'] == password:
            session['usuario'] = username
            if usuarios[username].get('plan'):
                return redirect(url_for('perfiles'))
            return redirect(url_for('planes'))
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos")

    return render_template('login.html')


# ---------------- PLANES ----------------
@app.route('/planes')
def planes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('planes.html')


@app.route('/guardar_plan', methods=['POST'])
def guardar_plan():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    plan = request.form.get('plan')
    usuarios[session['usuario']]['plan_pending'] = plan
    return redirect(url_for('pagar'))


@app.route('/pagar', methods=['GET', 'POST'])
def pagar():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    user = usuarios[session['usuario']]
    plan = user.get('plan_pending') or user.get('plan') or 'basico'

    if request.method == 'POST':
        card_number = request.form.get('card_number')
        name = request.form.get('name')
        exp = request.form.get('exp')
        cvv = request.form.get('cvv')

        if not card_number or not name or not exp or not cvv:
            return render_template('pagar.html', plan=plan, error='Completa los datos de la tarjeta')

        usuarios[session['usuario']]['plan'] = plan
        usuarios[session['usuario']].pop('plan_pending', None)

        # Inicializar perfiles por defecto
        plan_limits = {'basico': 1, 'estandar': 2, 'premium': 4}
        max_perfiles = plan_limits.get(plan, 1)
        if not usuarios[session['usuario']]['perfiles']:
            usuarios[session['usuario']]['perfiles'].append({'nombre': session['usuario'], 'imagen': 'images/avatar1.png', 'es_infantil': False})

        flash(f'Pago simulado correctamente. Plan activado: {plan}')
        return redirect(url_for('perfiles'))

    return render_template('pagar.html', plan=plan)


# ---------------- PERFILES ----------------
@app.route('/perfiles')
def perfiles():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    user = usuarios[session['usuario']]
    plan = user.get('plan', 'basico')
    plan_limits = {'basico': 1, 'estandar': 2, 'premium': 4}
    max_perfiles = plan_limits.get(plan, 1)

    perfiles = user.get('perfiles', [])
    for p in perfiles:
        p.setdefault('imagen', 'images/avatar1.png')

    return render_template('perfiles.html', perfiles=perfiles, max_perfiles=max_perfiles)


@app.route('/crear_perfil', methods=['POST'])
def crear_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    user = usuarios[session['usuario']]
    plan = user.get('plan', 'basico')
    plan_limits = {'basico': 1, 'estandar': 2, 'premium': 4}
    max_perfiles = plan_limits.get(plan, 1)

    perfiles = user.setdefault('perfiles', [])
    if len(perfiles) >= max_perfiles:
        flash('No puedes crear más perfiles con el plan actual')
        return redirect(url_for('perfiles'))

    nombre = request.form.get('nombre')
    es_infantil = bool(request.form.get('es_infantil'))
    if not nombre:
        flash('El nombre del perfil es requerido')
        return redirect(url_for('perfiles'))

    perfiles.append({'nombre': nombre, 'imagen': 'images/avatar1.png', 'es_infantil': es_infantil})
    flash('Perfil creado')
    return redirect(url_for('perfiles'))


# ---------------- PÁGINA PRINCIPAL (PELÍCULAS / SERIES) ----------------
@app.route('/main')
def main():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    perfil = request.args.get('perfil')
    return render_template('main.html', peliculas=peliculas, series=series, perfil=perfil)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
