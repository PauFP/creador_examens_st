import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

import requests
import re
import random
import json

SCOPES = ['https://www.googleapis.com/auth/drive']
credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')


def authenticate_google_drive(credentials_env=None):
        """
        Autentica al usuario y crea un cliente de servicio Google Drive.

        :param credentials_env: Diccionario que contiene las credenciales de la cuenta de servicio.
        """
        if credentials_env is None:
            # Cargar las credenciales desde una variable de entorno si no se proporcionan directamente
            credentials_raw = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            if credentials_raw:
                credentials_env = json.loads(credentials_raw)
            else:
                raise ValueError("No se proporcionaron credenciales y no se encontró una variable de entorno adecuada.")

        # Crear credenciales a partir del diccionario
        credentials = service_account.Credentials.from_service_account_info(credentials_env)
        service = build('drive', 'v3', credentials=credentials)
        return service

def find_folder_by_path(service, path_parts, parent_id='root'):
    """ Busca recursivamente una carpeta por su ruta a partir de un ID de carpeta padre. """
    current_id = parent_id
    for part in path_parts:
        query = f"mimeType='application/vnd.google-apps.folder' and name='{part}' and '{current_id}' in parents and trashed=false"
        response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = response.get('files', [])
        if not items:
            return None  # Carpeta no encontrada
        current_id = items[0]['id']
    return current_id

def find_files_in_folder(service, folder_id):
    """ Busca archivos en la carpeta especificada por folder_id. """
    query = f"'{folder_id}' in parents and trashed=false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name, mimeType)').execute()
    return response.get('files', [])


def get_image_drive(service, path):
    """ Muestra la imagen especificada por la ruta completa en Google Drive. """
    # Reemplazar las barras invertidas por barras normales para evitar errores en la división
    path = path.replace('\\', '/')
    path_parts = path.split('/')

    # La parte final de la ruta es el nombre del archivo
    file_name = path_parts[-1]
    # Todo lo demás es la ruta de la carpeta
    folder_path_parts = path_parts[:-1]

    folder_id = find_folder_by_path(service, folder_path_parts)
    response_image = None  # Inicializar response_image como None

    if folder_id:
        files = find_files_in_folder(service, folder_id)
        for file in files:
            if file['name'] == file_name:  # Buscar el archivo específico por nombre
                file_id = file['id']
                url = f"https://drive.google.com/uc?export=view&id={file_id}"
                response_image = requests.get(url)
                break  # Romper el bucle una vez que se encuentra el archivo
        else:
            # Esta sección de else se asocia con el for, se ejecuta si no se rompe el bucle
            st.error(f"No se encontró el archivo: {file_name}")
    else:
        st.error("No se encontró la carpeta especificada por la ruta.")

    return response_image


# class PDF(FPDF):
#     def header(self):
#         self.set_font('Arial', 'B', 12)
#         self.cell(0, 10, 'Examen', 0, 1, 'C')
#
#     def footer(self):
#         self.set_y(-15)
#         self.set_font('Arial', 'I', 8)
#         self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
# def get_subjects():
#     return os.listdir(subjects_folder)


def extract_id_from_path(path):
    # La expresión regular busca 'problem_' seguido de uno o más dígitos (\d+), antes del '.jpg'
    match = re.search(r'problem_(\d+).jpg', path)
    if match:
        return match.group(1)  # Retorna el grupo de dígitos que representa la ID
    else:
        return None



# Función para obtener todos los temas únicos
def get_unique_temas_tecno(subjects_folder):
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

def get_unique_temas(subjects_folder):
    temas_set = set()  # Usamos un set para evitar duplicados

    # Recorremos ambos subdirectorios si existen


    # Verifica si el subdirectorio existe para evitar errores
    if os.path.exists(subjects_folder):
        for tema in os.listdir(subjects_folder):
            temas_set.add(tema)

    # Convertimos el set a una lista para poder ordenarla o manipularla más fácilmente
    temas_list = list(temas_set)
    temas_list.sort()  # Ordenamos la lista para mejorar la presentación
    return temas_list

