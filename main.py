from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave segura

def encriptar(texto):
    clave = Fernet.generate_key()
    objeto_cifrado = Fernet(clave)
    texto_incriptado = objeto_cifrado.encrypt(str.encode(texto))
    return clave, texto_incriptado

def desencriptar(texto_incriptado, clave):
    objeto_cifrado = Fernet(clave)
    texto_desencriptado_bytes = objeto_cifrado.decrypt(texto_incriptado)
    texto_desencriptado = texto_desencriptado_bytes.decode()
    return texto_desencriptado

# Esta funcion es el que se encarga de insertar los datos encriptados en caso de que no exista una tabla crea uno
def insertar_usuario(usuario, contrasena):
    conexion = mysql.connector.connect(
        user="root",
        password='',
        host='localhost',
        database='usu_contra',
        port='3306'
    )
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datos_encriptados (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            USUARIO VARCHAR(255),
            CONTRASENA VARCHAR(255),
            CLAVE VARCHAR(255)
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM datos_encriptados WHERE USUARIO = %s", (usuario,))
    existe_usuario = cursor.fetchone()[0]

    if existe_usuario > 0:
        cursor.close()
        conexion.close()
    
    else:

        clave, contrasena_encriptada = encriptar(contrasena)
        clave = clave.decode('utf-8')
        contrasena_encriptada = contrasena_encriptada.decode('utf-8')

        cursor.execute("INSERT INTO datos_encriptados (USUARIO, CONTRASENA, CLAVE) VALUES (%s, %s, %s)",
                    (usuario, contrasena_encriptada, clave))
        conexion.commit()

        cursor.close()
        conexion.close()

#en esta parte del codigo se encarga de obtener los datos de la base de datos para luego desencriptarlos y comparar si las respuestas son correctas
def obtener_datos_usuario(nombre_usuario):
    conexion = mysql.connector.connect(
        user="root",
        password='',
        host='localhost',
        database='usu_contra',
        port='3306'
    )
    cursor = conexion.cursor()

    cursor.execute("SELECT USUARIO, CONTRASENA, CLAVE FROM datos_encriptados WHERE USUARIO = %s", (nombre_usuario,))
    resultado = cursor.fetchone()

    cursor.close()
    conexion.close()

    return resultado

####################################### trabajando con el crud ############################################

def establecer_conexion():
    return mysql.connector.connect(
        user="root",
        password='',
        host='localhost',
        database='epg_absmain',
        port='3306'
    )

#esto ya es lo que se va a mostrar en pantalla
def obtener_programas():
    conex = establecer_conexion()
    cursor = conex.cursor(dictionary=True)
    cursor.execute("SELECT dicprogramas.IdFacultad,dicprogramas.Nombre FROM dicprogramas")
    programas = cursor.fetchall()
    cursor.close()
    conex.close()
    return programas

#insertar programas a la base de datos
def insertar_programa(abreviatura_facultad, nombre_programa):
    conex = establecer_conexion()
    cursor = conex.cursor()
    insert_query = """
        INSERT INTO dicprogramas (IdFacultad, Nombre, CodPrograma, Tipo)
        VALUES (%s, %s, %s, %s)
    """
    valores = (1, nombre_programa, abreviatura_facultad, 1)
    cursor.execute(insert_query, valores)
    conex.commit()
    cursor.close()
    conex.close()

def obtener_programa_por_id(id):
    conex = establecer_conexion()
    cursor = conex.cursor(dictionary=True)
    cursor.execute("SELECT * FROM dicprogramas WHERE Id = %s", (id,))
    programa = cursor.fetchone()
    cursor.close()
    conex.close()
    return programa


#actualiza programas 

def actualizar_programa(id, abreviatura_facultad, nombre_programa):
    conex = establecer_conexion()
    cursor = conex.cursor()
    update_query = """
        UPDATE dicprogramas
        SET CodPrograma = %s, Nombre = %s
        WHERE Id = %s
    """
    valores = (abreviatura_facultad, nombre_programa, id)
    cursor.execute(update_query, valores)
    conex.commit()
    cursor.close()
    conex.close()

##elimina programas

def eliminar_programa(id):
    conex = establecer_conexion()
    cursor = conex.cursor()
    delete_query = "DELETE FROM dicprogramas WHERE Id = %s"
    valores = (id,)
    cursor.execute(delete_query, valores)
    conex.commit()
    cursor.close()
    conex.close()



####################################### views ############################################


def vista_facultades():
    connection = establecer_conexion()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM vista_facultades")
    vista_resultados = cursor.fetchall()
    cursor.close()
    connection.close()
    return vista_resultados

def vista_programas():
    connection = establecer_conexion()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM vista_programas")
    vista_resultados = cursor.fetchall()
    cursor.close()
    connection.close()
    return vista_resultados


def vista_rannking_facultades():
    connection = establecer_conexion()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM vista_ranking_facultad_mas_programas")
    vista_resultados = cursor.fetchall()
    cursor.close()
    connection.close()
    return vista_resultados


########################################## las rutas log ############################################

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro', methods=['POST'])
def registro():
    usuario = request.form['username']
    contrasena = request.form['password']

    insertar_usuario(usuario, contrasena)
    flash('success', '¡Registro exitoso!')

    return render_template('registrado.html')

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form['username']
    contrasena = request.form['password']

    datos_usuario = obtener_datos_usuario(usuario)

    if datos_usuario:
        usser, contra, clave = datos_usuario
        contrasena_desencriptada = desencriptar(contra, clave)
        if contrasena == contrasena_desencriptada:
            programas = obtener_programas()
            return render_template('ingreso.html', programas=programas)

        else:
            flash('danger', '¡Contraseña incorrecta!')
    else:
        flash('danger', '¡Usuario no encontrado!')

    return redirect(url_for('index'))


################################################# las rutas de crud ############################################

@app.route('/login')
def mostrar_programas():
    programas = obtener_programas()
    return render_template('ingreso.html', programas=programas)


# Ruta para crear un nuevo programa
@app.route('/crear_programa', methods=['GET', 'POST'])
def crear_programa():
    if request.method == 'POST':
        abreviatura_facultad = request.form['abreviatura_facultad']
        nombre_programa = request.form['nombre_programa']
        insertar_programa(abreviatura_facultad, nombre_programa)
        flash('Programa creado exitosamente', 'success')
        return redirect(url_for('mostrar_programas'))

    return render_template('crear.html')

# Ruta para editar un programa existente
@app.route('/editar_programa/<int:id>', methods=['GET', 'POST'])
def editar_programa(id):
    programa = obtener_programa_por_id(id)

    if request.method == 'POST':
        abreviatura_facultad = request.form['abreviatura_facultad']
        nombre_programa = request.form['nombre_programa']
        actualizar_programa(id, abreviatura_facultad, nombre_programa)
        flash('Programa editado exitosamente', 'success')
        return redirect(url_for('mostrar_programas'))

    return render_template('editar.html', programa=programa)

# Ruta para eliminar un programa
@app.route('/eliminar_programa/<int:id>', methods=['POST'])
def eliminar_programa_ruta(id):
    eliminar_programa(id)
    flash('Programa eliminado exitosamente', 'success')
    return redirect(url_for('mostrar_programas'))


########################## rutas view tablas ################################


@app.route('/view')
def index_view():
    return render_template('views.html')

@app.route('/view1')
def view1():
    resultados = vista_facultades()
    return render_template('view1.html', resultados=resultados)

@app.route('/view2')
def view2():
    resultados = vista_programas()
    return render_template('view2.html', resultados=resultados)

@app.route('/view3')
def view3():
    resultados = vista_rannking_facultades()
    return render_template('view3.html', resultados=resultados)

if __name__ == '__main__':
    app.run(debug=True)

