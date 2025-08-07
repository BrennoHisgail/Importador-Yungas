"""Script orquestrador para a Fase 2: Inserção na Plataforma Yungas."""

import argparse
import logging
import os
import configparser
import time
from typing import List

from yungas_selenium_utils import (
    iniciar_driver, 
    fazer_login, 
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
    
    # Lê as configurações de caminhos e do Selenium do arquivo .ini
    downloads_dir = config.get('Paths', 'downloads_dir', fallback='downloads')
    user_data_dir = config.get('Selenium', 'user_data_dir', fallback=None)
    profile_directory = config.get('Selenium', 'profile_directory', fallback=None)
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = argparse.ArgumentParser(description="Fase 2: Robô para inserir arquivos na Yungas.")
    parser.add_argument('--yungas-user', required=True, help='Usuário de acesso da plataforma Yungas.')
    parser.add_argument('--yungas-pass', required=True, help='Senha de acesso da plataforma Yungas.')
    args = parser.parse_args()

    logging.info("Iniciando Fase 2: Robô de Inserção.")
    # Passa as configurações de perfil lidas do .ini para a função que inicia o robô
    driver = iniciar_driver(user_data_dir=user_data_dir, profile_directory=profile_directory)

    if driver:
        try:
            if fazer_login(driver, args.yungas_user, args.yungas_pass):
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
                    # Futuramente, aqui começará a etapa de upload de arquivos

        finally:
            driver.quit()
            logging.info("Navegador fechado.")

if __name__ == "__main__":
    main()