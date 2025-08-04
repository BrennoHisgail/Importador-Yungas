# inseridor_yungas.py

"""Script orquestrador para a Fase 2: Inserção na Plataforma Yungas.

Nesta fase inicial, o script é usado para testar a funcionalidade de login do robô
e verificar a configuração do ambiente Selenium.
"""

import argparse
import logging
import time

# Importa as funções de controle do robô do nosso módulo de utilitários
from yungas_selenium_utils import iniciar_driver, fazer_login

def main() -> None:
    """
    Ponto de entrada principal para o script de inserção.

    Configura o ambiente, parseia os argumentos de linha de comando,
    inicia o driver do Selenium e executa o teste de login.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Fase 2: Robô para inserir arquivos na Yungas.")
    parser.add_argument('--yungas-user', required=True, help='Usuário de acesso da plataforma Yungas.')
    parser.add_argument('--yungas-pass', required=True, help='Senha de acesso da plataforma Yungas.')
    args = parser.parse_args()

    logging.info("Iniciando Fase 2: Robô de Inserção.")
    driver = iniciar_driver()

    if driver:
        try:
            login_successful = fazer_login(driver, args.yungas_user, args.yungas_pass)
            
            if login_successful:
                logging.info("Teste de login BEM-SUCEDIDO! Pausando por 15 segundos para verificação visual.")
                # Pausa para permitir que o usuário observe o resultado no navegador.
                time.sleep(15) 
            else:
                logging.error("O teste de login FALHOU. Verifique os seletores no 'yungas_selenium_utils.py' e as credenciais.")
        
        finally:
            # O bloco 'finally' garante que o navegador seja sempre fechado,
            # mesmo que ocorra um erro inesperado durante o login.
            driver.quit()
            logging.info("Navegador fechado.")
    else:
        logging.error("Não foi possível iniciar o WebDriver. A execução foi abortada.")

if __name__ == "__main__":
    main()