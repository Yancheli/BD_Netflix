from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "clave_secreta_segura"

# Diccionario para guardar usuarios (solo mientras el servidor corre)
usuarios = {}

@app.route('/')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    movies = [
        {'title': 'Inception', 'image': 'https://image.tmdb.org/t/p/w500/qmDpIHrmpJINaRKAfWQfftjCdyi.jpg'},
        {'title': 'Interstellar', 'image': 'https://image.tmdb.org/t/p/w500/rAiYTfKGqDCRIIqo664sY9XZIvQ.jpg'},
        {'title': 'The Batman', 'image': 'https://image.tmdb.org/t/p/w500/74xTEgt7R36Fpooo50r9T25onhq.jpg'}
    ]
    return render_template('index.html', movies=movies, usuario=session['usuario'])



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']

        if usuario in usuarios and usuarios[usuario] == contraseña:
            session['usuario'] = usuario
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']

        if usuario in usuarios:
            return render_template('register.html', error="El usuario ya existe")
        else:
            usuarios[usuario] = contraseña
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)