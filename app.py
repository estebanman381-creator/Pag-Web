import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = 'todo_bonito_clave_secreta'

# Configuración de la Base de Datos (PostgreSQL en Render / SQLite en tu compu)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Render suele dar URLs que empiezan con 'postgres://', pero SQLAlchemy necesita 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todobonito.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Credenciales de Cloudinary
cloudinary.config(
  cloud_name = "dskr6hoxg",
  api_key = "689217927388896",
  api_secret = "JzxF3utVFgxgb8i1odH-dIobw9c"
)

# --- 📸 MODELOS ACTUALIZADOS PARA MÚLTIPLES FOTOS ---

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200))
    categoria = db.Column(db.String(50), nullable=False)
    # Relación con la nueva tabla de imágenes (elimina huérfanos al borrar un producto)
    imagenes = db.relationship('ImagenProducto', backref='producto', lazy=True, cascade="all, delete-orphan")

class ImagenProducto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    url = db.Column(db.String(300), nullable=False)


# --- 📓 MODELOS PARA EL LIBRO DE DEUDAS ---
class Deudor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    telefono = db.Column(db.String(50))
    saldo = db.Column(db.Float, default=0.0)
    movimientos = db.relationship('HistorialDeuda', backref='deudor', lazy=True, cascade="all, delete-orphan")

class HistorialDeuda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deudor_id = db.Column(db.Integer, db.ForeignKey('deudor.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)
    descripcion = db.Column(db.String(200), nullable=False)
    monto = db.Column(db.Float, nullable=False)

# Crear la base de datos físicamente al arrancar
with app.app_context():
    db.create_all()

# Contraseña de acceso al panel administrador
CONTRASENA_ADMIN = "todobonito2024"


# --- 🌸 RUTA DE LA PÁGINA PRINCIPAL ---
@app.route('/')
def inicio():
    try:
        productos = Producto.query.all()
    except Exception as e:
        print(f"Base de datos no lista: {e}")
        productos = []
    return render_template('inicio.html', productos=productos)


# --- RUTA DE CONTACTO ---
@app.route('/contacto')
def contacto():
    return render_template('contacto.html')


# --- RUTA DE LOGIN (PANTALLA DE ACCESO) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        clave_ingresada = request.form.get('password')
        if clave_ingresada == CONTRASENA_ADMIN:
            session['admin_logueado'] = True
            return redirect(url_for('admin'))
        else:
            flash('Contraseña incorrecta. Intentalo de nuevo.', 'danger')
    return render_template('login.html')


# --- RUTA DE LOGOUT (PARA CERRAR SESIÓN) ---
@app.route('/logout')
def logout():
    session.pop('admin_logueado', None)
    return redirect(url_for('inicio'))


# --- PANEL DE ADMINISTRACIÓN PROTEGIDO (REFORMADO PARA RECIBIR MUCHAS IMÁGENES) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin_logueado'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion')
        categoria = request.form.get('categoria')
        
        # Agarra la lista completa de fotos seleccionadas
        fotos = request.files.getlist('foto')

        nuevo_producto = Producto(
            titulo=titulo, 
            precio=float(precio), 
            descripcion=descripcion, 
            categoria=categoria
        )
        db.session.add(nuevo_producto)
        db.session.flush() # Sincroniza para obtener el ID asignado al producto

        fotos_subidas = 0
        for foto in fotos:
            if foto and foto.filename != '':
                try:
                    upload_result = cloudinary.uploader.upload(foto)
                    nueva_imagen = ImagenProducto(producto_id=nuevo_producto.id, url=upload_result['secure_url'])
                    db.session.add(nueva_imagen)
                    fotos_subidas += 1
                except Exception as e:
                    print(f"Error al subir imagen a Cloudinary: {e}")
        
        # Si no cargaron ninguna foto, asigna un marcador de posición
        if fotos_subidas == 0:
            imagen_defecto = ImagenProducto(producto_id=nuevo_producto.id, url="https://via.placeholder.com/300")
            db.session.add(imagen_defecto)

        db.session.commit()
        return redirect(url_for('admin'))

    productos = Producto.query.all()
    return render_template('admin.html', productos=productos)


# --- 🔍 DETALLE, FECHAS, PAGOS Y AGREGAR DEUDA ---
@app.route('/admin/deudas/<int:id>', methods=['GET', 'POST'])
def detalle_deuda(id):
    if not session.get('admin_logueado'):
        return redirect(url_for('login'))

    cliente = Deudor.query.get_or_44(id) if hasattr(Deudor.query, 'get_or_44') else Deudor.query.get_or_404(id)

    if request.method == 'POST':
        tipo_movimiento = request.form.get('tipo')
        descripcion = request.form.get('descripcion')
        monto = float(request.form.get('monto'))

        if tipo_movimiento == 'pago':
            monto = -monto
            if not descripcion:
                descripcion = "Pago Parcial"
        else:
            if not descripcion:
                descripcion = "Compra anotada"

        cliente.saldo += monto

        nuevo_movimiento = HistorialDeuda(
            deudor_id=cliente.id,
            descripcion=descripcion,
            monto=monto
        )
        
        db.session.add(nuevo_movimiento)
        db.session.commit()
        return redirect(url_for('detalle_deuda', id=cliente.id))

    return render_template('detalle_deuda.html', cliente=cliente)


# --- 📑 VISTA GENERAL DE DEUDAS (PROTEGIDA) ---
@app.route('/admin/deudas', methods=['GET', 'POST'])
def admin_deudas():
    if not session.get('admin_logueado'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form.get('nombre').strip()
        telefono = request.form.get('telefono').strip()
        
        existe = Deudor.query.filter_by(nombre=nombre).first()
        if not existe and nombre:
            nuevo_deudor = Deudor(nombre=nombre, telefono=telefono)
            db.session.add(nuevo_deudor)
            db.session.commit()
        return redirect(url_for('admin_deudas'))

    deudores = Deudor.query.all()
    return render_template('admin_deudas.html', deudores=deudores)


# --- RUTA PARA ELIMINAR UN PRODUCTO ---
@app.route('/admin/eliminar/<int:id>', methods=['POST'])
def eliminar_producto(id):
    if not session.get('admin_logueado'):
        return redirect(url_for('login'))
        
    producto = Producto.query.get_or_404(id)
    try:
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado correctamente.', 'success')
    except Exception as e:
        print(f"Error al eliminar producto: {e}")
        flash('No se pudo eliminar el producto.', 'danger')
        
    return redirect(url_for('admin'))


# --- 🏷️ RUTA DINÁMICA PARA LOS RUBROS ---
@app.route('/rubro/<nombre_categoria>')
def mostrar_rubro(nombre_categoria):
    try:
        productos_filtrados = Producto.query.filter_by(categoria=nombre_categoria).all()
    except Exception as e:
        print(f"Error al filtrar productos: {e}")
        productos_filtrados = []
    
    titulo_estetico = nombre_categoria.replace('-', ' ').title()
    return render_template('rubro.html', productos=productos_filtrados, categoria_titulo=titulo_estetico)


# --- 🛒 RUTA DEL CARRITO ---
@app.route('/carrito')
def carrito():
    return render_template('carrito.html')


if __name__ == '__main__':
    app.run(debug=True)