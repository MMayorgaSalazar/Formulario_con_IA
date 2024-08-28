import os
import re  # Importar la librería de expresiones regulares
from dotenv import load_dotenv
from mistralai import Mistral
from flask import Flask, render_template, request, send_file
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuración de Mistral
load_dotenv("key.env")
api_key = os.getenv("MISTRAL_API_KEY")
model = "mistral-large-latest"

client = Mistral(api_key=api_key)

# Configuración de Flask
app = Flask(__name__)

def clean_response(text):
    # Esta función eliminará **, ##, y otros caracteres especiales que no desees en el contenido.
    clean_text = re.sub(r'[\*\#]', '', text)
    return clean_text

@app.route('/')
def index():
    return render_template('form_test.html')

@app.route('/index')
def base():
    return render_template('index.html')

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    # Recibe los datos del formulario
    curso = request.form.get('curso')
    fecha_inicio = request.form.get('fecha_inicio')
    fecha_termino = request.form.get('fecha_termino')
    horario_inicio = request.form.get('inicio')
    horario_termino = request.form.get('termino')
    participantes = request.form.get('participantes')
    instructor = request.form.get('instructor')
    objetivo = request.form.get('objetivo')
    temario = request.form.get('temario')
    nivel = request.form.get('nivel')
    modalidad = request.form.get('modalidad')
    materiales = request.form.get('materiales')

    # Crear un mensaje para Mistral para generar el contenido estructurado
    prompt = (
        f"Genera el contenido para un documento PDF estructurado de la siguiente forma: \n"
        f"1.-Para la cebecera del documento menciona el nombre de{curso}, incorpora los dias que durara el curso contando desde {fecha_inicio} y que terminaran el {fecha_termino}, los dias mencionalos en formato dia-mes-año por ejemplo martes 18 de enero 2024 e indica que este iniciara a {horario_inicio} y finaliza a las {horario_termino}por ultimo indica que al instructor que la imparte es {instructor} "
        f"2. Para esta categoria genera un objetivo que pueda tener el curso en base a los descrito a continuacion {objetivo}\n\n"
        f"3. Genera una descrición que pueda tener el temario de {curso}, para ello considera generara: Temas principales, subtemas en base a {temario} y los contenidos deben ser de nivel {nivel}, ademas debes definir la duracion de cada uno es decir a que hora comienza y a que hora terminara dicho tema, para esto ultimo considera que el inicio del curso es el día {fecha_inicio} y que termina el {fecha_termino} cada dia empezara a las {horario_inicio} y te terminara a las {horario_termino}.\n"
        f"4. Modalidad del Curso:\n{modalidad}\n\n"
        f"6. Requerimientos: menciona los requerimientos que se requieran para poder participar en el curso, para ello considera que este tiene una modalidad {modalidad}\n\n"
        f"Proporcióname el contenido en un formato que pueda ser convertido en un PDF."
        f"Trata de que el documento final no sea superior a 3 paginas."
        f"considera incorporar algun metodo de separación por punto"
        f"omite comentarios adicionales como por ejemplo como hacerlo en formato pdf,Documento PDF:,Fin del Documento,---,Este contenido puede ser copiado y pegado en un editor de texto o en un software de creación de PDF para generar el documento final, Este contenido puede ser copiado y pegado en un editor de texto o en un software de creación de PDF para generar el documento final, Fin del documento."
    )

    # Solicitar a Mistral la generación del contenido estructurado
    response = client.chat.complete(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Obtener el contenido textual y limpiarlo
    content = response.choices[0].message.content
    clean_content = clean_response(content)  # Limpiar el contenido

    # Crear un archivo PDF en memoria usando el contenido generado
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Definir estilos personalizados
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        name="Header",
        fontSize=14,
        leading=16,
        spaceAfter=10,
        textColor=colors.black
    )
    subheader_style = ParagraphStyle(
        name="SubHeader",
        fontSize=12,
        leading=14,
        spaceAfter=8,
        textColor=colors.black
    )
    normal_style = ParagraphStyle(
        name="Normal",
        fontSize=12,
        leading=16,
        spaceAfter=6
    )

    # Añadir contenido al PDF con estilos personalizados
    for line in clean_content.splitlines():
        if line.startswith("1. Cabecera:") or line.startswith("2. ") or line.startswith("3. ") or line.startswith("4. ") or line.startswith("5. ") or line.startswith("6. "):
            elements.append(Paragraph(line, header_style))
        elif line.startswith("- "):
            elements.append(Paragraph(line, subheader_style))
        else:
            elements.append(Paragraph(line, normal_style))
        elements.append(Spacer(1, 12))  # Añadir espacio entre párrafos

    doc.build(elements)

    buffer.seek(0)

    # Guardar el PDF en un archivo en la carpeta 'static/temp'
    pdf_file_path = os.path.join('static', 'temp', 'curso_inscripcion.pdf')
    os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)

    with open(pdf_file_path, 'wb') as f:
        f.write(buffer.getvalue())

    # Renderizar la vista de previa del PDF
    return render_template('preview.html', pdf_file_path=pdf_file_path)

