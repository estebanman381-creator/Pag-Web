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

# --- RUTA DE LA PÁGINA PRINCIPAL ---
@app.route('/')
def inicio():
    # Buscamos todos los productos guardados para pasárselos a la web
    productos = Producto.query.all()
    return render_template('inicio.html', productos=productos)

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

# --- PANEL DE ADMINISTRACIÓN SECRETO ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion')
        categoria = request.form.get('categoria')
        foto = request.files.get('foto')

        imagen_url = "https://via.placeholder.com/300"  # Imagen gris por defecto

        # Subida real a Cloudinary
        if foto and foto.filename != '':
            try:
                upload_result = cloudinary.uploader.upload(foto)
                imagen_url = upload_result['secure_url']
            except Exception as e:
                print(f"Error al subir imagen: {e}")

        # Guardamos todo en el archivo SQLite
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

    # Si entramos normal por el navegador, nos muestra la lista de lo cargado
    productos = Producto.query.all()
    return render_template('admin.html', productos=productos)

if __name__ == '__main__':
    app.run(debug=True)