import json
import os
from openai import OpenAI
from pydantic import BaseModel, Field

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def search_kb(question: str):
    with open("kb.json", "r") as f:
        return json.load(f)

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": "Ia raspunsurile utilizatorului din fisierul de cunostinte json.",
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

system_prompt = "Esti un asistent decent."

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "Care este politica de returnare?"},
]

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)

completion.model_dump()


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

class KBResponse(BaseModel):
    answer: str = Field(description="Raspunsul la intrebarea utilizatorului.")
    source: int = Field(description="ID-ul raspunsului.")


completion_2 = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    response_format=KBResponse,
)


final_response = completion_2.choices[0].message.parsed
final_response.answer
final_response.source

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "What is the weather in Tokyo?"},
]

completion_3 = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)

completion_3.choices[0].message.content
