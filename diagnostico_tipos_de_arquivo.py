# diagnostico_tipos_de_arquivo.py

import logging
from collections import Counter
from drive_utils import setup_google_drive_service, _sanitize_path_component
from typing import List, Dict

def get_full_inventory_with_types(service, folder_id, parent_path=""):
    """
    Percorre o Drive e retorna uma lista de todos os itens, incluindo o mimeType.
    """
    inventory = []
    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            pageSize=1000,
            fields="files(id, name, mimeType)"
        ).execute()
        
        items = results.get('files', [])

        for item in items:
            safe_name = _sanitize_path_component(item['name'])
            current_path = f"{parent_path}/{safe_name}"
            
            # Adiciona o item atual à lista
            inventory.append({'path': current_path, 'mimeType': item['mimeType']})
            
            # Se for uma pasta, continua a busca dentro dela
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                inventory.extend(get_full_inventory_with_types(service, item['id'], current_path))

    except Exception as e:
        logging.error(f"Erro ao gerar inventário para a pasta {folder_id}: {e}")
    
    return inventory

def main():
    """Roda o diagnóstico e imprime um relatório dos tipos de arquivo."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Use o mesmo ID de pasta que você usou no extrator
    drive_folder_id = "1xP0bda16dBESJHJ4yfLOaf4UThteGlcQ" # <-- CONFIRME SE É O ID CORRETO

    logging.info("Conectando ao Google Drive...")
    service = setup_google_drive_service()
    
    if service:
        logging.info("Gerando inventário completo de todos os itens. Isso pode levar um tempo...")
        full_inventory = get_full_inventory_with_types(service, drive_folder_id)
        
        # Filtra para remover as pastas da contagem
        files_only = [item for item in full_inventory if item['mimeType'] != 'application/vnd.google-apps.folder']
        
        logging.info(f"Inventário concluído. Total de {len(files_only)} arquivos/itens encontrados.")
        
        # Conta quantas vezes cada mimeType aparece
        mime_type_counts = Counter(item['mimeType'] for item in files_only)
        
        print("\n--- RELATÓRIO DE TIPOS DE ARQUIVO ---")
        for mime_type, count in mime_type_counts.items():
            print(f"{mime_type}: {count}")
        print("------------------------------------")

if __name__ == "__main__":
    main()