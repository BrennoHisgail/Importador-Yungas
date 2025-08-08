# drive_utils.py

"""Módulo de utilitários para interagir com a API do Google Drive v3."""

import os
import logging
import io
import time
import re
import hashlib
from typing import List, Optional, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaIoBaseDownload

# --- Module Constants ---
SCOPES: List[str] = ['https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_PATH: str = 'credentials/credentials.json'
TOKEN_PATH: str = 'credentials/token.json'

# --- Download Policy Configuration ---
DOWNLOAD_RETRIES: int = 3
DOWNLOAD_DELAY_SECONDS: int = 5


def _sanitize_path_component(name: str) -> str:
    """Executa uma limpeza pesada em nomes de ficheiros/pastas para o sistema de ficheiros."""
    safe_name = name.replace('\n', ' ').replace('\r', ' ')
    safe_name = re.sub(r'\s+', ' ', safe_name).strip()
    invalid_os_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_os_chars:
        safe_name = safe_name.replace(char, '-')
    max_len = 150
    if len(safe_name) <= max_len:
        return safe_name
    try:
        file_root, file_ext = os.path.splitext(safe_name)
        hash_suffix = hashlib.md5(name.encode('utf-8')).hexdigest()[:8]
        available_len_for_root = max_len - len(file_ext) - 9
        truncated_root = file_root[:available_len_for_root]
        return f"{truncated_root}_{hash_suffix}{file_ext}"
    except Exception:
        return safe_name[:max_len]


def setup_google_drive_service() -> Optional[Resource]:
    """Estabelece e retorna um cliente de serviço autenticado para a API do Drive."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logging.error(f'Falha ao atualizar o token de acesso: {e}')
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('drive', 'v3', credentials=creds)
        logging.info('Cliente de serviço do Google Drive inicializado com sucesso.')
        return service
    except Exception as e:
        logging.error(f'Falha ao construir o cliente de serviço do Google Drive: {e}')
        return None


def download_file(service: Resource, file_id: str, safe_file_name: str, download_folder: str, 
                  retries: int = DOWNLOAD_RETRIES, delay: int = DOWNLOAD_DELAY_SECONDS) -> Dict:
    """Baixa um ficheiro binário, com retentativas e suporte a caminhos longos."""
    for attempt in range(retries):
        try:
            request = service.files().get_media(fileId=file_id)
            os.makedirs(download_folder, exist_ok=True)
            filepath = os.path.join(download_folder, safe_file_name)
            abs_filepath = os.path.abspath(filepath)
            long_path_aware_filepath = f"\\\\?\\{abs_filepath}"
            with open(long_path_aware_filepath, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    logging.info(f"Download de '{safe_file_name}': {int(status.progress() * 100)}% concluído.")
            return {'status': 'sucesso', 'filepath': filepath, 'attempts': attempt + 1, 'error': None}
        except Exception as e:
            error_message = str(e)
            logging.warning(f"Tentativa {attempt + 1}/{retries} falhou ao baixar '{safe_file_name}': {error_message}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logging.error(f"Todas as tentativas para o ficheiro '{safe_file_name}' falharam.")
                return {'status': 'falha', 'filepath': None, 'attempts': attempt + 1, 'error': error_message}
    return {'status': 'falha', 'filepath': None, 'attempts': retries, 'error': 'Loop de tentativas finalizado inesperadamente.'}


def export_google_doc(service: Resource, file_id: str, safe_file_name: str, download_folder: str, 
                      retries: int = DOWNLOAD_RETRIES, delay: int = DOWNLOAD_DELAY_SECONDS) -> Dict:
    """Exporta um ficheiro Google Docs como PDF, com retentativas e suporte a caminhos longos."""
    for attempt in range(retries):
        try:
            request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
            os.makedirs(download_folder, exist_ok=True)
            file_root, _ = os.path.splitext(safe_file_name)
            filepath = os.path.join(download_folder, f"{file_root}.pdf")
            abs_filepath = os.path.abspath(filepath)
            long_path_aware_filepath = f"\\\\?\\{abs_filepath}"
            with open(long_path_aware_filepath, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    logging.info(f"Exportando '{safe_file_name}' para PDF: {int(status.progress() * 100)}% concluído.")
            return {'status': 'sucesso', 'filepath': filepath, 'attempts': attempt + 1, 'error': None}
        except Exception as e:
            error_message = str(e)
            logging.warning(f"Tentativa {attempt + 1}/{retries} falhou ao exportar '{safe_file_name}': {error_message}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logging.error(f"Todas as tentativas para o ficheiro '{safe_file_name}' falharam.")
                return {'status': 'falha', 'filepath': None, 'attempts': attempt + 1, 'error': error_message}
    return {'status': 'falha', 'filepath': None, 'attempts': retries, 'error': 'Loop de tentativas finalizado inesperadamente.'}


def get_drive_file_inventory(service: Resource, folder_id: str, parent_path: str = "") -> List[Dict]:
    """Gera um inventário completo de ficheiros com todas as informações necessárias."""
    inventory = []
    ignored_mime_types = ['application/vnd.google-apps.shortcut']
    try:
        fields = "files(id, name, mimeType, md5Checksum)"
        query = f"'{folder_id}' in parents and trashed = false"
        
        request = service.files().list(q=query, pageSize=1000, fields=fields, supportsAllDrives=True, includeItemsFromAllDrives=True)
        
        while request is not None:
            results = request.execute()
            items = results.get('files', [])
            for item in items:
                safe_name = _sanitize_path_component(item['name'])
                current_path = os.path.join(parent_path, safe_name)
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    inventory.extend(get_drive_file_inventory(service, item['id'], current_path))
                else:
                    task = {
                        'id': item['id'],
                        'original_name': item['name'],
                        'safe_name': safe_name,
                        'relative_path': current_path.replace('\\', '/'),
                        'md5Checksum': item.get('md5Checksum'),
                        'mimeType': item['mimeType']
                    }
                    task['status'] = 'ignorado' if item['mimeType'] in ignored_mime_types else 'pendente'
                    inventory.append(task)
            
            request = service.files().list_next(previous_request=request, previous_response=results)
            
    except Exception as e:
        logging.error(f"Falha ao gerar o inventário do Drive para a pasta ID '{folder_id}': {e}")
    return inventory