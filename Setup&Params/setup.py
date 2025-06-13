import os

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Esti un asistent decent."},
        {
            "role": "user",
            "content": "Scrie ceva despre python.",
        },
    ],
)

response = completion.choices[0].message.content
print(response)
