# yungas_selenium_utils.py

"""Módulo de utilitários para automação da interface web da Yungas usando Selenium."""

import logging
import time
from typing import Optional

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- Constants for Selectors and Configuration ---
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
FOLDER_BY_NAME_XPATH = "//span[contains(@class, 'card-title') and text()='%s']"


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
        campo_usuario = wait.until(EC.presence_of_element_located((By.ID, EMAIL_FIELD_ID)))
        campo_usuario.send_keys(user)
        driver.find_element(By.ID, CONTINUE_BUTTON_ID).click()
        logging.info("Pausando por 15 segundos para aguardar a página de senha...")
        time.sleep(15)
        campo_senha = wait.until(EC.presence_of_element_located((By.ID, PASSWORD_FIELD_ID)))
        campo_senha.send_keys(password)
        driver.find_element(By.ID, FINAL_LOGIN_BUTTON_ID).click()
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
        botao_materiais = wait.until(EC.element_to_be_clickable((By.XPATH, MATERIALS_MENU_BUTTON_XPATH)))
        botao_materiais.click()
        wait.until(EC.presence_of_element_located((By.XPATH, CREATE_FOLDER_BUTTON_XPATH)))
        logging.info("Navegação para o Módulo de Materiais bem-sucedida.")
        return True
    except Exception as e:
        logging.error(f"Falha ao navegar para o Módulo de Materiais: {e}")
        return False

def garantir_existencia_da_pasta(driver: WebDriver, caminho_da_pasta: str) -> bool:
    """
    Garante que uma estrutura de pastas exista na Yungas, com esperas inteligentes.
    """
    try:
        logging.info(f"Processando caminho de pasta: '{caminho_da_pasta}'")
        # Começa sempre navegando para a raiz de Materiais para garantir um ponto de partida limpo
        navegar_para_materiais(driver)
        
        partes_do_caminho = caminho_da_pasta.split('/')
        
        for nome_da_pasta in partes_do_caminho:
            wait = WebDriverWait(driver, ACTION_TIMEOUT_SECONDS)
            time.sleep(2) # Pausa para a interface carregar a lista de pastas

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
                
                # --- INÍCIO DA MUDANÇA: ESPERA INTELIGENTE ---
                logging.info("Aguardando a conclusão da criação da pasta...")
                # A melhor forma de saber que o pop-up fechou é esperar que um elemento da
                # página principal, como o próprio botão "Nova pasta", fique clicável novamente.
                wait.until(EC.element_to_be_clickable((By.XPATH, CREATE_FOLDER_BUTTON_XPATH)))
                logging.info("Criação concluída. A interface está pronta para a próxima ação.")
                # --- FIM DA MUDANÇA ---
                
                # Agora que a UI está estável, procuramos pela nova pasta para entrar nela.
                pasta_recem_criada = wait.until(EC.presence_of_element_located((By.XPATH, seletor_pasta_existente)))
                driver.execute_script("arguments[0].click();", pasta_recem_criada)
                logging.info(f"Pasta '{nome_da_pasta}' criada e acessada.")

        logging.info(f"Estrutura de pasta '{caminho_da_pasta}' sincronizada com sucesso.")
        return True
    except Exception as e:
        logging.error(f"Falha ao sincronizar a estrutura da pasta '{caminho_da_pasta}': {e}")
        return False
