import os
from dotenv import load_dotenv
import anthropic
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)
def text_processor(prompt):
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4096,
        temperature=0,
        system="You are a text processor",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    return message.content[0].text