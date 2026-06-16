
import os

client = None

def init_openai():
    global client
    key = os.getenv("OPENAI_API_KEY")

    if not key:
        return

    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
    except:
        client = None


def analyze_stock(text, stock_data):

    if client is None:
        return "AI not ready"

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Analyze stock:
{text}
Data:
{stock_data}"
            }]
        )

        return res.choices[0].message.content

    except:
        return "GPT error"
