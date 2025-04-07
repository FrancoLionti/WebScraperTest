from openai import OpenAI
import CryptoScamScraperTest
import json

# url = "http://127.0.0.1:5500/WebScraperTest/Test_Scripts/index1.html"
url = "http://dubblebitcoin.weebly.com"


scraper = CryptoScamScraperTest.CryptoScamScraper()
texto = scraper.scrape_site(url)

print(texto)

# Configura la API de DeepSeek
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="API KEY",
)

# Envía el contenido completo del HTML a la API de DeepSeek
completion = client.chat.completions.create(
    extra_headers={
        "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
        "X-Title": "<YOUR_SITE_NAME>",      # Optional. Site title for rankings on openrouter.ai.
    },
    extra_body={},
    model="deepseek/deepseek-chat-v3-0324:free",
    messages=[
        {
            "role": "user",
            "content": "From the following data structure scan all and get the wallet address in which the user should deposit: " + json.dumps(texto)
        }
    ]
)

# Imprime la respuesta de la API de DeepSeek
print(completion.choices[0].message.content)

# Cerrar el scraper
scraper.close()