import streamlit as st
import os
from fpdf import FPDF
from datetime import datetime
import random
from PIL import Image
import re

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Examen', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
def get_subjects():
    return os.listdir(subjects_folder)


def extract_id_from_path(path):
    # La expresión regular busca 'problem_' seguido de uno o más dígitos (\d+), antes del '.jpg'
    match = re.search(r'problem_(\d+).jpg', path)
    if match:
        return match.group(1)  # Retorna el grupo de dígitos que representa la ID
    else:
        return None



# Función para obtener todos los temas únicos
def get_unique_temas(subjects_folder):
    temas_set = set()  # Usamos un set para evitar duplicados

    # Recorremos ambos subdirectorios si existen
    for tipo in ["Problemes", "Questions"]:
        tipo_path = os.path.join(subjects_folder, tipo)

        # Verifica si el subdirectorio existe para evitar errores
        if os.path.exists(tipo_path):
            for tema in os.listdir(tipo_path):
                temas_set.add(tema)

    # Convertimos el set a una lista para poder ordenarla o manipularla más fácilmente
    temas_list = list(temas_set)
    temas_list.sort()  # Ordenamos la lista para mejorar la presentación
    return temas_list


def display_exercises_with_solutions(subjects_folder, subject, temas_questions, temas_problemas):
    st.header("Ejercicios y Soluciones")
    if not temas_questions and not temas_problemas:
        st.warning("No se han seleccionado temas para ejercicios o problemas.")
        return

    for temas, tipo in [(temas_questions, "Questions"), (temas_problemas, "Problemes")]:
        for tema in temas:
            tema_path = os.path.join(subjects_folder, subject, tipo, tema)

            if not os.path.exists(tema_path):
                st.error(f"No se encontró el directorio para el tema {tema}.")
                continue

            # Lista los años disponibles y elige uno al azar
            years = [y for y in os.listdir(tema_path) if os.path.isdir(os.path.join(tema_path, y))]
            if not years:
                st.error(f"No hay años disponibles para el tema {tema}.")
                continue
            random_year = random.choice(years)

            # Lista los meses disponibles y elige uno al azar
            year_path = os.path.join(tema_path, random_year)
            months = [m for m in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, m))]
            if not months:
                st.error(f"No hay meses disponibles para el año seleccionado en el tema {tema}.")
                continue
            random_month = random.choice(months)

            # Lista los problemas disponibles y elige uno al azar
            month_path = os.path.join(year_path, random_month)

            series = [s for s in os.listdir(month_path) if os.path.isdir(os.path.join(month_path, s))]
            if not series:
                st.error(f"No hay series disponibles para el mes seleccionado en el tema {tema}.")
                continue
            random_serie = random.choice(series)
            serie_path = os.path.join(month_path, random_serie)


            problems = [f for f in os.listdir(serie_path) if "problem" in f]
            if not problems:
                st.error(f"No hay problemas disponibles para el mes seleccionado en el tema {tema}.")
                continue
            random_problem = random.choice(problems)

            # Construye la ruta al problema y solución seleccionados
            problem_path = os.path.join(serie_path, random_problem)
            solution_path = problem_path.replace("problem", "solution")
            problem_id = extract_id_from_path(problem_path)
            print(problem_path)

            # Muestra el problema y la solución, si existen
            if os.path.exists(problem_path):
                st.image(problem_path, caption=f"Problema: {problem_id}")
            else:
                st.error(f"No se encontró el archivo del problema: {random_problem}")

            if os.path.exists(solution_path):
                with st.expander(f"Solución: {problem_id}"):
                    st.image(solution_path, caption=f"Solución: {problem_id}")
            else:
                st.warning(f"No se encontró archivo de solución correspondiente para: {random_problem}")


def add_content_to_pdf(pdf, subjects_folder, subject, temas_questions):
    left_margin, top_margin = 10, 10
    page_width = 190  # Ancho efectivo de la página ajustando los márgenes

    # Asegurarse de que haya al menos una página en el PDF
    if pdf.page_no() == 0:
        pdf.add_page()
    y_position = top_margin

    for tema in temas_questions:
        question_paths = []

        # Construir la lista completa de posibles preguntas
        tema_path = os.path.join(subjects_folder, subject, "Questions", tema)
        for root, dirs, files in os.walk(tema_path):
            for file in files:
                if "problem" in file:
                    question_paths.append(os.path.join(root, file))

        if question_paths:
            path = random.choice(question_paths)  # Selecciona aleatoriamente una pregunta del tema

            if os.path.exists(path):
                img = Image.open(path)
                img_width, img_height = img.size
                aspect_ratio = img_height / img_width
                new_height = page_width * aspect_ratio

                if (y_position + new_height) > (297 - top_margin):  # A4 page height - margin
                    pdf.add_page()
                    y_position = top_margin  # Restablecer la posición inicial en la nueva página

                pdf.image(path, x=left_margin, y=y_position, w=page_width)
                y_position += new_height + 5  # Actualizar posición Y para la siguiente imagen
        else:
            st.warning(f"No se encontraron preguntas para el tema: {tema}")

    return y_position

