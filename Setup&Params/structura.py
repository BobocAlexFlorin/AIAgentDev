import os

from openai import OpenAI
from pydantic import BaseModel

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants : list[str]
    
#Cheama modelul

completion = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages = [
        { "role": "system", "content": "Extrage informatia unui eveniment." },
        {
            "role": "user",
            "content": "Excrusie la muzeu"
        },
    ],
    
    response.format=CalendarEvent,
)

event = completion.choices[0].messages.parsed
event.name
event.date
event.participants