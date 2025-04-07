from flask import Flask, request, jsonify
import openai
# import pandas as pd

# Enlace_list=pd.read_csv("WebScraperTest/Scam adviser sample.csv",sep=";",header=0)
# empty=[]

# for index, row in Enlace_list.iterrows():
#     if not pd.isna(row["Enlace"]) and row["Enlace"] != "":
#         Enlaces_completed = "https://" + row["Enlace"]
#         empty.append(Enlaces_completed)


# print(empty)

app = Flask(__name__)

# Configurar la clave de la API de OpenAI
openai.api_key = 'TU_CLAVE_DE_API'

@app.route('/procesar', methods=['POST'])
def procesar_texto():
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

if __name__ == '__main__':
    app.run(debug=True)