def add_problems_to_pdf(pdf, subjects_folder, subject, temas_problemas, start_y_position):
    left_margin, top_margin = 10, 10
    page_width = 190  # Ancho efectivo de la página ajustando los márgenes

    # Asegurarse de que haya al menos una página en el PDF
    if pdf.page_no() == 0:
        pdf.add_page()

    y_position = start_y_position

    for tema in temas_problemas:
        problem_paths = []

        # Construir la lista completa de posibles problemas
        tema_path = os.path.join(subjects_folder, subject, "Problemes", tema)
        for root, dirs, files in os.walk(tema_path):
            for file in files:
                if "problem" in file:
                    problem_paths.append(os.path.join(root, file))

        if problem_paths:
            path = random.choice(problem_paths)  # Selecciona aleatoriamente un problema del tema

            if os.path.exists(path):
                img = Image.open(path)
                img_width, img_height = img.size
                aspect_ratio = img_height / img_width
                new_height = page_width * aspect_ratio

                if (y_position + new_height) > (297 - top_margin):  # Altura de página A4 - margen
                    pdf.add_page()
                    y_position = top_margin  # Restablecer la posición inicial en la nueva página

                pdf.image(path, x=left_margin, y=y_position, w=page_width)
                y_position += new_height + 5  # Actualizar posición Y para la siguiente imagen
        else:
            st.warning(f"No se encontraron problemas para el tema: {tema}")

    return y_position


st.title("Creador de Exámenes")
subjects_folder = "examens"

subject = st.selectbox("Selecciona la asignatura", get_subjects())


# Suponiendo que los temas están organizados en subdirectorios
if subject:
    temas_list = get_unique_temas(os.path.join(subjects_folder, subject))
    #selected_temas = st.multiselect("Selecciona los temas",temas_list)
    q1, q2 = st.columns(2)
    p1, p2 = st.columns(2)

    st.subheader("Cuestiones")
    questions_count = st.number_input("Cantidad de cuestiones por tema", min_value=0, value=5)


    questiones_temas = st.multiselect("Temas de las cuestiones", temas_list)
    distribucion_q_temas = []

    with st.expander("Temas cuestiones"):
        for i in range(questions_count):
            tema = st.selectbox(f"Tema Question {i + 1}", questiones_temas)
            distribucion_q_temas.append(tema)
        print(distribucion_q_temas)


    st.subheader("Problemas")

    problems_count = st.number_input("Cantidad de problemas por tema", min_value=0, value=5)
    problemas_temas = st.multiselect("Temas de los problemas", temas_list)

    distribucion_p_temas = []
    with st.expander("Temas Problemas"):
        for i in range(problems_count):
            tema = st.selectbox(f"Tema Problema {i + 1}", problemas_temas)
            distribucion_p_temas.append(tema)

    # Ejemplo de cómo llamar a la función
    if st.button("Mostrar Ejercicios y Soluciones"):
        display_exercises_with_solutions(subjects_folder, subject, distribucion_q_temas, distribucion_p_temas)

    # if st.button("Crear Examen"):
    #     pdf = PDF(orientation='P', unit='mm', format='A4')
    #
    #     # Llama a la primera función y guarda la última posición y
    #     y_position_after_questions = add_content_to_pdf(pdf, subjects_folder, subject, distribucion_q_temas)
    #
    #     # Pasa esa posición y a la siguiente función para continuar añadiendo contenido
    #     add_problems_to_pdf(pdf, subjects_folder, subject, distribucion_p_temas, y_position_after_questions)
    #
    #     # Guardar y ofrecer el PDF para descarga
    #     pdf_file_path = "examen.pdf"
    #     pdf.output(pdf_file_path)
    #     with open(pdf_file_path, "rb") as pdf_file:
    #         st.download_button(label="Descargar Examen", data=pdf_file, file_name=pdf_file_path)