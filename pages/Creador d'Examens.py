import streamlit as st
from google.oauth2 import service_account
import requests
import random
import json
from fpdf import FPDF
from drive_utils import file_management as fm
from collections import Counter
import tempfile
import os
from PIL import Image
from io import BytesIO

class PDF(FPDF):
    def __init__(self, subject_title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject_title = subject_title

    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'Examen de {self.subject_title}', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page %s' % self.page_no(), 0, 0, 'C')

    def add_image(self, image_path, title):
        self.add_page()
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.image(image_path, x=10, y=30, w=180)

def generate_pdf(problems_info, subject_title):
    pdf = PDF(subject_title)

    for problem in problems_info:
        # Añadir el problema
        problem_title = f"Problema - Año: {problem['year_name']}, Mes: {problem['month_name']}, Serie: {problem['serie_name']}"
        problem_url = f"https://drive.google.com/uc?export=view&id={problem['prob_id']}"
        response = requests.get(problem_url)
        if response.status_code == 200:
            try:
                image = Image.open(BytesIO(response.content))
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmpfile:
                    image.save(tmpfile, format='JPEG')
                    tmpfile_path = tmpfile.name
                    pdf.add_image(tmpfile_path, problem_title)
                    os.unlink(tmpfile_path)  # Eliminar la imagen temporal después de agregarla al PDF
            except Exception as e:
                print("Error al procesar la imagen del problema:", e)
        else:
            print(f"Fallo en la carga de la imagen del problema, código de estado HTTP: {response.status_code}")

        # Añadir la solución
        solution_title = f"Solución - Año: {problem['year_name']}, Mes: {problem['month_name']}, Serie: {problem['serie_name']}"
        solution_url = f"https://drive.google.com/uc?export=view&id={problem['sol_id']}"
        response = requests.get(solution_url)
        if response.status_code == 200:
            try:
                image = Image.open(BytesIO(response.content))
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmpfile:
                    image.save(tmpfile, format='JPEG')
                    tmpfile_path = tmpfile.name
                    pdf.add_image(tmpfile_path, solution_title)
                    os.unlink(tmpfile_path)  # Eliminar la imagen temporal después de agregarla al PDF
            except Exception as e:
                print("Error al procesar la imagen de la solución:", e)
        else:
            print(f"Fallo en la carga de la imagen de la solución, código de estado HTTP: {response.status_code}")

    return pdf

def display_problems_and_solutions(service, temas_problemas, subject_folder_id, filtered_years):
    st.header("Ejercicios y Soluciones")
    all_problems_info = []  # Lista para almacenar la información de todos los problemas

    if not temas_problemas:
        st.warning("No se han seleccionado temas para ejercicios o problemas.")
        return

    for tema in temas_problemas:
        temas_id = fm.find_folder_id(service, tema, subject_folder_id)
        if not temas_id:
            st.error(f"No se encontró el directorio para el tema {tema}.")
            continue

        if "Todos" in filtered_years or not filtered_years:
            years = fm.list_folders(service, temas_id)
            if years:
                random_year = random.choice(years)
            else:
                random_year = None
        else:
            years = filtered_years
            random_filtered_year = random.choice(filtered_years)
            random_year = random_filtered_year

        if not years:
            st.error(f"No hay años disponibles para el tema {tema}.")
            continue

        random_year_id = fm.find_folder_id(service, random_year, temas_id)
        months = fm.list_folders(service, random_year_id)
        if not months:
            st.error(f"No hay meses disponibles para el año seleccionado: {random_year['name']}.")
            continue
        random_month = random.choice(months)

        random_month_id = fm.find_folder_id(service, random_month, random_year_id)
        series = fm.list_folders(service, random_month_id)

        if not series:
            st.error(f"No hay series disponibles para el mes seleccionado: {random_month['name']}.")
            continue
        random_serie = random.choice(series)
        random_serie_id = fm.find_folder_id(service, random_serie, random_month_id)

        problems = fm.list_files(service, random_serie_id)
        if not problems:
            st.error(f"No hay problemas disponibles en la serie seleccionada: {random_serie['name']}.")
            continue
        random_problem_id_list = []
        random_problem = random.choice(problems)
        random_problem_id = None
        solution_id = None

        if "solution" in random_problem['name']:
            problem_name = random_problem['name'].replace('solution', 'problem')
            problem_item = next((item for item in problems if item['name'] == problem_name), None)
            if problem_item:
                random_problem_id = problem_item['id']
            solution_id = random_problem['id']
        else:
            random_problem_id = random_problem['id']
            solution_name = random_problem['name'].replace('problem', 'solution')
            solution_item = next((item for item in problems if item['name'] == solution_name), None)
            if solution_item:
                solution_id = solution_item['id']

        random_problem_id_list.append(random_problem_id)
        problem_info = {
            "prob_id": random_problem_id,
            "sol_id": solution_id,
            "year_name": random_year,
            "month_name": random_month,
            "serie_name": random_serie,
            "tema_id": temas_id,
            "name": random_problem['name']
        }

        all_problems_info.append(problem_info)  # Agregar info del problema a la lista

        problem_url = f"https://drive.google.com/uc?export=view&id={random_problem_id}"
        response = requests.get(problem_url)

        if response.status_code == 200:
            try:
                st.image(response.content,
                         caption=f"Año: {random_year}, Mes: {random_month}, Serie: {random_serie}")
            except Exception as e:
                print("Error al cargar la imagen:", e)
                st.error("No se pudo cargar la imagen. Verifique los permisos del archivo y el ID.")
        else:
            print(f"Fallo en la carga de la imagen, código de estado HTTP: {response.status_code}")
            st.error(f"Error al cargar la imagen desde Google Drive. Código de estado: {response.status_code}")

        solution_name = random_problem['name'].replace('problem', 'solution')
        solution_found = False

        for file in problems:
            if file['name'] == solution_name:
                solution_url = f"https://drive.google.com/uc?export=view&id={file['id']}"
                sol_response = requests.get(solution_url)

                with st.expander("Ver Solución"):
                    st.image(sol_response.content, caption=f"Solución: {solution_name}")
                solution_found = True
                break

        if not solution_found:
            st.warning("No se encontró archivo de solución correspondiente.")

    return all_problems_info

if fm.CREDENTIALS_JSON:
    credentials_dict = json.loads(fm.CREDENTIALS_JSON)
    CREDENTIALS = service_account.Credentials.from_service_account_info(credentials_dict)

st.title("Creador de Exámenes")
service = fm.authenticate_google_drive()
examens_folder_id = "14Xh6eAL6b_9VFOaBq62LIKAXDT4SGqMy"

subjects = fm.list_folders(service, examens_folder_id)
selected_subject = st.selectbox("Selecciona la asignatura", subjects)
if selected_subject:
    tema_folder_id = fm.find_folder_id(service, selected_subject, folder_id="14Xh6eAL6b_9VFOaBq62LIKAXDT4SGqMy")
    if selected_subject == "Tecnologia":
        tipo = st.selectbox("Tipo", ["Problemes", "Questions"])
        if tipo == "Problemes":
            tema_folder_id = "1q99OL4r6HkcPPoirDm2ipa4B7Gz_zm6q"
        else:
            tema_folder_id = "1AN9VXrQpOywlL3VjRKKmD5YiUkValeOl"
    temas_list = fm.list_folders(service, tema_folder_id)

    q1, q2 = st.columns(2)
    p1, p2 = st.columns(2)

    st.subheader("Problemas")

    problems_count = st.number_input("Cantidad de problemas por tema", min_value=0, value=5)
    problemas_temas = st.multiselect("Temas de los problemas", temas_list)
    filtered_year = []
    if problemas_temas:
        temas_id = fm.find_folder_id(service, problemas_temas[0], tema_folder_id)
        years = fm.list_folders(service, temas_id)
        filtered_year = st.multiselect("Filtrar por años: ", ["Todos"]+sorted(years))

    distribucion_p_temas = []
    with st.expander("Temas Problemas"):
        for i in range(problems_count):
            tema = st.selectbox(f"Tema Problema {i + 1}", problemas_temas)
            distribucion_p_temas.append(tema)

    if st.button("Mostrar Ejercicios y Soluciones"):
        all_problems_info = display_problems_and_solutions(service, distribucion_p_temas, tema_folder_id, filtered_year)
        st.session_state['all_problems_info'] = all_problems_info

    if 'all_problems_info' in st.session_state and st.session_state['all_problems_info']:
        if st.button("Crear Examen"):
            pdf = generate_pdf(st.session_state['all_problems_info'], selected_subject)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                pdf_output_path = tmpfile.name
                pdf.output(pdf_output_path)

            with open(pdf_output_path, "rb") as pdf_file:
                st.download_button(
                    label="Descargar Examen en PDF",
                    data=pdf_file,
                    file_name="examen.pdf",
                    mime="application/pdf"
                )
