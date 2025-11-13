from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contraseña = db.Column(db.String(200), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
   
    perfiles = db.relationship('Perfil', backref='usuario', lazy=True, cascade='all, delete-orphan')

class Perfil(db.Model):
    __tablename__ = 'perfiles'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    avatar = db.Column(db.String(200), default='avatar1.png')
    es_infantil = db.Column(db.Boolean, default=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    
    favoritos = db.relationship('Favorito', backref='perfil', lazy=True, cascade='all, delete-orphan')

class Contenido(db.Model):
    __tablename__ = 'contenidos'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    imagen_url = db.Column(db.String(500))
    tipo = db.Column(db.String(20))  
    genero = db.Column(db.String(100))
    año = db.Column(db.Integer)
    duracion = db.Column(db.String(50))  
    calificacion = db.Column(db.String(10)) 
    fecha_agregado = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    favoritos = db.relationship('Favorito', backref='contenido', lazy=True)

class Favorito(db.Model):
    __tablename__ = 'favoritos'
    id = db.Column(db.Integer, primary_key=True)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfiles.id'), nullable=False)
    contenido_id = db.Column(db.Integer, db.ForeignKey('contenidos.id'), nullable=False)
    fecha_agregado = db.Column(db.DateTime, default=datetime.utcnow)