# def display_exercises_with_solutions_tecno(subjects_folder, subject, temas_questions, temas_problemas):
#     st.header("Ejercicios y Soluciones")
#     if not temas_questions and not temas_problemas:
#         st.warning("No se han seleccionado temas para ejercicios o problemas.")
#         return
#
#     for temas, tipo in [(temas_questions, "Questions"), (temas_problemas, "Problemes")]:
#         for tema in temas:
#             tema_path = os.path.join(subjects_folder, subject, tipo, tema)
#             print("TEANA" + tema_path)
#
#             if not os.path.exists(tema_path):
#                 st.error(f"No se encontró el directorio para el tema {tema}.")
#                 continue
#
#             # Lista los años disponibles y elige uno al azar
#             years = [y for y in os.listdir(tema_path) if os.path.isdir(os.path.join(tema_path, y))]
#             if not years:
#                 st.error(f"No hay años disponibles para el tema {tema}.")
#                 continue
#             random_year = random.choice(years)
#
#             # Lista los meses disponibles y elige uno al azar
#             year_path = os.path.join(tema_path, random_year)
#             months = [m for m in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, m))]
#             if not months:
#                 st.error(f"No hay meses disponibles para el año seleccionado en el tema {tema}.")
#                 continue
#             random_month = random.choice(months)
#
#             # Lista los problemas disponibles y elige uno al azar
#             month_path = os.path.join(year_path, random_month)
#
#             series = [s for s in os.listdir(month_path) if os.path.isdir(os.path.join(month_path, s))]
#             if not series:
#                 st.error(f"No hay series disponibles para el mes seleccionado en el tema {tema}.")
#                 continue
#             random_serie = random.choice(series)
#             serie_path = os.path.join(month_path, random_serie)
#
#
#             problems = [f for f in os.listdir(serie_path) if "problem" in f]
#             if not problems:
#                 st.error(f"No hay problemas disponibles para el mes seleccionado en el tema {tema}.")
#                 continue
#             random_problem = random.choice(problems)
#
#             # Construye la ruta al problema y solución seleccionados
#             problem_path = os.path.join(serie_path, random_problem)
#             solution_path = problem_path.replace("problem", "solution")
#             problem_id = extract_id_from_path(problem_path)
#             print("HOUSTON"+problem_path)
#
#             # Muestra el problema y la solución, si existen
#             if os.path.exists(problem_path):
#                 st.image(problem_path, caption=f"Problema: {problem_id}")
#             else:
#                 st.error(f"No se encontró el archivo del problema: {random_problem}")
#
#             if os.path.exists(solution_path):
#                 with st.expander(f"Solución: {problem_id}"):
#                     st.image(solution_path, caption=f"Solución: {problem_id}")
#             else:
#                 st.warning(f"No se encontró archivo de solución correspondiente para: {random_problem}")

def list_folders(service, parent_id):
    folders_list = []
    # """Lista todas las carpetas dentro de una carpeta de Google Drive usando una cuenta de servicio."""
    query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    folder_names = [folder['name'] for folder in folders]


    return folder_names

def list_files(service, folder_id):
    """Lista todos los archivos dentro de una carpeta de Google Drive."""
    query = f"'{folder_id}' in parents and trashed = false"
    response = service.files().list(q=query, fields='files(id, name)').execute()
    return response.get('files', [])

# def find_folder_id(service, name, parent_id='root'):
#     """Encuentra el ID de una carpeta por nombre dentro de una carpeta específica."""
#     folders = list_folders(service, parent_id)
#     for folder in folders:
#         if folder['name'] == name:
#             return folder['id']
#     return None

def find_folder_id(service, folder_name, folder_id):
    """Busca una carpeta por nombre y devuelve su ID."""
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{folder_id}' in parents and trashed=false"
    response = service.files().list(q=query, fields='files(id, name)').execute()
    folders = response.get('files', [])
    if folders:
        return folders[0]['id']  # devuelve el ID de la primera carpeta encontrada
    else:
        return None  # devuelve None si no se encuentra la carpeta
