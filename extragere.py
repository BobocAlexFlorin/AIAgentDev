import json
import os

from openai import OpenAI
from pydantic import BaseModel, Field

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def search_kb(question: str):
    """
    Search for a query in the background using OpenAI's API. - asta ar fii o funcție de căutare în baza de date, insa cum nu o avem inca o sa citesc dintr-un json
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content
    """
    
    with open("kb.json", "r") as f:
        return json.load(f)
    
    tools = [
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": "Ia raspunsul pentru user din documentul de cunostinte.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                },
                "required": ["question"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]

system_prompt = "Esti un asistent."

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "Care este politica de returnare?"},
]

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)

#Modelul trebuie sa decida ce functie sa cheme

completion.model_dump()

#Executa functia de search obligatoriu


def call_function(name, args):
    if name == "search_kb":
        return search_kb(**args)


for tool_call in completion.choices[0].message.tool_calls:
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    messages.append(completion.choices[0].message)

    result = call_function(name, args)
    messages.append(
        {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)}
    )

# Da rezultatul


class KBResponse(BaseModel):
    answer: str = Field(description="Raspunsul la intrebare")
    source: int = Field(description="ID-ul sursei din care a fost extras raspunsul")


completion_2 = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    response_format=KBResponse,
)

#Verifica raspunsul

final_response = completion_2.choices[0].message.parsed
final_response.answer
final_response.source

#Intrebarea nu da trigger la tool

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "Cum e vremea in Resita?"},
]

completion_3 = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)

completion_3.choices[0].message.content