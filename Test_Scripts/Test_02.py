from openai import OpenAI
import CryptoScamScraperTest02
import json

# url = "http://127.0.0.1:5500/WebScraperTest/Test_Scripts/index1.html"
url = "https://dubblebitcoin.weebly.com"

scraper = CryptoScamScraperTest02.CryptoScamScraper()

# Realizar el scraping
wallet_data = scraper.scrape_site(url)

# Estructurar el resultado para el LLM
structured_result = {
    "url": url,
    "wallets": []
}

for addr in wallet_data['addresses']:
    for context in wallet_data['details'][addr]:
        structured_result["wallets"].append({
            "address": addr,
            "div_html": context['div_html'],
            "surrounding_text": context['surrounding_text'],
            "text_context": context['text_context'],
            "parent_html": context['parent_html'],
            "parent_attributes": context['parent_attributes'],
            "sibling_text": context['sibling_text']
        })

# Guardar el resultado en un archivo JSON
output_file = "wallet_data.json"
with open(output_file, "w") as f:
    json.dump(structured_result, f, indent=4)

# Imprimir un resumen en la consola
print(f"Se encontraron {len(wallet_data['addresses'])} direcciones de billeteras.")
print(f"Resultados guardados en {output_file}")

# Cerrar el scraper
scraper.close()

# # Configura la API de DeepSeek
# client = OpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key="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",
# )

# # Envía el contenido completo del HTML a la API de DeepSeek
# completion = client.chat.completions.create(
#     extra_headers={
#         "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
#         "X-Title": "<YOUR_SITE_NAME>",      # Optional. Site title for rankings on openrouter.ai.
#     },
#     extra_body={},
#     model="deepseek/deepseek-chat-v3-0324:free",
#     messages=[
#         {
#             "role": "user",
#             "content": "From the following data structure, analyze the wallet addresses found and their surrounding HTML context to identify which wallet address a user is expected to deposit funds into. Tell me which wallet address is the deposit address for the scam and explain why by analyzing the HTML context: " + json.dumps(wallet_data)
#         }
#     ]
# )

# # Imprime la respuesta de la API de DeepSeek
# print(completion.choices[0].message.content)

# Cerrar el scraper
scraper.close()