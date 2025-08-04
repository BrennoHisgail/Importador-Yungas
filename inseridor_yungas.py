"""Script orquestrador para a Fase 2: Inserção na Plataforma Yungas.

Nesta fase, o script é usado para testar as funcionalidades de login,
navegação e criação de uma pasta de teste.
"""

import argparse
import logging
import time

# Importamos a nova função de teste que criamos
from yungas_selenium_utils import (
    iniciar_driver, 
    fazer_login, 
    navegar_para_materiais, 
    criar_pasta_teste
)

def main() -> None:
    """
    Ponto de entrada principal para o script de inserção.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Fase 2: Robô para inserir arquivos na Yungas.")
    parser.add_argument('--yungas-user', required=True, help='Usuário de acesso da plataforma Yungas.')
    parser.add_argument('--yungas-pass', required=True, help='Senha de acesso da plataforma Yungas.')
    args = parser.parse_args()

    logging.info("Iniciando Fase 2: Teste de Criação de Pasta.")
    driver = iniciar_driver()

    if driver:
        try:
            if fazer_login(driver, args.yungas_user, args.yungas_pass):
                if navegar_para_materiais(driver):
                    # Se o login e a navegação deram certo, TENTA CRIAR A PASTA
                    # Gera um nome único para a pasta usando o timestamp atual
                    nome_pasta_teste = f"Pasta de Teste do Robô - {int(time.time())}"
                    
                    criar_pasta_teste(driver, nome_pasta_teste)
                    
                    logging.info("Teste de criação de pasta concluído! Pausando por 15 segundos...")
                    time.sleep(15)
        
        finally:
            driver.quit()
            logging.info("Navegador fechado.")

if __name__ == "__main__":
    main()