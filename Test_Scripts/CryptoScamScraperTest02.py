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
        Testing02

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
        """Configura un navegador con opciones de seguridad para sitios que requieren JavaScript"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Opciones de seguridad pero permitiendo JS y cookies para sitios que los requieren
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        
        # Remove these lines as they block JavaScript and cookies
        # chrome_options.add_argument("--disable-javascript")
        # chrome_options.add_argument("--disable-cookies")
        
        # Set a realistic user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
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
            # Acà podrías integrar un servicio de correo temporal
            # Por ahora, generamos un correo aleatorio ficticio
            # random_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
            # self.temp_email = f"{random_id}@tempmail.example.com"
            # logger.info(f"Correo temporal generado: {self.temp_email}")
            self.temp_email = ""

        return self.temp_email
        
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
        # Configurar opciones de Chrome
        chrome_options = Options()
        
        # Especificar la ruta exacta al binario de Chrome
        chrome_options.binary_location = "/usr/bin/google-chrome"
        
        # Opciones para hacer que Chrome sea menos detectable
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            # Inicializar el navegador
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            # Añadir un timeout para cargar la página
            driver.set_page_load_timeout(30)

            # Cargar la página
            driver.get(url)

            # Esperar un tiempo aleatorio para que cargue completamente el JS
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )

            # Obtener el contenido de la página
            page_source = driver.page_source

            # Cerrar el navegador
            driver.quit()

            # Procesar el contenido HTML para extraer las billeteras con contexto
            return self.extract_wallet_addresses(page_source)

        except Exception as e:
            if 'driver' in locals():
                driver.quit()
            logger.error(f"Error en Selenium: {str(e)}")
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
        junto con su contexto circundante para mejor análisis.
        """
        wallet_data = {}
        soup = BeautifulSoup(html_content, 'html.parser')

        # Convertir el HTML a texto para búsqueda por regex
        text_content = soup.get_text()

        for pattern in self.wallet_patterns:
            # Buscar en el HTML completo
            for match in re.finditer(pattern, text_content):  # Cambiado a text_content para asegurar que se busque en el texto visible
                address = match.group(0)

                if address not in wallet_data:
                    wallet_data[address] = []

                # Encontrar el elemento HTML que contiene esta dirección
                containing_element = None
                for tag in soup.find_all(string=re.compile(re.escape(address))):
                    containing_element = tag.parent
                    break

                # Extraer el HTML del contenedor y su contexto
                if containing_element:
                    div_html = str(containing_element)
                    surrounding_text = containing_element.get_text(strip=True)[:200]  # Primeros 200 caracteres

                    # Capturar el contenedor padre del contenedor actual (abuelo)
                    parent_element = containing_element.find_parent()
                    parent_html = str(parent_element) if parent_element else "No se encontró contenedor padre"
                    parent_attributes = parent_element.attrs if parent_element else {}

                    # Capturar texto de los elementos hermanos
                    sibling_text = " | ".join([sibling.get_text(strip=True) for sibling in containing_element.find_next_siblings()[:3]])
                else:
                    div_html = "No se encontró un contenedor adecuado"
                    surrounding_text = "No se encontró texto circundante"
                    parent_html = "No se encontró contenedor padre"
                    parent_attributes = {}
                    sibling_text = "No se encontraron elementos hermanos"

                # Extraer contexto adicional del texto
                text_window = 100  # caracteres antes y después
                match_text_pos = text_content.find(address)
                if match_text_pos >= 0:
                    start_pos = max(0, match_text_pos - text_window)
                    end_pos = min(len(text_content), match_text_pos + len(address) + text_window)
                    text_context = text_content[start_pos:end_pos]
                else:
                    text_context = "Contexto no encontrado"

                wallet_context = {
                    'address': address,
                    'div_html': div_html,
                    'parent_html': parent_html,
                    'parent_attributes': parent_attributes,
                    'sibling_text': sibling_text,
                    'text_context': text_context,
                    'surrounding_text': surrounding_text
                }

                wallet_data[address].append(wallet_context)

        # Formatear los datos para facilitar el consumo por el LLM
        result = {
            'addresses': list(wallet_data.keys()),
            'details': wallet_data
        }

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