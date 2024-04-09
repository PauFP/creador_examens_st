import streamlit as st
import os
import re

subjects_folder = "examens"

def get_all_subjects():
    return os.listdir(subjects_folder)

st.header("Home")
subject = st.selectbox("Subjects", get_all_subjects())

if subject:
    st.subheader("Buscador")
    type = st.selectbox("Tipo", ["Problemes", "Questions"])

    if type:
        tema_path = os.path.join(subjects_folder, subject, type)
        temas = os.listdir(tema_path)

        temas_procesados = []
        for tema in temas:
            nombre_procesado = ' '.join(palabra.capitalize() for palabra in tema.split('-'))
            temas_procesados.append(nombre_procesado)

        selected_tema = st.selectbox("Temas", temas_procesados)

        if selected_tema:
            selected_tema_processed = '-'.join(palabra.lower() for palabra in selected_tema.split(' '))
            year_path = os.path.join(tema_path, selected_tema_processed)

            if os.path.exists(year_path):
                year = st.selectbox("Año", sorted(os.listdir(year_path)))

                if year:
                    mes_path = os.path.join(year_path, year)
                    mes = st.selectbox("Mes", sorted(os.listdir(mes_path)))

                    if mes:
                        serie_path = os.path.join(mes_path, mes.lower())
                        serie = st.selectbox("Serie (Opcional)", sorted(os.listdir(serie_path)))

                        if serie:
                            final_path = os.path.join(serie_path, serie)
                            files = os.listdir(final_path)

                            # Crear un diccionario para emparejar problemas y soluciones basado en el ID.
                            matched_files = {}
                            for file in files:
                                match = re.search(r'(problem|solution)_(\d+)', file)
                                if match:
                                    file_type, file_id = match.groups()
                                    if file_id not in matched_files:
                                        matched_files[file_id] = {'problem': None, 'solution': None}
                                    matched_files[file_id][file_type] = file

                            # Mostrar en pares: problema seguido de solución
                            for file_id in matched_files:
                                with st.container(border=True):
                                    pair = matched_files[file_id]
                                    if pair['problem']:
                                        st.image(os.path.join(final_path, pair['problem']), caption=pair['problem'])
                                    with st.expander("Solución"):
                                        if pair['solution']:
                                            st.image(os.path.join(final_path, pair['solution']), caption=pair['solution'])
