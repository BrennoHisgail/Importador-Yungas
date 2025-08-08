# yungas_selenium_utils.py

"""Módulo de utilitários para automação da interface web da Yungas usando Selenium.

Esta versão é projetada para se conectar a uma instância do Chrome já em execução,
assumindo que o utilizador já realizou o login manualmente.
"""

import logging
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# --- Constants for Selectors and Configuration ---
YUNGAS_BASE_URL = "https://app.yungas.com.br"
ACTION_TIMEOUT_SECONDS = 15

# --- Selectors for Verification and Navigation ---
LOGIN_SUCCESS_XPATH = "//span[contains(text(), 'Materiais')]"

# --- Selectors for Materiais Module ---
MATERIALS_MENU_BUTTON_XPATH = "//span[contains(text(), 'Materiais')]"
CREATE_FOLDER_BUTTON_XPATH = "//img[@alt='Nova pasta']"
FOLDER_NAME_INPUT_CSS = "input[placeholder='Título']"
CONFIRM_CREATE_FOLDER_BUTTON_XPATH = "//button[text()='Salvar']"
FOLDER_BY_NAME_XPATH = "//span[contains(@class, 'card-title') and text()='%s']"


def conectar_driver_existente(debugging_port: int) -> Optional[WebDriver]:
    """
    Conecta-se a uma instância do Chrome que já está em execução com o modo de depuração ativado.
    """
    try:
        logging.info(f"Tentando conectar-se ao Chrome na porta de depuração: {debugging_port}...")
        
        options = Options()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debugging_port}")
        
        # O webdriver-manager baixa e configura o driver correto automaticamente.
        service = ChromeService(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("Conexão com o navegador existente estabelecida com sucesso.")
        return driver
    except Exception as e:
        logging.error(f"Não foi possível conectar ao navegador existente. Verifique se o Chrome foi iniciado com a porta de depuração correta. Erro: {e}")
        return None

def verificar_login(driver: WebDriver) -> bool:
    """Verifica se a sessão do navegador conectado já está logada na plataforma."""
    try:
        logging.info("Verificando se a sessão está logada...")
        driver.get(YUNGAS_BASE_URL)
        driver.maximize_window()
        
        wait = WebDriverWait(driver, ACTION_TIMEOUT_SECONDS)
        wait.until(EC.presence_of_element_located((By.XPATH, LOGIN_SUCCESS_XPATH)))
        
        logging.info("Verificação de login bem-sucedida. Sessão ativa.")
        return True
    except TimeoutException:
        logging.error("Login não detetado. A página não parece estar logada.")
        return False
    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado ao verificar o login: {e}")
        return False

def navegar_para_materiais(driver: WebDriver) -> bool:
    """Após o login, clica no item de menu para navegar até o Módulo de Materiais."""
    try:
        logging.info("Navegando para o Módulo de Materiais...")
        wait = WebDriverWait(driver, ACTION_TIMEOUT_SECONDS)
        botao_materiais = wait.until(EC.element_to_be_clickable((By.XPATH, MATERIALS_MENU_BUTTON_XPATH)))
        botao_materiais.click()
        wait.until(EC.presence_of_element_located((By.XPATH, CREATE_FOLDER_BUTTON_XPATH)))
        logging.info("Navegação para o Módulo de Materiais bem-sucedida.")
        return True
    except Exception as e:
        logging.error(f"Falha ao navegar para o Módulo de Materiais: {e}")
        return False

def garantir_existencia_da_pasta(driver: WebDriver, caminho_da_pasta: str) -> bool:
    """Garante que uma estrutura de pastas exista na Yungas, criando-a se necessário."""
    try:
        logging.info(f"Processando caminho de pasta: '{caminho_da_pasta}'")
        navegar_para_materiais(driver)
        
        partes_do_caminho = caminho_da_pasta.split('/')
        
        for nome_da_pasta in partes_do_caminho:
            wait = WebDriverWait(driver, ACTION_TIMEOUT_SECONDS)
            time.sleep(2)

            try:
                seletor_pasta_existente = FOLDER_BY_NAME_XPATH % nome_da_pasta
                pasta = wait.until(EC.presence_of_element_located((By.XPATH, seletor_pasta_existente)))
                logging.info(f"Pasta '{nome_da_pasta}' encontrada. Entrando...")
                driver.execute_script("arguments[0].click();", pasta)
            except TimeoutException:
                logging.info(f"Pasta '{nome_da_pasta}' não encontrada. Criando...")
                
                botao_criar_pasta = wait.until(EC.element_to_be_clickable((By.XPATH, CREATE_FOLDER_BUTTON_XPATH)))
                botao_criar_pasta.click()
                
                campo_nome_pasta = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, FOLDER_NAME_INPUT_CSS)))
                campo_nome_pasta.send_keys(nome_da_pasta)
                
                botao_confirmar = wait.until(EC.element_to_be_clickable((By.XPATH, CONFIRM_CREATE_FOLDER_BUTTON_XPATH)))
                botao_confirmar.click()
                
                logging.info("Aguardando a conclusão da criação da pasta...")
                wait.until(EC.element_to_be_clickable((By.XPATH, CREATE_FOLDER_BUTTON_XPATH)))
                
                pasta_recem_criada = wait.until(EC.presence_of_element_located((By.XPATH, seletor_pasta_existente)))
                driver.execute_script("arguments[0].click();", pasta_recem_criada)
                logging.info(f"Pasta '{nome_da_pasta}' criada e acessada.")

        logging.info(f"Estrutura de pasta '{caminho_da_pasta}' sincronizada com sucesso.")
        return True
    except Exception as e:
        logging.error(f"Falha ao sincronizar a estrutura da pasta '{caminho_da_pasta}': {e}")
        return False
