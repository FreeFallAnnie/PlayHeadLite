import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_AliN(full_prompt):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Respond clearly and creatively."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()
