from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import Annotated

load_dotenv(override=True)  # Se cargan las variables de entorno
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("<Missing OPENAI_API_KEY environment variable>")
openai = OpenAI(api_key=api_key) 

aiModel = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Default to gpt-3.5-turbo
app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")  # Archivos estáticos

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("home.html", {'request': request})

chat_log = [{'role': 'system',  # Mensaje de sistema para establecer el contexto
            'content': 'Eres un chatbot culturalmente sensible y educativo que hace parte del proyecto ABLE, especializado en ofrecer información precisa, respetuosa y profunda sobre las minorías en Colombia, como la comunidad gay, las mujeres, raizales e indígenas de Colombia, como los pueblos Muisca, Arhuaco, Yagua y Wayuu. Fuiste desarrollado como parte de un proyecto para fortalecer el conocimiento, respeto y valoración de la diversidad étnica del país. No puedes recibir emojis o lenguaje ofensivo. Tu objetivo es responder preguntas de usuarios interesados en estas minorías y culturas, ayudándoles a entender su historia, organización social, espiritualidad, idioma, alimentación, vestimenta, desafíos actuales y procesos de resistencia. Tus respuestas deben ser claras, empáticas, completas y culturalmente conscientes. Siempre reconoces la autonomía, la diversidad interna y los procesos históricos propios de cada minoría y comunidad. Puedes responder preguntas generales o específicas sobre cada comunidad, etnia o minoría. Puedes comparar prácticas culturales entre comunidades si el usuario lo solicita. Puedes explicar conceptos asociados a cada comunidad o grupo minoritario. Puedes orientar a usuarios sobre cómo acceder a información confiable o respetar a las comunidades y culturas, si desean visitarlas. Puedes funcionar como herramienta educativa para estudiantes, agentes culturales o usuarios de ABLE. Tu tono es respetuoso, informativo y empático, evitando estereotipos y generalizaciones, siendo honesto cuando careces de la información. Siempre fomentas el respeto y la valoración de la diversidad cultural.'}]

chat_responses = []

@app.websocket("/ws")
async def chat(websocket: WebSocket):
    await websocket.accept()

    while True:
        user_input = await websocket.receive_text()

        chat_log.append({'role': 'user', 'content': user_input})
        chat_responses.append(user_input)

        try:
            response = openai.chat.completions.create(
                model=aiModel,
                messages=chat_log,
                temperature=0.6,
                max_tokens=500,
                stream=True  
            )

            ai_response = ""
            collected_chunks = []
            current_message = ""

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    collected_chunks.append(content)
                    current_message += content
                    ai_response += content
                    
                    # Enviar bloques de texto completos
                    if " " in content or "." in content or "," in content or "\n" in content:
                        await websocket.send_text(current_message)
                        current_message = ""
            
            # Enviar cualquier texto restante
            if current_message:
                await websocket.send_text(current_message)
            
            chat_log.append({'role': 'assistant', 'content': ai_response})
            chat_responses.append(ai_response)

        except Exception as e:
            await websocket.send_text(f"Error: {str(e)}")
            break


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
