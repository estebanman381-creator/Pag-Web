from flask import Flask, render_template, request

app = Flask(__name__)

# Ruta para la página de inicio
@app.route('/')
def inicio():
    return render_template('inicio.html')

# Ruta para la página de contacto
@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        # Aquí procesaremos los datos que envíe el cliente más adelante
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        mensaje = request.form.get('mensaje')
        
        # Por ahora, solo simulamos que se envió con éxito
        return f"¡Gracias {nombre}! Recibimos tu mensaje. Nos contactaremos a {email}."
    
    return render_template('contacto.html')

if __name__ == '__main__':
    # El modo debug te permite ver los cambios en tiempo real sin reiniciar el servidor
    app.run(debug=True)