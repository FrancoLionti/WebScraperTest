import requests
import time
import random
from CryptoScamScraper import logger, CryptoScamScraper
from pandas import read_csv as pd_read
from pandas import isna
from selenium.webdriver.support import expected_conditions as EC


def main():
    """Función principal para ejecutar el scraper"""
    # Configuración del correo electrónico temporal
    temp_email = "gadepor122@avulos.com"  # Cambiar por tu correo temporal
    temp_email_password = "elJulio3819+_!"  # Cambiar por tu contraseña
    Enlace_list=pd_read("WebScraperTest/Scam_adviser_sample.csv",sep=";",header=0)
    urls=[]
    for index, row in Enlace_list.iterrows():
        if not isna(row["Enlace"]) and row["Enlace"] != "":
            urls.append("https://" + row["Enlace"]);

    # Inicializar el scraper con el correo temporal
    scraper = CryptoScamScraper(
        temp_email=temp_email,
        temp_email_password=temp_email_password,
        use_proxy=False
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