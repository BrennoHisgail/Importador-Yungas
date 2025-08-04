# extrator_drive.py

"""Script orquestrador para a Fase 1 do processo de importação.

Lê a configuração de um arquivo config.ini, extrai uma estrutura de arquivos 
do Google Drive, cria a estrutura de pastas local antecipadamente, gerencia o
estado para retomada de downloads, verifica a integridade e cria um backlog
detalhado e um backup compactado.
"""

import argparse
import logging
import os
import shutil
import datetime
import json
import csv
import configparser
from typing import List, Dict, Optional

from drive_utils import (
    setup_google_drive_service, 
    get_drive_file_inventory, 
    download_file, 
    export_google_doc
)

def load_state(state_filepath: str) -> Optional[List[Dict]]:
    """Carrega o estado da extração de um arquivo JSON."""
    if os.path.exists(state_filepath):
        logging.info(f"Arquivo de estado encontrado em '{state_filepath}'. Carregando progresso.")
        try:
            with open(state_filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Erro ao ler o arquivo de estado: {e}. Um novo será criado.")
            return None
    logging.info("Nenhum estado anterior encontrado.")
    return None

def save_state(state: List[Dict], state_filepath: str) -> None:
    """Salva o estado atual da extração em um arquivo JSON."""
    try:
        os.makedirs(os.path.dirname(state_filepath), exist_ok=True)
        with open(state_filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
    except IOError as e:
        logging.error(f"Não foi possível salvar o estado em '{state_filepath}': {e}")

def write_backlog_csv(records: List[Dict], client_name: str) -> None:
    """Escreve uma lista de registros de processamento em um arquivo CSV."""
    if not records:
        return
    
    backlog_filepath = f"backlog_{client_name}_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"
    headers = [
        'timestamp', 'status', 'drive_id', 'original_name', 'sanitized_name', 
        'was_renamed', 'relative_path', 'attempts', 'error_message', 'md5_checksum'
    ]
    try:
        with open(backlog_filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(records)
        logging.info(f"Backlog de extração salvo com sucesso em '{backlog_filepath}'")
    except IOError as e:
        logging.error(f"Falha ao escrever o arquivo de backlog: {e}")

def get_local_file_inventory(root_folder: str) -> List[str]:
    """Escaneia um diretório local e retorna uma lista de caminhos de arquivos relativos."""
    local_inventory: List[str] = []
    if not os.path.isdir(root_folder):
        return local_inventory
    for dirpath, _, filenames in os.walk(root_folder):
        for f in filenames:
            full_path = os.path.join(dirpath, f)
            relative_path = os.path.relpath(full_path, root_folder)
            local_inventory.append(relative_path.replace('\\', '/'))
    return local_inventory

def verify_downloads(drive_inventory: List[str], local_inventory: List[str]) -> bool:
    """Compara o inventário do Drive com o inventário local para verificar a integridade."""
    logging.info("--- Iniciando verificação de integridade dos downloads ---")
    drive_set = set(drive_inventory)
    local_set = set(local_inventory)
    missing_files = drive_set - local_set
    if not missing_files:
        logging.info(f"VERIFICAÇÃO BEM-SUCEDIDA: Todos os {len(drive_set)} arquivos esperados foram baixados.")
        return True
    logging.error(f"VERIFICAÇÃO FALHOU: {len(missing_files)} arquivo(s) estão faltantes.")
    for missing in sorted(list(missing_files)):
        logging.error(f"  - Arquivo Faltante: {missing}")
    return False

def create_backup(source_dir: str, backup_dir: str, client_name: str) -> bool:
    """Cria um arquivo .zip de um diretório de origem."""
    os.makedirs(backup_dir, exist_ok=True)
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"backup_{client_name}_{timestamp}"
        backup_filepath = os.path.join(backup_dir, backup_filename)
        logging.info(f"Iniciando criação do backup de '{source_dir}'...")
        shutil.make_archive(backup_filepath, 'zip', source_dir)
        logging.info(f"Backup criado com sucesso em: {backup_filepath}.zip")
        return True
    except Exception as e:
        logging.error(f"Falha ao criar o backup: {e}")
        return False

def main() -> None:
    """Ponto de entrada principal para a execução do script de extração."""
    config = configparser.ConfigParser()
    config.read('config.ini')

    downloads_dir = config['Paths']['downloads_dir']
    backups_dir = config['Paths']['backups_dir']
    state_dir = config['Paths']['state_dir']
    log_filename = config['Logging']['log_filename']
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_filename, encoding='utf-8'),
                            logging.StreamHandler()
                        ])
    
    parser = argparse.ArgumentParser(description="Fase 1: Ferramenta para extrair arquivos do Google Drive.")
    parser.add_argument('--drive-folder-id', required=True, help='ID da pasta raiz no Google Drive.')
    parser.add_argument('--client-name', required=True, help='Nome do cliente para o backup e arquivo de estado.')
    args = parser.parse_args()
    
    state_filepath = os.path.join(state_dir, f"download_state_{args.client_name}.json")
    
    logging.info("--- INICIANDO FASE 1: EXTRAÇÃO E BACKUP ---")
    
    drive_service = setup_google_drive_service()
    if not drive_service:
        logging.critical("Falha na conexão com o Google Drive. Processo abortado.")
        return

    tasks = load_state(state_filepath)
    if not tasks:
        logging.info("Iniciando fase de planejamento: mapeando todos os arquivos no Drive...")
        inventory = get_drive_file_inventory(drive_service, args.drive_folder_id)
        tasks = inventory
        save_state(tasks, state_filepath)
        logging.info(f"Novo plano de download com {len(tasks)} itens foi criado.")

    # --- NOVA ETAPA: CRIAÇÃO ANTECIPADA DE PASTAS ---
    logging.info("Iniciando fase de estruturação: criando a árvore de diretórios local...")
    dir_paths_to_create = {os.path.dirname(task['relative_path']) for task in tasks if os.path.dirname(task['relative_path'])}
    for unique_dir in sorted(list(dir_paths_to_create)):
        full_dir_path = os.path.join(downloads_dir, unique_dir)
        os.makedirs(full_dir_path, exist_ok=True)
    logging.info("Estrutura de diretórios local criada/verificada com sucesso.")
    # --- FIM DA NOVA ETAPA ---

    logging.info("Iniciando/Retomando processo de download...")
    total_tasks = len(tasks)
    backlog_records = []
    
    for index, task in enumerate(tasks):
        expected_path = task['relative_path']
        if 'google-apps' in task.get('mimeType', ''):
            path_root, _ = os.path.splitext(expected_path)
            expected_path = f"{path_root}.pdf"
        local_filepath = os.path.join(downloads_dir, expected_path)

        if task['status'] == 'concluido' or (task['status'] == 'pendente' and os.path.exists(local_filepath)):
            if task['status'] == 'pendente':
                task['status'] = 'concluido'
            logging.info(f"--- [ {index + 1} / {total_tasks} ] Pulando arquivo já existente: {task['safe_name']} ---")
            continue
        
        if task['status'] == 'pendente':
            logging.info(f"--- [ {index + 1} / {total_tasks} ] ---")
            download_dir = os.path.join(downloads_dir, os.path.dirname(task['relative_path']))
            
            result: Dict
            if 'google-apps' in task.get('mimeType', ''):
                result = export_google_doc(drive_service, task['id'], task['safe_name'], download_folder=download_dir)
            else:
                result = download_file(drive_service, task['id'], task['safe_name'], download_folder=download_dir)
            
            task['status'] = result['status']
            
            record = {
                'timestamp': datetime.datetime.now().isoformat(), 'status': result['status'].upper(),
                'drive_id': task['id'], 'original_name': task.get('original_name', task['safe_name']),
                'sanitized_name': task['safe_name'], 
                'was_renamed': 'Sim' if task.get('original_name', task['safe_name']) != task['safe_name'] else 'Não',
                'relative_path': task['relative_path'], 'attempts': result['attempts'],
                'error_message': result['error'], 'md5_checksum': task.get('md5Checksum')
            }
            backlog_records.append(record)
    
    save_state(tasks, state_filepath)
    
    logging.info("Processo de download finalizado. Iniciando verificação final e geração de relatórios...")
    
    write_backlog_csv(backlog_records, args.client_name)
    
    final_tasks = tasks
    drive_inventory_paths = []
    for t in final_tasks:
        if t['status'] in ['ignorado', 'falha']:
            continue
        path = t['relative_path']
        if 'google-apps' in t.get('mimeType', ''):
            path_root, _ = os.path.splitext(path)
            drive_inventory_paths.append(f"{path_root}.pdf")
        else:
            drive_inventory_paths.append(path)
    
    local_inventory_paths = get_local_file_inventory(downloads_dir)
    is_download_complete = verify_downloads(drive_inventory_paths, local_inventory_paths)
    
    if is_download_complete:
        create_backup(downloads_dir, backups_dir, args.client_name)
        logging.info("--- FASE 1 CONCLUÍDA COM SUCESSO ---")
    else:
        logging.error("O backup foi ignorado devido a arquivos faltantes na extração.")
        logging.info("--- FASE 1 CONCLUÍDA COM ERROS ---")

if __name__ == "__main__":
    main()