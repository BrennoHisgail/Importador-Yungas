# inseridor_yungas.py

"""Script orquestrador para a Fase 2: Inserção na Plataforma Yungas.

Este script utiliza um perfil do Chrome pré-logado para sincronizar uma
estrutura de pastas local com o Módulo de Materiais da plataforma.
"""

import logging
import os
import configparser
from typing import List

# A função de importação mudou para a nova lógica
from yungas_selenium_utils import (
    conectar_driver_existente, 
    verificar_login, 
    navegar_para_materiais,
    garantir_existencia_da_pasta
)

def get_local_folder_structure(root_dir: str) -> List[str]:
    """
    Lê uma estrutura de diretórios local e retorna uma lista ordenada de caminhos relativos.
    """
    folder_paths = set()
    if not os.path.isdir(root_dir):
        logging.warning(f"Diretório de downloads '{root_dir}' não encontrado.")
        return []
        
    for dirpath, _, _ in os.walk(root_dir):
        relative_path = os.path.relpath(dirpath, root_dir)
        if relative_path != '.':
            folder_paths.add(relative_path.replace('\\', '/'))
    
    return sorted(list(folder_paths))

def main() -> None:
    """Ponto de entrada principal para o script de inserção."""
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    downloads_dir = config.get('Paths', 'downloads_dir', fallback='downloads')
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logging.info("Iniciando Fase 2: Robô de Inserção.")
    
    # --- MUDANÇA AQUI ---
    # Conecta-se ao Chrome na porta 9222, que foi aberta manualmente.
    driver = conectar_driver_existente(debugging_port=9222)

    if driver:
        try:
            if verificar_login(driver):
                if navegar_para_materiais(driver):
                    
                    logging.info("Iniciando fase de sincronização de pastas...")
                    pastas_a_sincronizar = get_local_folder_structure(downloads_dir)
                    
                    if not pastas_a_sincronizar:
                        logging.info("Nenhuma estrutura de pastas encontrada em '/downloads' para sincronizar.")
                    else:
                        logging.info(f"{len(pastas_a_sincronizar)} pastas para sincronizar.")
                        for pasta in pastas_a_sincronizar:
                            sucesso = garantir_existencia_da_pasta(driver, pasta)
                            if not sucesso:
                                logging.error(f"Erro crítico ao criar a pasta '{pasta}'. Abortando.")
                                break
                    
                    logging.info("Fase de sincronização de pastas concluída.")

        finally:
            # Não usamos mais driver.quit(), pois não queremos fechar o navegador manual.
            logging.info("Script finalizado. O navegador permanece aberto.")

if __name__ == "__main__":
    main()
