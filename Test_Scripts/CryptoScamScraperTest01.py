import logging
import requests
import time
import random
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
import undetected_chromedriver as uc

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("crypto_scam_scraper_browser")

class CryptoScamScraper:
    def __init__(self, temp_email=None, temp_email_password=None, use_proxy=False, use_gpt=False, gpt_api_key=None):  
        """
        Testing01

        Inicializa el scraper con opciones configurables
        
        Args:
            temp_email (str, optional): Dirección de correo temporal a utilizar para registros
            temp_email_password (str, optional): Contraseña para el correo temporal
            use_proxy (bool, optional): Si se debe usar un proxy 
        """
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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
        
        # Integración con GPT
        self.use_gpt = use_gpt
        self.gpt_api_key = gpt_api_key

    """ Setup de proxy y navegador """

    def setup_proxy(self):
        """Configura un proxy para añadir una capa adicional de seguridad"""
        # Implementar proxy rotation o algo por el estilo para evitar detección
        # Ojo que esto es un proxy ficticio todavía tengo que implementar esto
        # Bueno esto acaba de cobrar mucha mas relevancia, de manera que tengo que 
        # hacer muchas requests lo mejor va a ser tener proxies para rotar y que no me 
        # bloqueen la ip del browser
        self.proxy = {
            'http': 'http://user:pass@proxy.example.com:8080',
            'https': 'https://user:pass@proxy.example.com:8080'
        }
        self.session.proxies.update(self.proxy)
        logger.info("Proxy configurado correctamente")
        
    def setup_browser(self, headless=False):
        """Configura un navegador con undetected_chromedriver"""
        try:
            chrome_options = uc.ChromeOptions()
            if headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.browser = uc.Chrome(options=chrome_options)
            self.browser.set_page_load_timeout(30)
            
            logger.info("Navegador configurado correctamente con undetected_chromedriver")
            return True
        except Exception as e:
            logger.error(f"Error al configurar el navegador: {str(e)}")
            return False
        
    def check_site_safety(self, url):
        """Verifica si una URL es conocida por ser maliciosa usando servicios externos"""
        # Acà se integraría con servicios como Google Safe Browsing o VirusTotal
        # Para este ejemplo, simplemente hacemos una comprobación básica
        suspicious_keywords = ['hack', 'malware', 'virus', 'free-bitcoin', 'get-rich']
        
        if any(keyword in url.lower() for keyword in suspicious_keywords):
            logger.warning(f"URL potencialmente peligrosa detectada: {url}")
            return False
            
        logger.info(f"URL verificada preliminarmente: {url}")
        return True
        
    """
    -------------------------------------------------------------------------------------------------------------------
    Metodos principales llamados desde el main
    -------------------------------------------------------------------------------------------------------------------
    """

    def scrape_site(self, url):
        """
        Descarga el HTML completo de un sitio web y extrae las direcciones de billeteras.
        Maneja la intervención de Cloudflare si es detectada.
        """
        try:
            # Configurar opciones de Chrome
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")

            # Inicializar el navegador con undetected_chromedriver
            driver = uc.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)

            logger.info(f"Accediendo a {url}")
            driver.get(url)

            # Esperar a que la página cargue completamente
            time.sleep(10)

            # Verificar si la página está intervenida por Cloudflare
            page_source = driver.page_source
            if "Un momento…" in page_source or "Verificar que usted es un ser humano" in page_source:
                logger.warning("Intervención de Cloudflare detectada. Esperando más tiempo...")
                time.sleep(15)  # Esperar más tiempo para que Cloudflare complete la verificación
                page_source = driver.page_source

                # Si aún está intervenido, intentar recargar la página
                if "Un momento…" in page_source or "Verificar que usted es un ser humano" in page_source:
                    logger.warning("Cloudflare sigue interviniendo. Recargando la página...")
                    driver.refresh()
                    time.sleep(10)
                    page_source = driver.page_source

            driver.quit()

            # Procesar el contenido HTML completo
            result = self.extract_wallet_addresses(page_source)
            if not result['addresses']:
                logger.warning("No se encontraron direcciones en el scraping inicial")

            return result

        except Exception as e:
            logger.error(f"Error en undetected_chromedriver: {str(e)}")
            if driver:
                driver.quit()
            return {'addresses': [], 'details': {}}

    def scrape_with_browser(self, url):
        """Utiliza Selenium para sitios que requieren JavaScript o login"""
        if self.browser is None:
            self.setup_browser(headless=False)  # Set to False for difficult sites
            
        try:
            logger.info(f"Accediendo a {url} con navegador automatizado")
            self.browser.get(url)
            # Wait longer for the page to fully load
            time.sleep(5)
            
            # Execute JavaScript to scroll down the page to trigger lazy loading
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Extraer el contenido actualizado después de cualquier interacción
            page_source = self.browser.page_source
            wallet_data = self.extract_wallet_addresses(page_source)
            
            # Check if we found wallets
            if wallet_data['addresses']:
                logger.info(f"Se encontraron {len(wallet_data['addresses'])} direcciones de billetera mediante navegador")
            else:
                logger.info("No se encontraron direcciones de billeteras mediante navegador")
                
                # Try navigating to subpages
                try:
                    all_links = self.browser.find_elements(By.TAG_NAME, "a")
                    internal_links = []
                    
                    # Get up to 3 internal links
                    for link in all_links[:10]:
                        href = link.get_attribute("href")
                        if href and url in href and href not in internal_links:
                            internal_links.append(href)
                            if len(internal_links) >= 3:
                                break
                    
                    # Visit internal pages
                    for link in internal_links:
                        try:
                            logger.info(f"Explorando enlace interno con navegador: {link}")
                            self.browser.get(link)
                            time.sleep(3)
                            sub_page_source = self.browser.page_source
                            sub_wallet_data = self.extract_wallet_addresses(sub_page_source)
                            
                            # Merge the results
                            wallet_data['addresses'].extend(sub_wallet_data['addresses'])
                            for addr, details in sub_wallet_data['details'].items():
                                if addr in wallet_data['details']:
                                    wallet_data['details'][addr].extend(details)
                                else:
                                    wallet_data['details'][addr] = details
                        except Exception as e:
                            logger.error(f"Error al explorar enlace interno con navegador {link}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error al buscar enlaces internos: {str(e)}")
                    
            return wallet_data
                
        except Exception as e:
            logger.error(f"Error al hacer scraping con navegador de {url}: {str(e)}")
            return {'addresses': [], 'details': {}}
        finally:
            # Capturar screenshot para análisis posterior
            if self.browser:
                try:
                    self.browser.save_screenshot(f"screenshot_{int(time.time())}.png")
                except:
                    pass

    def extract_wallet_addresses(self, html_content):
        """
        Extrae direcciones de billeteras de criptomonedas del contenido HTML
        junto con su contexto circundante.
        """
        wallet_data = {}
        try:
            # Analizar el HTML con BeautifulSoup
            logger.info("Iniciando el análisis del contenido HTML con BeautifulSoup")
            soup = BeautifulSoup(html_content, 'html.parser')

            # Convertir el HTML a texto para búsqueda por regex
            text_content = soup.get_text(separator=' ', strip=True)
            logger.info("Contenido HTML convertido a texto para búsqueda de patrones")

            for pattern in self.wallet_patterns:
                logger.info(f"Buscando direcciones con el patrón: {pattern}")
                matches = list(re.finditer(pattern, text_content))
                logger.info(f"Se encontraron {len(matches)} coincidencias para el patrón {pattern}")

                for match in matches:
                    address = match.group(0)
                    if address not in wallet_data:
                        wallet_data[address] = []

                    # Buscar el elemento HTML que contiene la dirección
                    try:
                        for tag in soup.find_all(text=re.compile(re.escape(address)), limit=5):
                            containing_tag = tag.parent
                            if containing_tag:
                                parent = containing_tag.parent
                                wallet_context = {
                                    'div_html': str(containing_tag)[:500],
                                    'surrounding_text': containing_tag.get_text(strip=True)[:200],
                                    'text_context': text_content[max(0, match.start() - 50):match.end() + 50],
                                    'parent_html': str(parent)[:500] if parent else None
                                }
                                wallet_data[address].append(wallet_context)
                                break

                    except Exception as e:
                        logger.error(f"Error al procesar el contexto de la dirección {address}: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Error en extract_wallet_addresses: {str(e)}")
            return {'addresses': [], 'details': {}}

        # Formatear los datos para facilitar el consumo
        result = {
            'addresses': list(wallet_data.keys()),
            'details': wallet_data
        }

        logger.info(f"Extracción completada. Se encontraron {len(result['addresses'])} direcciones de billeteras.")
        return result

    """ Context manager para el scraper """
    
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

# if __name__ == "__main__":
#     CryptoScamScraper()