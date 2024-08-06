import anthropic


client = anthropic.Anthropic(
    api_key="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",
)
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