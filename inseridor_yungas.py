# inseridor_yuncas.py (Versão para Teste de Login)

"""Script orquestrador para a Fase 2: Inserção na Plataforma Yungas.

Nesta fase inicial, o script é usado para testar a funcionalidade de login do robô.
"""

import argparse
import logging
import time
from typing import Dict

# Importa as funções do nosso módulo de robô
from yungas_selenium_utils import iniciar_driver, fazer_login

def main() -> None:
    """Ponto de entrada para a Fase 2: Inserção na Yungas."""
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = argparse.ArgumentParser(description="Fase 2: Robô para inserir arquivos na Yungas.")
    parser.add_argument('--yungas-user', required=True, help='Usuário de acesso da plataforma Yungas.')
    parser.add_argument('--yungas-pass', required=True, help='Senha de acesso da plataforma Yungas.')
    args = parser.parse_args()

    logging.info("Iniciando Fase 2: Robô de Inserção.")
    driver = iniciar_driver()

    if driver:
        sucesso_login = fazer_login(driver, args.yungas_user, args.yungas_pass)
        
        if sucesso_login:
            logging.info("Teste de login BEM-SUCEDIDO! A janela do navegador ficará aberta por 15 segundos para verificação.")
            time.sleep(15) # Pausa para você ver a tela logada
        else:
            logging.error("O teste de login FALHOU. Verifique os seletores no 'yungas_selenium_utils.py' e as credenciais fornecidas.")
            
        driver.quit()
        logging.info("Navegador fechado.")

if __name__ == "__main__":
    main()