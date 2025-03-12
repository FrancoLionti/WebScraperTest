import requests
import time
import random
import logging
import re
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("crypto_scam_scraper")

class CryptoScamScraper:
    def __init__(self, temp_email=None, temp_email_password=None, use_proxy=False):
        """
        Inicializa el scraper con opciones configurables
        
        Args:
            temp_email (str, optional): Dirección de correo temporal a utilizar para registros
            temp_email_password (str, optional): Contraseña para el correo temporal
            use_proxy (bool, optional): Si se debe usar un proxy 
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.wallet_patterns = [
            # Bitcoin
            r'(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}',
            # Ethereum
            r'0x[a-fA-F0-9]{40}',
            # Binance Smart Chain (same format as Ethereum)
            r'0x[a-fA-F0-9]{40}',
            # Ripple
            r'r[0-9a-zA-Z]{24,34}',
            # Litecoin
            r'[LM][a-km-zA-HJ-NP-Z1-9]{26,33}',
            # Dogecoin
            r'D{1}[5-9A-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-z]{32}'
        ]
        self.browser = None
        self.proxy = None
        
        # Almacenar información del correo electrónico temporal
        self.temp_email = temp_email
        self.temp_email_password = temp_email_password or f"Temp{random.randint(10000, 99999)}!"
        
        if use_proxy:
            self.setup_proxy()
        
    def setup_proxy(self):
        """Configura un proxy para añadir una capa adicional de seguridad"""
        # Implementar proxy rotation o algo por el estilo para evitar detección
        # Ojo que esto es un proxy ficticio todavía tengo que implementar esto
        self.proxy = {
            'http': 'http://user:pass@proxy.example.com:8080',
            'https': 'https://user:pass@proxy.example.com:8080'
        }
        self.session.proxies.update(self.proxy)
        logger.info("Proxy configurado correctamente")
        
    def setup_browser(self, headless=True):
        """Configura un navegador con opciones de seguridad para sitios que requieren JavaScript"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
        # Opciones de seguridad
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-site-isolation-trials")
        
        # Bloquear JavaScript potencialmente peligroso
        chrome_options.add_argument("--disable-javascript")
        
        # Bloquear cookies
        chrome_options.add_argument("--disable-cookies")
        
        # Desactivar autoguardado de contraseñas
        chrome_options.add_experimental_option(
            "prefs", {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            }
        )
        
        # Configurar proxy si está habilitado
        if self.proxy:
            chrome_options.add_argument(f"--proxy-server={self.proxy['https']}")
        
        self.browser = webdriver.Chrome(options=chrome_options)
        self.browser.set_page_load_timeout(30)  # Tiempo máximo de carga para evitar cuelgues
        logger.info("Navegador configurado correctamente")
        
    def get_temp_email(self):
        """Retorna el correo electrónico temporal configurado o genera uno nuevo"""
        if not self.temp_email:
            # Aquí podrías integrar un servicio de correo temporal
            # Por ahora, generamos un correo aleatorio ficticio
            random_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
            self.temp_email = f"{random_id}@tempmail.example.com"
            logger.info(f"Correo temporal generado: {self.temp_email}")
        
        return self.temp_email
        
    def check_site_safety(self, url):
        """Verifica si una URL es conocida por ser maliciosa usando servicios externos"""
        # Aquí se integraría con servicios como Google Safe Browsing o VirusTotal
        # Para este ejemplo, simplemente hacemos una comprobación básica
        suspicious_keywords = ['hack', 'malware', 'virus', 'free-bitcoin', 'get-rich']
        
        if any(keyword in url.lower() for keyword in suspicious_keywords):
            logger.warning(f"URL potencialmente peligrosa detectada: {url}")
            return False
            
        logger.info(f"URL verificada preliminarmente: {url}")
        return True
        
    def scrape_site(self, url):
        """Realiza scraping de un sitio utilizando requests y BeautifulSoup"""
        if not self.check_site_safety(url):
            logger.error(f"El sitio {url} ha sido marcado como inseguro. Abortando scraping.")
            return []
            
        try:
            logger.info(f"Iniciando scraping de {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Verificar si la página requiere inicio de sesión o registro
            if self.requires_login(response.text):
                logger.info(f"El sitio {url} requiere inicio de sesión. Cambiando a modo navegador.")
                return self.scrape_with_browser(url)
                
            # Extraer direcciones de billetera
            wallets = self.extract_wallet_addresses(response.text)
            logger.info(f"Se encontraron {len(wallets)} direcciones de billetera en {url}")
            
            # También buscamos en enlaces internos
            soup = BeautifulSoup(response.text, 'html.parser')
            internal_links = self.get_internal_links(soup, url)
            
            # Limitar cantidad de enlaces internos para no sobrecargar
            internal_links = internal_links[:5]
            
            for link in internal_links:
                logger.info(f"Explorando enlace interno: {link}")
                time.sleep(random.uniform(2, 5))  # Pausa para no sobrecargar el servidor
                try:
                    sub_response = self.session.get(link, timeout=10)
                    sub_wallets = self.extract_wallet_addresses(sub_response.text)
                    wallets.extend(sub_wallets)
                    logger.info(f"Se encontraron {len(sub_wallets)} direcciones adicionales en {link}")
                except Exception as e:
                    logger.error(f"Error al explorar enlace interno {link}: {str(e)}")
                    
            return list(set(wallets))  # Eliminamos duplicados
            
        except Exception as e:
            logger.error(f"Error al hacer scraping de {url}: {str(e)}")
            return []
            
    def requires_login(self, html_content):
        """Detecta si una página requiere inicio de sesión o registro"""
        login_indicators = [
            'iniciar sesión', 'login', 'sign in', 'acceder', 'register',
            'registrarse', 'create account', 'crear cuenta'
        ]
        
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text().lower()
        
        # Buscar formularios
        forms = soup.find_all('form')
        
        # Verificar si hay formularios con campos de entrada que parecen de login/registro
        for form in forms:
            inputs = form.find_all('input')
            input_types = [inp.get('type', '').lower() for inp in inputs]
            input_names = [inp.get('name', '').lower() for inp in inputs]
            
            if 'password' in input_types or 'password' in input_names:
                return True
                
        # Verificar texto indicativo de login/registro
        return any(indicator in text_content for indicator in login_indicators)
        
    def scrape_with_browser(self, url):
        """Utiliza Selenium para sitios que requieren JavaScript o login"""
        if self.browser is None:
            self.setup_browser()
            
        try:
            logger.info(f"Accediendo a {url} con navegador automatizado")
            self.browser.get(url)
            time.sleep(3)  # Esperar a que la página cargue completamente
            
            # Verificar si hay formulario de registro
            if self.has_registration_form():
                logger.info("Detectado formulario de registro. Intentando registrarse.")
                self.register_account()
                
            # Verificar si hay formulario de login
            elif self.has_login_form():
                logger.info("Detectado formulario de login. No es posible continuar sin credenciales.")
                # Aquí podrías implementar lógica para usar credenciales si las tienes
                
            # Extraer el contenido actualizado después de cualquier interacción
            page_source = self.browser.page_source
            wallets = self.extract_wallet_addresses(page_source)
            
            return wallets
            
        except Exception as e:
            logger.error(f"Error al hacer scraping con navegador de {url}: {str(e)}")
            return []
        finally:
            # Capturar screenshot para análisis posterior
            if self.browser:
                self.browser.save_screenshot(f"screenshot_{int(time.time())}.png")
                
    def has_registration_form(self):
        """Detecta si hay un formulario de registro en la página actual"""
        try:
            registration_indicators = [
                "//button[contains(text(), 'Registrar')]",
                "//button[contains(text(), 'Register')]",
                "//button[contains(text(), 'Sign up')]",
                "//button[contains(text(), 'Crear cuenta')]",
                "//input[@type='submit' and contains(@value, 'Register')]",
                "//input[@type='submit' and contains(@value, 'Registrar')]"
            ]
            
            for indicator in registration_indicators:
                try:
                    if self.browser.find_elements(By.XPATH, indicator):
                        return True
                except:
                    continue
                    
            return False
            
        except Exception as e:
            logger.error(f"Error al verificar formulario de registro: {str(e)}")
            return False
            
    def has_login_form(self):
        """Detecta si hay un formulario de login en la página actual"""
        try:
            login_indicators = [
                "//button[contains(text(), 'Login')]",
                "//button[contains(text(), 'Iniciar')]",
                "//button[contains(text(), 'Sign in')]",
                "//button[contains(text(), 'Acceder')]",
                "//input[@type='submit' and contains(@value, 'Login')]",
                "//input[@type='submit' and contains(@value, 'Iniciar')]"
            ]
            
            for indicator in login_indicators:
                try:
                    if self.browser.find_elements(By.XPATH, indicator):
                        return True
                except:
                    continue
                    
            return False
            
        except Exception as e:
            logger.error(f"Error al verificar formulario de login: {str(e)}")
            return False
            
    def register_account(self):
        """Intenta registrar una cuenta con correo temporal"""
        try:
            # Obtener correo temporal
            email = self.get_temp_email()
            password = self.temp_email_password
            
            # Buscar campos de entrada comunes
            email_fields = [
                "//input[@type='email']",
                "//input[@name='email']",
                "//input[contains(@id, 'email')]",
                "//input[contains(@name, 'mail')]"
            ]
            
            password_fields = [
                "//input[@type='password']",
                "//input[@name='password']",
                "//input[contains(@id, 'password')]",
                "//input[contains(@name, 'pass')]"
            ]
            
            # Intentar encontrar y completar campo de email
            for field in email_fields:
                try:
                    email_input = WebDriverWait(self.browser, 5).until(
                        EC.element_to_be_clickable((By.XPATH, field))
                    )
                    email_input.clear()
                    email_input.send_keys(email)
                    logger.info("Campo de email completado")
                    break
                except:
                    continue
                    
            # Intentar encontrar y completar campo de contraseña
            for field in password_fields:
                try:
                    password_input = WebDriverWait(self.browser, 5).until(
                        EC.element_to_be_clickable((By.XPATH, field))
                    )
                    password_input.clear()
                    password_input.send_keys(password)
                    logger.info("Campo de contraseña completado")
                    break
                except:
                    continue
                    
            # Buscar y hacer clic en el botón de registro
            register_buttons = [
                "//button[contains(text(), 'Registrar')]",
                "//button[contains(text(), 'Register')]",
                "//button[contains(text(), 'Sign up')]",
                "//button[contains(text(), 'Crear')]",
                "//input[@type='submit' and contains(@value, 'Register')]"
            ]
            
            for button in register_buttons:
                try:
                    register_btn = WebDriverWait(self.browser, 5).until(
                        EC.element_to_be_clickable((By.XPATH, button))
                    )
                    register_btn.click()
                    logger.info("Formulario de registro enviado")
                    
                    # Esperar a que se complete el registro
                    time.sleep(5)
                    return True
                except:
                    continue
                    
            logger.warning("No se pudo completar el proceso de registro")
            return False
            
        except Exception as e:
            logger.error(f"Error durante el proceso de registro: {str(e)}")
            return False
            
    def extract_wallet_addresses(self, html_content):
        """Extrae direcciones de billeteras de criptomonedas del contenido HTML"""
        wallets = []
        
        for pattern in self.wallet_patterns:
            matches = re.findall(pattern, html_content)
            wallets.extend(matches)
            
        return wallets
        
    def get_internal_links(self, soup, base_url):
        """Extrae enlaces internos de la página"""
        internal_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/'):
                # Convertir ruta relativa a absoluta
                if base_url.endswith('/'):
                    internal_links.append(base_url[:-1] + href)
                else:
                    internal_links.append(base_url + href)
            elif href.startswith(base_url):
                internal_links.append(href)
                
        return internal_links
        
    def close(self):
        """Cierra todas las conexiones y sesiones"""
        if self.browser:
            self.browser.quit()
        self.session.close()
        logger.info("Scraper cerrado correctamente")
        
    def save_results(self, wallets, filename="wallets.txt"):
        """Guarda las direcciones de billeteras encontradas en un archivo"""
        with open(filename, 'w') as f:
            for wallet in wallets:
                f.write(f"{wallet}\n")
        logger.info(f"Resultados guardados en {filename}")


def main():
    """Función principal para ejecutar el scraper"""
    # Configuración del correo electrónico temporal
    temp_email = "tucorreo@temporal.com"  # Cambiar por tu correo temporal
    temp_email_password = "ContraseñaSegura123"  # Cambiar por tu contraseña
    
    # Lista de URLs a escanear
    urls = [
        # Colocar aquí las URLs a escanear
        # "https://ejemplo-estafa-cripto.com",
        # "https://otro-sitio-sospechoso.net"
    ]
    
    # Inicializar el scraper con el correo temporal
    scraper = CryptoScamScraper(
        temp_email=temp_email,
        temp_email_password=temp_email_password,
        use_proxy=True
    )
    
    try:
        all_wallets = []
        for url in urls:
            logger.info(f"Iniciando análisis de {url}")
            wallets = scraper.scrape_site(url)
            all_wallets.extend(wallets)
            
            # Pausa para evitar detección
            time.sleep(random.uniform(5, 10))
            
        # Eliminar duplicados
        unique_wallets = list(set(all_wallets))
        
        # Guardar resultados
        scraper.save_results(unique_wallets)
        logger.info(f"Proceso completado. Se encontraron {len(unique_wallets)} direcciones únicas.")
        
    except Exception as e:
        logger.error(f"Error en el proceso principal: {str(e)}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()