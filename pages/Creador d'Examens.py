import streamlit as st
from google.oauth2 import service_account
import requests
import random
import json
from scripts.project.drive_utils import file_management as fm


# subjects_folder, subject
def display_exercises_with_solutions(service, temas_problemas, subject_folder_id):
    st.header("Ejercicios y Soluciones")
    if not temas_problemas:
        st.warning("No se han seleccionado temas para ejercicios o problemas.")
        return

    for tema in temas_problemas:
        # tema_folder_id = find_folder_id(service, tema, tema_folder_id)
        temas_id = fm.find_folder_id(service, tema, subject_folder_id)
        if not tema_folder_id:
            st.error(f"No se encontró el directorio para el tema {tema}.")
            continue

        years = fm.list_folders(service, temas_id)
        if not years:
            st.error(f"No hay años disponibles para el tema {tema}.")
            continue
        random_year = random.choice(years)
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

        random_problem = random.choice(problems)
        random_problem_id = None

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
                st.image(response.content,
                         caption=f"Año: {random_year}, Mes: {random_month}, Serie: {random_serie}")  # Elimina el doble llamado a st.image
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
        solution_found = False

        # Buscar la solución en la lista de problemas
        for file in problems:
            if file['name'] == solution_name:
                solution_url = f"https://drive.google.com/uc?export=view&id={file['id']}"
                sol_response = requests.get(solution_url)

                # Mostrar la solución usando un expander de Streamlit
                with st.expander("Ver Solución"):
                    st.image(sol_response.content, caption=f"Solución: {solution_name}")
                solution_found = True
                break

        # Manejar el caso en que no se encuentra la solución correspondiente
        if not solution_found:
            st.warning("No se encontró archivo de solución correspondiente.")


if fm.CREDENTIALS_JSON:
    credentials_dict = json.loads(fm.CREDENTIALS_JSON)
    CREDENTIALS = service_account.Credentials.from_service_account_info(credentials_dict)

st.title("Creador de Exámenes")
# subjects_folder = r"examens"
service = fm.authenticate_google_drive()
examens_folder_id = "14Xh6eAL6b_9VFOaBq62LIKAXDT4SGqMy"

subjects = fm.list_folders(service, examens_folder_id)
selected_subject = st.selectbox("Selecciona la asignatura", subjects)
if selected_subject:
    tema_folder_id = fm.find_folder_id(service, selected_subject, folder_id="14Xh6eAL6b_9VFOaBq62LIKAXDT4SGqMy")

    temas_list = fm.list_folders(service, tema_folder_id)

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
