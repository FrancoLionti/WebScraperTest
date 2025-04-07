import logging
import requests
import time
import random
import re
import openai
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# import GPTLoginHelper

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
        
    def setup_browser(self, headless=True):
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
    Metodo principal llamado desde el main
    -------------------------------------------------------------------------------------------------------------------
    """
    def gpt_start_scrape_test():
        # Obtener el texto desde la solicitud POST
        data = request.json
        texto = data.get('texto', '')

        # Llamar a la API de OpenAI
        response = openai.Completion.create(
            model="text-davinci-003",  # O el modelo que prefieras
            prompt=texto,
            max_tokens=100
        )

        # Extraer el texto generado por GPT
        gpt_respuesta = response.choices[0].text.strip()

        # Devolver la respuesta al frontend
        return jsonify({'respuesta': gpt_respuesta})

    def scrape_site_old(self, url):
        """Realiza scraping de un sitio utilizando requests y BeautifulSoup"""
        if not self.check_site_safety(url):
            logger.error(f"El sitio {url} ha sido marcado como inseguro. Abortando scraping.")
            return []
        
        try:
            logger.info(f"Iniciando scraping de {url}")
            
            # Updated headers to better mimic a real browser
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
                "Referer": "https://www.google.com/"
            })
            
            response = self.session.get(url, timeout=10)
            
            # Check for 403/401 status codes and fall back to browser if needed
            if response.status_code in [401, 403]:
                logger.warning(f"Acceso denegado (código {response.status_code}). Cambiando a modo navegador.")
                return self.scrape_with_browser(url)
            
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
            # Fall back to browser method after any exception
            try:
                logger.info("Intentando scraping con navegador como alternativa...")
                return self.scrape_with_browser(url)
            except Exception as e2:
                logger.error(f"También falló el scraping con navegador: {str(e2)}")
                return []

    def scrape_site(self, url):
        """Realiza scraping de un sitio utilizando requests y BeautifulSoup"""
        if not self.check_site_safety(url):
            logger.error(f"El sitio {url} ha sido marcado como inseguro. Abortando scraping.")
            return {'addresses': [], 'details': {}}
        
        try:
            # Your existing code...
            
            # Extraer direcciones de billetera
            wallet_data = self.extract_wallet_addresses(response.text)
            logger.info(f"Se encontraron {len(wallet_data['addresses'])} direcciones de billetera en {url}")
            
            # También buscamos en enlaces internos
            soup = BeautifulSoup(response.text, 'html.parser')
            internal_links = self.get_internal_links(soup, url)
            
            # Save original data
            all_addresses = wallet_data['addresses'].copy()
            all_details = wallet_data['details'].copy()
            
            # Limitar cantidad de enlaces internos para no sobrecargar
            internal_links = internal_links[:5]
            
            for link in internal_links:
                logger.info(f"Explorando enlace interno: {link}")
                time.sleep(random.uniform(2, 5))  # Pausa para no sobrecargar el servidor
                try:
                    sub_response = self.session.get(link, timeout=10)
                    sub_wallet_data = self.extract_wallet_addresses(sub_response.text)
                    
                    # Add new addresses
                    for addr in sub_wallet_data['addresses']:
                        if addr not in all_addresses:
                            all_addresses.append(addr)
                    
                    # Merge details
                    for addr, contexts in sub_wallet_data['details'].items():
                        if addr in all_details:
                            all_details[addr].extend(contexts)
                        else:
                            all_details[addr] = contexts
                    
                    logger.info(f"Se encontraron {len(sub_wallet_data['addresses'])} direcciones adicionales en {link}")
                except Exception as e:
                    logger.error(f"Error al explorar enlace interno {link}: {str(e)}")
            
            result = {
                'addresses': all_addresses,
                'details': all_details,
                'url': url,
                'title': soup.title.string if soup.title else "No title"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error al hacer scraping de {url}: {str(e)}")
            # Fall back to browser method after any exception
            try:
                logger.info("Intentando scraping con navegador como alternativa...")
                return self.scrape_with_browser(url)
            except Exception as e2:
                logger.error(f"También falló el scraping con navegador: {str(e2)}")
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
            wallets = self.extract_wallet_addresses(page_source)
            
            if wallets:
                logger.info(f"Se encontraron {len(wallets)} direcciones de billetera mediante navegador")
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
                            sub_wallets = self.extract_wallet_addresses(sub_page_source)
                            wallets.extend(sub_wallets)
                        except Exception as e:
                            logger.error(f"Error al explorar enlace interno con navegador {link}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error al buscar enlaces internos: {str(e)}")
                    
            return list(set(wallets))
                
        except Exception as e:
            logger.error(f"Error al hacer scraping con navegador de {url}: {str(e)}")
            return []
        finally:
            # Capturar screenshot para análisis posterior
            if self.browser:
                try:
                    self.browser.save_screenshot(f"screenshot_{int(time.time())}.png")
                except:
                    pass
    
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


# Esta vuela por ahora
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

    def extract_wallet_addresses_old(self, html_content):
        """Extrae direcciones de billeteras de criptomonedas del contenido HTML"""
        wallets = []
        
        for pattern in self.wallet_patterns:
            matches = re.findall(pattern, html_content)
            wallets.extend(matches)
            
        return wallets
        
    def extract_wallet_addresses(self, html_content):
        
        """
        Extrae direcciones de billeteras de criptomonedas del contenido HTML
        junto con su contexto circundante para mejor análisis
        """
        
        wallet_data = {}
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Convertir el HTML a texto para búsqueda por regex
        text_content = soup.get_text()
        html_lines = html_content.split('\n')
        
        for pattern in self.wallet_patterns:
            # Buscar en el HTML completo
            for match in re.finditer(pattern, html_content):
                address = match.group(0)
                if address not in wallet_data:
                    wallet_data[address] = []
                
                # Encontrar el elemento HTML que contiene esta dirección
                line_num = 1
                char_count = 0
                match_line = 0
                match_pos = 0
                
                # Encontrar la línea y posición del match
                for line in html_lines:
                    new_char_count = char_count + len(line) + 1  # +1 for newline
                    if char_count <= match.start() < new_char_count:
                        match_line = line_num
                        match_pos = match.start() - char_count
                        break
                    char_count = new_char_count
                    line_num += 1
                
                # Obtener contexto (5 líneas antes y después)
                start_line = max(1, match_line - 5)
                end_line = min(len(html_lines), match_line + 5)
                context_html = '\n'.join(html_lines[start_line-1:end_line])
                
                # Buscar el elemento específico que contiene la dirección
                containing_elements = []
                for tag in soup.find_all():
                    if address in tag.get_text():
                        # Get parent elements for better context
                        parents = []
                        parent = tag.parent
                        for _ in range(3):  # Get up to 3 levels of parents
                            if parent and parent.name != '[document]':
                                parents.append(parent.name)
                                parent = parent.parent
                            else:
                                break
                        
                        # Get tag attributes that might be useful
                        attrs = {}
                        for attr_name, attr_value in tag.attrs.items():
                            if isinstance(attr_value, list):
                                attrs[attr_name] = ' '.join(attr_value)
                            elif isinstance(attr_value, str):
                                attrs[attr_name] = attr_value
                        
                        element_info = {
                            'tag': tag.name,
                            'parents': '->'.join(parents[::-1]) if parents else 'none',
                            'attributes': attrs,
                            'surrounding_text': tag.get_text().strip()[:100]  # Get first 100 chars
                        }
                        containing_elements.append(element_info)
                
                # Extract text context (text before and after the address)
                text_window = 100  # characters before and after
                match_text_pos = text_content.find(address)
                if match_text_pos >= 0:
                    start_pos = max(0, match_text_pos - text_window)
                    end_pos = min(len(text_content), match_text_pos + len(address) + text_window)
                    text_context = text_content[start_pos:end_pos]
                else:
                    text_context = "Context not found"
                
                wallet_context = {
                    'address': address,
                    'html_context': context_html,
                    'text_context': text_context,
                    'containing_elements': containing_elements,
                    'line_number': match_line
                }
                
                wallet_data[address].append(wallet_context)
        
        # Format the data for easier consumption by LLM
        result = {
            'addresses': list(wallet_data.keys()),
            'details': wallet_data
        }
        
        return result


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

# if __name__ == "__main__":
#     CryptoScamScraper()