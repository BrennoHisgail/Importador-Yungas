# diagnostico_tipos_de_arquivo.py

"""
Script de diagnóstico para analisar o conteúdo de uma pasta do Google Drive.

Este script percorre recursivamente uma estrutura de pastas a partir de um ID raiz
e gera um relatório que conta a quantidade de cada tipo de arquivo (MIME Type)
encontrado. É útil para entender a composição dos dados antes de uma migração.
"""

import logging
import os
import argparse
from collections import Counter
from typing import List, Dict, Optional

# Reutilizamos nosso motor de autenticação e sanitização já construído
from drive_utils import setup_google_drive_service, _sanitize_path_component
from googleapiclient.discovery import Resource

def get_full_inventory_with_types(service: Resource, folder_id: str, parent_path: str = "") -> List[Dict[str, str]]:
    """
    Percorre o Drive recursivamente e retorna uma lista de todos os itens, 
    incluindo pastas, com seus respectivos MimeTypes.

    Args:
        service (Resource): O cliente de serviço autenticado do Google Drive.
        folder_id (str): O ID da pasta do Drive para iniciar a varredura.
        parent_path (str): Usado internamente pela recursão para construir o caminho.

    Returns:
        List[Dict[str, str]]: Uma lista de dicionários, cada um representando um item no Drive.
    """
    inventory = []
    try:
        query = f"'{folder_id}' in parents and trashed = false"
        # Adicionamos nextPageToken ao fields para futura implementação de paginação
        fields = "nextPageToken, files(id, name, mimeType)"
        
        request = service.files().list(q=query, pageSize=1000, fields=fields)
        
        while request is not None:
            results = request.execute()
            items = results.get('files', [])

            for item in items:
                safe_name = _sanitize_path_component(item['name'])
                # Usamos os.path.join para construir o caminho de forma segura
                current_path = os.path.join(parent_path, safe_name)
                
                inventory.append({'path': current_path, 'mimeType': item['mimeType']})
                
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    inventory.extend(get_full_inventory_with_types(service, item['id'], current_path))
            
            request = service.files().list_next(previous_request=request, previous_response=results)

    except Exception as e:
        logging.error(f"Erro ao gerar inventário para a pasta {folder_id}: {e}")
    
    return inventory

def print_report(full_inventory: List[Dict[str, str]]) -> None:
    """
    Filtra a lista de inventário para incluir apenas arquivos e imprime
    um relatório sumarizado da contagem de cada tipo.

    Args:
        full_inventory (List[Dict[str, str]]): A lista completa de itens do Drive.
    """
    files_only = [item for item in full_inventory if item['mimeType'] != 'application/vnd.google-apps.folder']
    
    logging.info(f"Análise concluída. Total de {len(files_only)} arquivos/itens encontrados.")
    
    mime_type_counts = Counter(item['mimeType'] for item in files_only)
    
    print("\n" + "="*50)
    print("--- RELATÓRIO DE TIPOS DE ARQUIVO ---")
    print("="*50)
    # Ordena o relatório por contagem, do maior para o menor
    for mime_type, count in sorted(mime_type_counts.items(), key=lambda item: item[1], reverse=True):
        print(f"{count:<5} | {mime_type}")
    print("-" * 50)

def main() -> None:
    """Ponto de entrada principal para o script de diagnóstico."""
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    parser = argparse.ArgumentParser(description="Ferramenta de diagnóstico de tipos de arquivo no Google Drive.")
    parser.add_argument('--drive-folder-id', required=True, help='ID da pasta raiz no Google Drive a ser analisada.')
    args = parser.parse_args()

    logging.info("Conectando ao Google Drive...")
    service = setup_google_drive_service()
    
    if service:
        logging.info("Gerando inventário completo de todos os itens. Isso pode levar um tempo...")
        full_inventory = get_full_inventory_with_types(service, args.drive_folder_id)
        
        if full_inventory:
            print_report(full_inventory)
        else:
            logging.warning("Nenhum item foi encontrado na pasta especificada.")

if __name__ == "__main__":
    main()