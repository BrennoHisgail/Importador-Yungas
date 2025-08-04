
"""Módulo de utilitários para automação da interface web da Yungas usando Selenium.

Fornece funcionalidades para inicializar um driver de navegador furtivo,
executar o fluxo de login de duas etapas e interagir com o módulo de materiais.
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
ACTION_TIMEOUT_SECONDS = 15
POST_LOGIN_TIMEOUT_SECONDS = 60

# --- Selectors for Login Flow ---
EMAIL_FIELD_ID = "username-password"
CONTINUE_BUTTON_ID = "submit-button"
PASSWORD_FIELD_ID = "password"
FINAL_LOGIN_BUTTON_ID = "password-submit-button"
POST_LOGIN_SUCCESS_XPATH = "//span[text()='Caixa de entrada']"

# --- Selectors for Materiais Module ---
MATERIALS_MENU_BUTTON_XPATH = "//span[contains(text(), 'Materiais')]"
CREATE_FOLDER_BUTTON_XPATH = "//img[@alt='Nova pasta']"
FOLDER_NAME_INPUT_CSS = "input[placeholder='Título']"
CONFIRM_CREATE_FOLDER_BUTTON_XPATH = "//button[text()='Salvar']"


def iniciar_driver() -> Optional[WebDriver]:
    """Inicializa e retorna uma instância do Undetected ChromeDriver."""
    try:
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = uc.Chrome(options=options)
        logging.info("Undetected ChromeDriver iniciado com sucesso.")
        return driver
    except Exception as e:
        logging.error(f"Erro ao iniciar o Undetected ChromeDriver: {e}")
        return None

def fazer_login(driver: WebDriver, user: str, password: str) -> bool:
    """Navega pelo fluxo de login de 2 etapas da Yungas."""
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

def navegar_para_materiais(driver: WebDriver) -> bool:
    """Após o login, clica no item de menu para navegar até o Módulo de Materiais."""
    try:
        logging.info("Navegando para o Módulo de Materiais...")
        wait = WebDriverWait(driver, ACTION_TIMEOUT_SECONDS)

        # 1. Encontra e clica no botão "Materiais" no menu lateral
        botao_materiais = wait.until(EC.element_to_be_clickable((By.XPATH, MATERIALS_MENU_BUTTON_XPATH)))
        botao_materiais.click()
        
        # 2. Espera pelo botão "Nova pasta" para confirmar que a página carregou
        wait.until(EC.presence_of_element_located((By.XPATH, CREATE_FOLDER_BUTTON_XPATH)))
        
        logging.info("Navegação para o Módulo de Materiais bem-sucedida.")
        return True

    except Exception as e:
        logging.error(f"Falha ao navegar para o Módulo de Materiais: {e}")
        return False

def criar_pasta_teste(driver: WebDriver, nome_da_pasta: str) -> bool:
    """
    Tenta criar uma única pasta de teste, com logs detalhados para depuração.
    """
    try:
        logging.info(f"Iniciando teste de criação da pasta: '{nome_da_pasta}'")
        wait = WebDriverWait(driver, ACTION_TIMEOUT_SECONDS)

        # --- ETAPA DE DEBATE 1: Encontrar e clicar no botão "Nova pasta" ---
        logging.info("Procurando o botão 'Nova pasta'...")
        botao_criar_pasta = wait.until(EC.element_to_be_clickable((By.XPATH, CREATE_FOLDER_BUTTON_XPATH)))
        logging.info("Botão 'Nova pasta' encontrado. Clicando...")
        botao_criar_pasta.click()
        time.sleep(2) # Pequena pausa para a interface reagir

        # --- ETAPA DE DEBATE 2: Encontrar e preencher o campo de nome ---
        logging.info("Procurando o campo de texto para o nome da pasta...")
        campo_nome_pasta = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, FOLDER_NAME_INPUT_CSS)))
        logging.info("Campo de nome encontrado. Inserindo texto...")
        campo_nome_pasta.send_keys(nome_da_pasta)
        time.sleep(1)

        # --- ETAPA DE DEBATE 3: Encontrar e clicar no botão "Salvar" ---
        logging.info("Procurando o botão 'Salvar'...")
        botao_confirmar = wait.until(EC.element_to_be_clickable((By.XPATH, CONFIRM_CREATE_FOLDER_BUTTON_XPATH)))
        logging.info("Botão 'Salvar' encontrado. Clicando...")
        botao_confirmar.click()
        time.sleep(2) # Pequena pausa para a pasta ser criada

        # --- ETAPA DE DEBATE 4: Verificar se a pasta apareceu ---
        logging.info(f"Verificando se a pasta '{nome_da_pasta}' apareceu na lista...")
        wait.until(EC.presence_of_element_located((By.XPATH, f"//span[text()='{nome_da_pasta}']")))
        
        logging.info(f"SUCESSO! Pasta '{nome_da_pasta}' criada e verificada.")
        return True

    except Exception as e:
        logging.error(f"FALHA ao tentar criar a pasta de teste. O erro foi: {e}")
        return False