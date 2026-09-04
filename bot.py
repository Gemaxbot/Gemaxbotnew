import os
import json
import urllib.request
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SYSTEM_INSTRUCTION = (
    "Eres GemaxBot, el analista senior oficial de la comunidad @SimpleGemax. "
    "Hablas con elegancia, firmeza y alta seguridad técnica. Sé ultra conciso "
    "y aclara brevemente al final que es contenido educativo."
)

def consultar_gemini(prompt: str) -> str:
    full_prompt = f"{SYSTEM_INSTRUCTION}\n\nPregunta: {prompt}"
    # Usamos la API de Vertex/Generative Language compatible con proyectos de GCP
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    # Si la clave empieza por AQ, va como Bearer token; si no, como query param
    if GEMINI_API_KEY.startswith("AQ"):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {GEMINI_API_KEY}'
        }
    else:
        url = f"{url}?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}

    data = {"contents": [{"parts": [{"text": full_prompt}]}]}
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as err:
        return f"Error técnico de IA: {str(err)}"

def enviar_mensaje(chat_id, texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": texto, "parse_mode": "Markdown"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as ex:
        print(f"Error al enviar mensaje: {ex}")

@app.route("/")
def home():
    return "GemaxBot está activo y operando en la nube."

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = json.loads(json_str)
    
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        texto_usuario = update["message"]["text"]
        
        if texto_usuario.startswith("/start"):
            respuesta = "📈 *GemaxBot activo.*\n\nEscribe tu consulta o usa `/analisis btc`."
        elif texto_usuario.startswith("/analisis"):
            activo = texto_usuario.replace("/analisis", "").strip() or "BTC"
            analisis = consultar_gemini(f"Análisis técnico breve de {activo}")
            respuesta = f"📊 *Análisis Técnico: {activo.upper()}*\n\n{analisis}"
        else:
            respuesta = consultar_gemini(texto_usuario)
        
        enviar_mensaje(chat_id, respuesta)
    
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
          
