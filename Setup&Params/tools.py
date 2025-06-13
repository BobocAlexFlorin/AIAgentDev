import json
import os
import requests
from openai import OpenAI
from pydantic import BaseModel, Field

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#Defineste functiionalitatea toolului

def get_weather(latitude, longitude):
    response = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"

    )
    data = response.json()
    return data["current"]

#Chemama modelul in functie
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Ia temperatura curenta pentru coordonatele date."
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude" : {"type": "number"}
            },
                "required": ["latitude", "longitude"],
                "additionalProprieties": False,
                            },
            "strict": True,
        },
    }
]

system_prompt = "Este un asistent decent, sa stii"

messages = [
    {{"role": "system", "content": system_prompt},
    {"role": "user", "content": "Cum e astazi vremea in Resita?"},}
]

completion = client.chat.completions.create(
    model = "gpt-4o",
    messages = messages,
    tools = tools,
)

completion.model_dump()

def call_function(name, args):
    if name == "get_weather":
        return get_weather(**args)
    
for tool_call in completion.choices[0].message.tool_calls:
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    messages.append(completion.choices[0].message)
    
    result = call_function(name, args)
    messages.append(
        {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)}
    )
    
#Incarcare rezultat si rechemare model

class WeatherResult(BaseModel):
    temperature: float = Field(
        description = "Temperatura curenta in Celsius la locatia data"
    )
    response: str = Field(
        description = "Un raspuns natural la cererea utilizatorului"
    )
    
completion_2 = client.beta.chat.completion.parse(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    response_format=WeatherResult,
)

#Verifica raspunsul modelului

final_result = completion_2.choice[0].message.parsed
final_result.temperature
final_result.response