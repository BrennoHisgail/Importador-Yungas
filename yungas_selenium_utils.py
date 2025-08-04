# yungas_selenium_utils.py

import logging
import time
from typing import Optional

# O import principal agora é do 'undetected_chromedriver'
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def iniciar_driver() -> Optional[WebDriver]:
    """Inicializa e retorna uma instância do Undetected ChromeDriver.
    
    Esta versão é projetada para ser menos detectável por sistemas anti-robô.
    """
    try:
        # Usamos uc.Chrome() em vez de webdriver.Chrome()
        driver = uc.Chrome()
        logging.info("Undetected ChromeDriver iniciado com sucesso.")
        return driver
    except Exception as e:
        logging.error(f"Erro ao iniciar o Undetected ChromeDriver. Verifique sua conexão e instalação. Erro: {e}")
        return None

def fazer_login(driver: WebDriver, user: str, password: str) -> bool:
    """Navega pelo fluxo de login de 2 etapas da Yungas."""
    try:
        url_login = "https://app.yungas.com.br"
        driver.get(url_login)
        driver.maximize_window()
        logging.info(f"Navegando para a página de login: {url_login}")
        
        wait = WebDriverWait(driver, 20)

        # --- Etapa 1: Inserir o E-mail ---
        logging.info("Procurando campo de e-mail...")
        campo_usuario = wait.until(EC.presence_of_element_located((By.ID, 'username-password')))
        campo_usuario.send_keys(user)
        
        logging.info("Procurando botão 'Continuar'...")
        # Assumindo que o ID que você encontrou para o botão é 'submit-button'
        driver.find_element(By.ID, 'submit-button').click()
        
        # --- Pausa Estratégica ---
        logging.info("Pausando por 15 segundos para aguardar o carregamento da página de senha e do CAPTCHA...")
        time.sleep(15)
        
        # --- Etapa 2: Inserir a Senha ---
        logging.info("Procurando campo de senha...")
        # Assumindo que o ID do campo de senha é 'password'
        campo_senha = wait.until(EC.presence_of_element_located((By.ID, 'password')))
        campo_senha.send_keys(password)
        
        # --- Etapa 3: Clicar em Entrar e Aguardar ---
        logging.info("Procurando botão final 'Entrar'...")
        # Assumindo que o ID do botão final é 'password-submit-button'
        driver.find_element(By.ID, 'password-submit-button').click()
        
        logging.info("Aguardando confirmação de login (até 60 segundos)...")
        
        long_wait = WebDriverWait(driver, 60)
        # Espera pelo elemento 'Caixa de entrada' para confirmar o sucesso do login.
        long_wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Caixa de entrada']")))
        
        logging.info("Login finalizado com sucesso!")
        return True
        
    except Exception as e:
        logging.error(f"Falha durante o processo de login: {e}")
        return False