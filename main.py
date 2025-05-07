from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()  # Automatically loads variables from .env
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("<Missing OPENAI_API_KEY environment variable>")

openai = OpenAI(api_key=api_key) # Do not erase

response = openai.chat.completions.create(
    model = 'gpt-3.5-turbo',
    messages=[{
        'role': 'system',
        'content': 'You are a helpful assistant.' 
    }, {
        'role': 'assistant',
        'content': ''
    }, {
        'role': 'user',
        'content': 'Who won the last NBA championship?'        
    }],
    temperature=0.6 # Higher temperature, higher creativity
)

print(response.choices[0].message.content)
# Use print(response) for the entire json
