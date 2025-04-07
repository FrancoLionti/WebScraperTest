from openai import OpenAI
import CryptoScamScraper
import json

# url = "http://127.0.0.1:5500/WebScraperTest/Test_Scripts/index1.html"
url = "http://dubblebitcoin.weebly.com"

scraper = CryptoScamScraper.CryptoScamScraper()
wallet_data = scraper.scrape_site(url)

print(f"Found {len(wallet_data['addresses'])} potential crypto addresses")

# Create a more informative prompt for the LLM
prompt = f"""
Analyze the following cryptocurrency website data to identify the main deposit address where users are instructed to send funds:

URL: {wallet_data.get('url', 'Unknown')}
Title: {wallet_data.get('title', 'Unknown')}

Found addresses:
"""

for addr in wallet_data['addresses']:
    prompt += f"\n- {addr}"
    for context in wallet_data['details'][addr][:2]:  # Limit to first 2 contexts for each address
        prompt += f"\n  Context: {context['text_context']}"
        if context['containing_elements']:
            element = context['containing_elements'][0]
            prompt += f"\n  Element: <{element['tag']} {' '.join([f'{k}=\"{v}\"' for k,v in element['attributes'].items()])}>"
            prompt += f"\n  Parents: {element['parents']}"

prompt += """

Based on the context and HTML elements, identify which cryptocurrency address is the main deposit address that users are instructed to send their funds to. 
Explain your reasoning and provide your confidence level.
"""

print("\nSending data to LLM...\n")

# Configura la API de DeepSeek
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="your api key",
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
            "content": prompt
        }
    ]
)

# Imprime la respuesta de la API de DeepSeek
print(completion.choices[0].message.content)

# Cerrar scraper
scraper.close()