# subjects_folder, subject
def display_exercises_with_solutions(service, temas_problemas, subject_folder_id):
    st.header("Ejercicios y Soluciones")
    if not temas_problemas:
        st.warning("No se han seleccionado temas para ejercicios o problemas.")
        return

    # subject_folder_id = find_folder_id(service, subject)
    # print(subject_folder_id)
    # if not subject_folder_id:
    #     st.error("No se encontró el directorio del sujeto.")
    #     return

    for tema in temas_problemas:
        # tema_folder_id = find_folder_id(service, tema, tema_folder_id)
        temas_id = find_folder_id(service, tema, subject_folder_id)
        if not tema_folder_id:
            st.error(f"No se encontró el directorio para el tema {tema}.")
            continue

        years = list_folders(service, temas_id)
        if not years:
            st.error(f"No hay años disponibles para el tema {tema}.")
            continue
        random_year = random.choice(years)
        random_year_id = find_folder_id(service, random_year, temas_id)
        months = list_folders(service, random_year_id)
        if not months:
            st.error(f"No hay meses disponibles para el año seleccionado: {random_year['name']}.")
            continue
        random_month = random.choice(months)

        random_month_id = find_folder_id(service, random_month, random_year_id)
        series = list_folders(service, random_month_id)

        if not series:
            st.error(f"No hay series disponibles para el mes seleccionado: {random_month['name']}.")
            continue
        random_serie = random.choice(series)
        random_serie_id = find_folder_id(service, random_serie, random_month_id)

        problems = list_files(service, random_serie_id)
        if not problems:
            st.error(f"No hay problemas disponibles en la serie seleccionada: {random_serie['name']}.")
            continue


        random_problem = random.choice(problems)
        random_problem_id = None

        print(random_problem)
        if "solution" in random_problem['name']:
            # Cambiar 'solution' por 'problem' en el nombre para encontrar el problema correspondiente
            problem_name = random_problem['name'].replace('solution', 'problem')
            # Buscar el problema correspondiente
            problem_item = next((item for item in problems if item['name'] == problem_name), None)
            if problem_item:
                random_problem_id = problem_item['id']
            else:
                print("Problema correspondiente no encontrado.")
        else:
            random_problem_id = random_problem['id']

        problem_url = f"https://drive.google.com/uc?export=view&id={random_problem_id}"
        response = requests.get(problem_url)

        if response.status_code == 200:
            try:
                # Intentar mostrar la imagen si la respuesta es exitosa
                st.image(response.content, caption=f"Año: {random_year}, Mes: {random_month}, Serie: {random_serie}")  # Elimina el doble llamado a st.image
                print("Imagen cargada correctamente.")

            except Exception as e:

                # Manejar el caso en que el contenido no pueda ser interpretado como una imagen
                print("Error al cargar la imagen:", e)
                st.error("No se pudo cargar la imagen. Verifique los permisos del archivo y el ID.")
        else:
            # Manejar respuestas fallidas
            print(f"Fallo en la carga de la imagen, código de estado HTTP: {response.status_code}")
            st.error(f"Error al cargar la imagen desde Google Drive. Código de estado: {response.status_code}")
        #
        # # Supongamos que las soluciones están nombradas con el prefijo 'solution' en lugar de 'problem'
        # Determinar el nombre de la solución correspondiente cambiando 'problem' por 'solution'
        solution_name = random_problem['name'].replace('problem', 'solution')
        print(solution_name)
        solution_found = False

        # Buscar la solución en la lista de problemas
        for file in problems:
            print(file)
            if file['name'] == solution_name:
                solution_url = f"https://drive.google.com/uc?export=view&id={file['id']}"
                print(solution_url)
                sol_response = requests.get(solution_url)
                print(sol_response.headers)

                # Mostrar la solución usando un expander de Streamlit
                with st.expander("Ver Solución"):
                    st.image(sol_response.content, caption=f"Solución: {solution_name}")
                solution_found = True
                break

        # Manejar el caso en que no se encuentra la solución correspondiente
        if not solution_found:
            st.warning("No se encontró archivo de solución correspondiente.")

# Reemplaza 'service', 'subjects_folder', 'subject', y 'temas_problemas' con tus valores apropiados para probar.


# def add_content_to_pdf(pdf, subjects_folder, subject, temas_questions):
#     left_margin, top_margin = 10, 10
#     page_width = 190  # Ancho efectivo de la página ajustando los márgenes
#
#     # Asegurarse de que haya al menos una página en el PDF
#     if pdf.page_no() == 0:
#         pdf.add_page()
#     y_position = top_margin
#
#     for tema in temas_questions:
#         question_paths = []
#
#         # Construir la lista completa de posibles preguntas
#         tema_path = os.path.join(subjects_folder, subject, "Questions", tema)
#         for root, dirs, files in os.walk(tema_path):
#             for file in files:
#                 if "problem" in file:
#                     question_paths.append(os.path.join(root, file))
#
#         if question_paths:
#             path = random.choice(question_paths)  # Selecciona aleatoriamente una pregunta del tema
#
#             if os.path.exists(path):
#                 img = Image.open(path)
#                 img_width, img_height = img.size
#                 aspect_ratio = img_height / img_width
#                 new_height = page_width * aspect_ratio
#
#                 if (y_position + new_height) > (297 - top_margin):  # A4 page height - margin
#                     pdf.add_page()
#                     y_position = top_margin  # Restablecer la posición inicial en la nueva página
#
#                 pdf.image(path, x=left_margin, y=y_position, w=page_width)
#                 y_position += new_height + 5  # Actualizar posición Y para la siguiente imagen
#         else:
#             st.warning(f"No se encontraron preguntas para el tema: {tema}")
#
#     return y_position

