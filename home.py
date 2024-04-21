
from drive_utils import file_management as fm
import streamlit as st
import requests

service = fm.authenticate_google_drive()
examens_folder_id = "14Xh6eAL6b_9VFOaBq62LIKAXDT4SGqMy"

st.title("Creador D'Examens")
st.header("Home")

subjects = fm.list_folders(service, examens_folder_id)
selected_subject = st.selectbox("Selecciona la asignatura", subjects)

# subject = st.selectbox("Subjects", get_all_subjects())

if selected_subject:
    st.subheader("Buscador")
    subject_id = fm.find_folder_id(service, selected_subject, folder_id="14Xh6eAL6b_9VFOaBq62LIKAXDT4SGqMy")

    if subject_id:
        tema = st.selectbox("Temas del ejercicio", fm.list_folders(service, subject_id))

        if tema:
            tema_id = fm.find_folder_id(service, tema, subject_id)

            # print(service, tema, subject_id)
            if tema_id:
                available_years = fm.list_folders(service, tema_id)
                selected_year = st.selectbox("Seleccionar año:", sorted(available_years))

                if selected_year:
                    selected_year_id = fm.find_folder_id(service, selected_year, tema_id)

                    if selected_year_id:
                        selected_month = st.selectbox("Seleccionar mes:",
                                                      sorted(fm.list_folders(service, selected_year_id)))

                        if selected_month:
                            selected_month_id = fm.find_folder_id(service, selected_month, selected_year_id)

                            if selected_month_id:
                                selected_serie = st.selectbox("Seleccionar serie:",
                                                              sorted(fm.list_folders(service, selected_month_id)))

                                if selected_serie:
                                    selected_serie_id = fm.find_folder_id(service, selected_serie, selected_month_id)

                                    if selected_serie_id:
                                        images = fm.list_files(service, selected_serie_id)

                                        for image in images:
                                            if "problem" in image['name']:
                                                problem_id = image['id']
                                                problem_url = f"https://drive.google.com/uc?export=view&id={problem_id}"
                                                response = requests.get(problem_url)

                                                if response.status_code == 200:
                                                    try:
                                                        st.image(response.content, caption=image['name'])
                                                    except Exception as e:
                                                        print("Error al cargar la imagen:", e)
                                                        st.error(
                                                            "No se pudo cargar la imagen. Verifique los permisos del archivo y el ID.")
                                                else:
                                                    print(
                                                        f"Fallo en la carga de la imagen, código de estado HTTP: {response.status_code}")
                                                    st.error(
                                                        f"Error al cargar la imagen desde Google Drive. Código de estado: {response.status_code}")

                                                # Buscar la solución correspondiente
                                                solution_name = image['name'].replace('problem', 'solution')
                                                solution_found = False

                                                for file in images:
                                                    if file['name'] == solution_name:
                                                        solution_url = f"https://drive.google.com/uc?export=view&id={file['id']}"
                                                        sol_response = requests.get(solution_url)

                                                        if sol_response.status_code == 200:
                                                            with st.expander("Ver Solución"):
                                                                st.image(sol_response.content,
                                                                         caption=f"Solución: {solution_name}")
                                                            solution_found = True
                                                            break
                                                        else:
                                                            print(
                                                                f"Error al cargar la imagen de solución con ID {file['id']}, código de estado HTTP: {sol_response.status_code}")

                                                if not solution_found:
                                                    st.warning(
                                                        "No se encontró archivo de solución correspondiente para: " +
                                                        image['name'])