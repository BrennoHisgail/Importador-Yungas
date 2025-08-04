# yungas_selenium_utils.py

"""Módulo de utilitários para automação da interface web da Yungas usando Selenium.

Fornece funcionalidades para inicializar um driver de navegador furtivo,
executar o fluxo de login de duas etapas e, futuramente, interagir com
o módulo de materiais.
"""

import logging
import time
from typing import Optional

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Constants for Selectors and Configuration ---
# Centralizar seletores aqui facilita a manutenção se a interface da Yungas mudar.
YUNGAS_BASE_URL = "https://app.yungas.com.br"
LOGIN_TIMEOUT_SECONDS = 20
POST_LOGIN_TIMEOUT_SECONDS = 60

# --- Selectors for Login Flow ---
EMAIL_FIELD_ID = "username-password"
CONTINUE_BUTTON_ID = "submit-button"
PASSWORD_FIELD_ID = "password"
FINAL_LOGIN_BUTTON_ID = "password-submit-button"
POST_LOGIN_SUCCESS_XPATH = "//span[text()='Caixa de entrada']"


def iniciar_driver() -> Optional[WebDriver]:
    """Inicializa e retorna uma instância do Undetected ChromeDriver.
    
    Esta versão é projetada para ser menos detectável por sistemas anti-robô.
    """
    try:
        # Configurações para tentar parecer mais humano
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        driver = uc.Chrome(options=options)
        logging.info("Undetected ChromeDriver iniciado com sucesso.")
        return driver
    except Exception as e:
        logging.error(f"Erro ao iniciar o Undetected ChromeDriver: {e}")
        return None

def fazer_login(driver: WebDriver, user: str, password: str) -> bool:
    """Navega pelo fluxo de login de 2 etapas da Yungas.

    Args:
        driver (WebDriver): A instância do navegador a ser controlada.
        user (str): O nome de usuário para o login.
        password (str): A senha para o login.

    Returns:
        bool: True se o login for bem-sucedido, False caso contrário.
    """
    try:
        driver.get(YUNGAS_BASE_URL)
        driver.maximize_window()
        logging.info(f"Navegando para a página inicial: {YUNGAS_BASE_URL}")
        
        wait = WebDriverWait(driver, LOGIN_TIMEOUT_SECONDS)

        # Etapa 1: Inserir o E-mail
        logging.info("Procurando campo de e-mail...")
        campo_usuario = wait.until(EC.presence_of_element_located((By.ID, EMAIL_FIELD_ID)))
        campo_usuario.send_keys(user)
        
        logging.info("Clicando em 'Continuar'...")
        driver.find_element(By.ID, CONTINUE_BUTTON_ID).click()
        
        # Pausa Estratégica
        logging.info("Pausando por 15 segundos para aguardar a página de senha...")
        time.sleep(15)
        
        # Etapa 2: Inserir a Senha
        logging.info("Procurando campo de senha...")
        campo_senha = wait.until(EC.presence_of_element_located((By.ID, PASSWORD_FIELD_ID)))
        campo_senha.send_keys(password)
        
        # Etapa 3: Clicar em Entrar e Aguardar Confirmação
        logging.info("Clicando no botão final 'Entrar'...")
        driver.find_element(By.ID, FINAL_LOGIN_BUTTON_ID).click()
        
        logging.info(f"Aguardando confirmação de login por até {POST_LOGIN_TIMEOUT_SECONDS} segundos...")
        
        long_wait = WebDriverWait(driver, POST_LOGIN_TIMEOUT_SECONDS)
        long_wait.until(EC.presence_of_element_located((By.XPATH, POST_LOGIN_SUCCESS_XPATH)))
        
        logging.info("Login finalizado com sucesso!")
        return True
        
    except Exception as e:
        logging.error(f"Falha durante o processo de login: {e}")
        return False