# def add_problems_to_pdf(pdf, subjects_folder, subject, temas_problemas, start_y_position):
#     left_margin, top_margin = 10, 10
#     page_width = 190  # Ancho efectivo de la página ajustando los márgenes
#
#     # Asegurarse de que haya al menos una página en el PDF
#     if pdf.page_no() == 0:
#         pdf.add_page()
#
#     y_position = start_y_position
#
#     for tema in temas_problemas:
#         problem_paths = []
#
#         # Construir la lista completa de posibles problemas
#         tema_path = os.path.join(subjects_folder, subject, "Problemes", tema)
#         for root, dirs, files in os.walk(tema_path):
#             for file in files:
#                 if "problem" in file:
#                     problem_paths.append(os.path.join(root, file))
#
#         if problem_paths:
#             path = random.choice(problem_paths)  # Selecciona aleatoriamente un problema del tema
#
#             if os.path.exists(path):
#                 img = Image.open(path)
#                 img_width, img_height = img.size
#                 aspect_ratio = img_height / img_width
#                 new_height = page_width * aspect_ratio
#
#                 if (y_position + new_height) > (297 - top_margin):  # Altura de página A4 - margen
#                     pdf.add_page()
#                     y_position = top_margin  # Restablecer la posición inicial en la nueva página
#
#                 pdf.image(path, x=left_margin, y=y_position, w=page_width)
#                 y_position += new_height + 5  # Actualizar posición Y para la siguiente imagen
#         else:
#             st.warning(f"No se encontraron problemas para el tema: {tema}")
#
#     return y_position

if credentials_json:
    credentials_dict = json.loads(credentials_json)
    CREDENTIALS = service_account.Credentials.from_service_account_info(credentials_dict)

st.title("Creador de Exámenes")
# subjects_folder = r"examens"
service = authenticate_google_drive()
examens_folder_id = "14Xh6eAL6b_9VFOaBq62LIKAXDT4SGqMy"

subjects = list_folders(service,examens_folder_id)
selected_subject = st.selectbox("Selecciona la asignatura", subjects)
if selected_subject:
    tema_folder_id = find_folder_id(service, selected_subject, folder_id="14Xh6eAL6b_9VFOaBq62LIKAXDT4SGqMy")

    temas_list = list_folders(service, tema_folder_id)
    #temas_list = get_unique_temas(os.path.join(examens_folder_id, selected_subject))
    # selected_temas = st.multiselect("Selecciona los temas",temas_list)
    q1, q2 = st.columns(2)
    p1, p2 = st.columns(2)

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
        display_exercises_with_solutions(service, distribucion_p_temas, tema_folder_id)

# Suponiendo que los temas están organizados en subdirectorios
# if selected_subject == "Tecnologia":
#     temas_list = get_unique_temas_tecno(os.path.join(subjects_folder, subject))
#     #selected_temas = st.multiselect("Selecciona los temas",temas_list)
#     q1, q2 = st.columns(2)
#     p1, p2 = st.columns(2)
#
#     st.subheader("Cuestiones")
#     questions_count = st.number_input("Cantidad de cuestiones por tema", min_value=0, value=5)
#
#
#     questiones_temas = st.multiselect("Temas de las cuestiones", temas_list)
#     distribucion_q_temas = []
#
#     with st.expander("Temas cuestiones"):
#         for i in range(questions_count):
#             tema = st.selectbox(f"Tema Question {i + 1}", questiones_temas)
#             distribucion_q_temas.append(tema)
#         print(distribucion_q_temas)
#
#
#     st.subheader("Problemas")
#
#     problems_count = st.number_input("Cantidad de problemas por tema", min_value=0, value=5, key="tecno")
#     problemas_temas = st.multiselect("Temas de los problemas", temas_list)
#
#     distribucion_p_temas = []
#     with st.expander("Temas Problemas"):
#         for i in range(problems_count):
#             tema = st.selectbox(f"Tema Problema {i + 1}", problemas_temas)
#             distribucion_p_temas.append(tema)
#
#     # Ejemplo de cómo llamar a la función
#     if st.button("Mostrar Ejercicios y Soluciones", key="tecno_btn"):
#         display_exercises_with_solutions_tecno(subjects_folder, subject, distribucion_q_temas, distribucion_p_temas)

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