@app.route('/download_pdf')
def download_pdf():
    pdf_file_path = os.path.join('static', 'temp', 'curso_inscripcion.pdf')
    return send_file(pdf_file_path, as_attachment=True, download_name='curso_inscripcion.pdf')

@app.route('/evaluate_pdf', methods=['POST'])
def evaluate_pdf():
    # Leer el contenido del PDF
    pdf_file_path = os.path.join('static', 'temp', 'curso_inscripcion.pdf')
    
    with open(pdf_file_path, 'rb') as f:
        pdf_content = f.read()

    # Crear un prompt para evaluar cada sección del PDF
    prompt = (
        "Evalúa cada sección del siguiente PDF en una escala del 1 al 10 y proporciona comentarios breves sobre posibles correcciones que se puedan realizar:\n\n"
        "Evaluacion formulario:\n"
        "1. Cabecera:\n"
        "- Fechas del curso: ¿Qué tan precisa es la fecha? ¿Alguna de las fechas establecidas es un dia feriado?\n"
        "- Horario de inicio y término: ¿Son adecuados los horarios?\n"
        "- Nombre del Instructor:¿Se debe dar más informacion sobre el instructor?\n\n"
        "2. Objetivo del Curso: ¿Qué tan claro y alcanzable es el objetivo durante el palzo establecido?\n\n"
        "3. Descripción del Temario: ¿Qué tan completo y claro es el temario?\n\n"
        "4. Nivel del Curso: ¿El nivel definido para el temario va acorde a la descripcion del temario propuesta?\n\n"
        "5. Modalidad del Curso: ¿Es adecuada la modalidad para presentar los contenidos?\n\n"
        "6. Requerimientos: ¿Son suficientes los requerimientos considerando el nivel del curso y adecuados los materiales?\n\n"
        "Proporcióname la evaluación en un formato estructurado para su presentación."
        f"y considera colocar la evaluacions según tu opinion"
        f"Comienza tu respuesta con:  evaluacion del documento usando una escala del 1 al 10, considere 1 como minimo y 10 como maximo.\n"
        f"proporciona una conclusion"
        f"Considera que tu respuesta sea en forma de codigo y que este ira dentro de un div en html y añadele estilos dentro del mismo codigo para que sea grato a la vista del usuario, considera iniciar tu respuesta directamente con el codigo"
        f"omite comentarios como por ejemplo ``` Este código HTML proporciona una evaluación estructurada del documento, con estilos incluidos para una presentación clara y organizada,```html "
    )

    # Solicitar a Mistral la evaluación del contenido del PDF
    response = client.chat.complete(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Obtener la evaluación y limpiarla
    evaluation_content = response.choices[0].message.content
    clean_evaluation_content = clean_response(evaluation_content)  # Limpiar la evaluación

    # Renderizar la vista de evaluación
    return render_template('evaluacion.html', evaluation_content=clean_evaluation_content)


@app.route('/preview_pdf', methods=['GET'])
def preview_pdf():
    # Asegúrate de que el PDF ya ha sido generado
    pdf_file_path = os.path.join('static', 'temp', 'curso_inscripcion.pdf')
    if not os.path.isfile(pdf_file_path):
        return "El archivo PDF no ha sido generado aún.", 404
    
    return render_template('preview.html', pdf_file_path=pdf_file_path)


if __name__ == '__main__':
    app.run(debug=True)
