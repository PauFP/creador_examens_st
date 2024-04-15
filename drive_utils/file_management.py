from google.oauth2 import service_account
from googleapiclient.discovery import build
import streamlit as st
import os
import re
import json
import requests

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_JSON = st.secrets["secrets"]["GOOGLE_APPLICATION_CREDENTIALS_JSON"]

def authenticate_google_drive(credentials_env=None):
        """
        Autentica al usuario y crea un cliente de servicio Google Drive.

        :param credentials_env: Diccionario que contiene las credenciales de la cuenta de servicio.
        """
        if credentials_env is None:
            # Cargar las credenciales desde una variable de entorno si no se proporcionan directamente
            credentials_raw = st.secrets["secrets"]['GOOGLE_APPLICATION_CREDENTIALS_JSON']
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

    # Verifica si el subdirectorio existe para evitar errores
    if os.path.exists(subjects_folder):
        for tema in os.listdir(subjects_folder):
            temas_set.add(tema)

    # Convertimos el set a una lista para poder ordenarla o manipularla más fácilmente
    temas_list = list(temas_set)
    temas_list.sort()  # Ordenamos la lista para mejorar la presentación
    return temas_list



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


def find_folder_id(service, folder_name, folder_id):
    """Busca una carpeta por nombre y devuelve su ID."""
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{folder_id}' in parents and trashed=false"
    response = service.files().list(q=query, fields='files(id, name)').execute()
    folders = response.get('files', [])
    if folders:
        return folders[0]['id']  # devuelve el ID de la primera carpeta encontrada
    else:
        return None  # devuelve None si no se encuentra la carpeta