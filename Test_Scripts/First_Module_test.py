import openai
import requests
from bs4 import BeautifulSoup

# Asegúrate de que tienes la última versión de la librería instalada:
# pip install --upgrade openai

openai.api_key = 'your api key'


url = "http://127.0.0.1:5500/WebScraperTest/Test_Scripts/index1.html"
headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

response = requests.get(url, headers=headers)

# Convertir a objeto BeautifulSoup
soup = BeautifulSoup(response.text, "html.parser")

# Extraer solo el texto limpio
texto = soup.get_text(separator="\n", strip=True)

# Guardar el texto en un archivo
with open("pagina.txt", "w", encoding="utf-8") as file:
    file.write(texto)

print("Texto extraído y guardado en pagina.txt")

# Cargar el texto extraído
with open("pagina.txt", "r", encoding="utf-8") as file:
    texto = file.read()

# Definir el modelo y los mensajes
response = openai.completions.create(
    model="gpt-4o-mini-2024-07-18",  # Asegúrate de usar el modelo correcto aquí
    prompt="Retorna la dirección principal a la que depositar",
    max_tokens=0
)

print(response.choices[0].text.strip())



# # Enviar el texto a la API de GPT
# response = openai.ChatCompletion.create(
#     model="gpt-4o-mini-2024-07-18",
#     messages=[{"role": "system", "content": "Retorna la dirección principal a la que depositar"},
#               {"role": "user", "content": texto}]
# )

# # Imprimir la respuesta
# print(response["choices"][0]["message"]["content"])
