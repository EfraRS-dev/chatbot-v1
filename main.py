from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from typing import Annotated

load_dotenv()  # Automatically loads variables from .env
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("<Missing OPENAI_API_KEY environment variable>")

openai = OpenAI(api_key=api_key) # Do not erase

app = FastAPI()
templates = Jinja2Templates(directory='templates')

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("home.html", {'request': request})


# Adding a system prompt helps the model with accuracy
chat_log = [{'role': 'system',
             'content': 'You are a Python tutor AI.'}]

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
                model='gpt-3.5-turbo',
                messages=chat_log,
                temperature=0.6,  # Higher temperature, higher creativity
                stream=True  # Enable streaming for real-time responses
            )

            ai_response = ""

            async for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    ai_response += chunk.choices[0].delta.content
                    await websocket.send_text(chunk.choices[0].delta.content)
            chat_responses.append(ai_response)

        except Exception as e:
            await websocket.send_text(f"Error: {str(e)}")
            break


@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = openai.chat.completions.create(
        model = 'gpt-3.5-turbo',
        messages=chat_log,
        temperature=0.6 # Higher temperature, higher creativity
    )

    bot_response = response.choices[0].message.content
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return templates.TemplateResponse("home.html", {request: Request, "chat_responses": chat_responses})
