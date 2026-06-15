import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = 'todo_bonito_clave_secreta'

# Configuración de la Base de Datos (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todobonito.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ⚠️ COMPLETÁ ACÁ CON TUS DATOS DE CLOUDINARY:
cloudinary.config(
  cloud_name = "dskr6hoxg",
  api_key = "689217927388896",
  api_secret = "JzxF3utVFgxgb8i1odH-dIobw9c"
)

# Modelo de la tabla de Productos
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200))
    categoria = db.Column(db.String(50), nullable=False)
    imagen_url = db.Column(db.String(300))

# Crear la base de datos físicamente al arrancar
with app.app_context():
    db.create_all()

from flask import session  # Asegurate de que 'session' esté importado arriba junto a redirect, url_for, etc.

# CLAVE DE ACCESO (Cambiá 'admin123' por la contraseña secreta que vos quieras)
CONTRASENA_ADMIN = "todobonito2024"

# --- RUTA DE LOGIN (PANTALLA DE ACCESO) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        clave_ingresada = request.form.get('password')
        if clave_ingresada == CONTRASENA_ADMIN:
            session['admin_logueado'] = True  # Guardamos en la memoria del navegador que ya entró
            return redirect(url_for('admin'))
        else:
            flash('Contraseña incorrecta. Intentalo de nuevo.', 'danger')
    return render_template('login.html')

# --- RUTA DE LOGOUT (PARA CERRAR SESIÓN) ---
@app.route('/logout')
def logout():
    session.pop('admin_logueado', None)  # Borra la sesión
    return redirect(url_for('inicio'))

# --- PANEL DE ADMINISTRACIÓN PROTEGIDO ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # 🛑 CONTROL DE SEGURIDAD: Si no está logueado, lo mandamos a ponerse la clave
    if not session.get('admin_logueado'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion')
        categoria = request.form.get('categoria')
        foto = request.files.get('foto')

        imagen_url = "https://via.placeholder.com/300"

        if foto and foto.filename != '':
            try:
                upload_result = cloudinary.uploader.upload(foto)
                imagen_url = upload_result['secure_url']
            except Exception as e:
                print(f"Error al subir imagen: {e}")

        nuevo_producto = Producto(
            titulo=titulo, 
            precio=float(precio), 
            descripcion=descripcion, 
            categoria=categoria, 
            imagen_url=imagen_url
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        
        return redirect(url_for('admin'))

    productos = Producto.query.all()
    return render_template('admin.html', productos=productos)

if __name__ == '__main__':
    app.run(debug=True)