from typing import Optional, Literal
from pydantic import BaseModel, Field
from openai import OpenAI
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o"

#Definire modele de date pentru raspunsuri si routing

class CalendarRequestType(BaseModel):
    '''Call LLM Router: Determina tipul de request din calendar'''
    
    request_type: Literal["new_event", "modify_event", "other"] = Field(
        description="Tipul de request de calendar este creat..."
    )
    confidence_score: float = Field(description="Scorul de Confidenta este intre 0 si 1")
    description: str = Field(description="Descrierea curatata a requestului de calendar")
    
class NewEventDetails(BaseModel):
    '''Detalii pentru crearea unui eveniment nou in calendar'''

    name: str = Field(description="Nume eveniment")
    date: str = Field(description="Data si ora evenimentului")
    duration_minutes: int = Field(description="Durata trecuta in minute a evenimentului")
    participants: list[str] = Field(description="Lista de participanti")
    
    
class Change(BaseModel):
    '''Detalii pentru modificarea unui eveniment existent in calendar'''
    
    field: str = Field(description="Campul pe care il vrem schimbat")
    new_value: str = Field(description="Noua valoare a campului")
    
class ModifyEventDetails(BaseModel):
    '''Detalii pentru modificarea unui eveniment existent in calendar'''
    
    event_identifier: str = Field(description="Descrierea unui eveniment existent in calendar")
    changes: list[Change] = Field(description="Lista de modificari")
    participants_to_add: list[str] = Field(description="Lista de participanti noi")
    participants_to_remove: list[str] = Field(description="Lista de participanti care vor fi stersi")
    
class CalendarResponse(BaseModel):
    '''Formatul de raspuns final din calendar'''
    
    succes: bool = Field(description="Operatiunea a fost, sau nu, indeplinita")
    message: str = Field(description="Raspuns User-Friendly")
    calendar_link: Optional[str] = Field(description="Link catre calendar, unde se aplica")
    
#Definim routing ul si rpocesarea functilor

def route_calendar_request(user_input: str) -> CalendarRequestType:
    '''Route LLM pentru a determina tipul de request catre calendar'''
    
    logger.info("Routare calendar")
    
    completion = client.beta.chat.completions.parse(  # <-- corectat aici
        model = model,
        messages = [
            {
                "role": "system",
             "content": "Determina daca este un request pentru a creea un nou eveniment sau sa modifice unul deja existent"
            },
            {
                "role": "user", "content": user_input 
            },
        ],
        response_format = CalendarRequestType,
    )
    result = completion.choices[0].message.parsed
    logger.info(
        f"Request-ul a fost routed ca si: {result.request_type} cu confidenta {result.confidence_score}"
    )
    return result

def handle_new_event(description: str) -> CalendarResponse:
    '''Procesarea unui nou eveniment in calendar'''
    logger.info("Procesarea unui eveniment nou")
    
    #Ia detaliile
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
             "content": "Extrage detaliile pentru a creea un eveniment nou in calendar"
            },
            {
                "role": "user", "content": description 
            },
        ],
        response_format=NewEventDetails,
    )
    details = completion.choices[0].message.parsed
    
    logger.info(f"Eveniment nou: {details.model_dump_json(indent=2)}")
    
    #generare raspuns
    return CalendarResponse(
        succes=True,
        message = f"Evenimentul {details.name} a fost creat pentru data {details.date} cu participantii {', '.join(details.participants)}",
        calendar_link = f"calendar://new?event={details.name}",
    )
    
def handle_modify_event(description: str) -> CalendarResponse:
    '''Procesarea modificarilor unui eveniment existent'''
    logger.info("Procesare cerere de modificare...")
    
    #Ia detaliile modificarii
    completion = client.beta.chat.completions.parse(
        model = model,
        messages = [
            {
                "role": "system",
             "content": "Extrage detaliile modificarii unui eveniment deja existent"
            },
            {
                "role": "user", "content": description
            },
        ],
        response_format=ModifyEventDetails,
    )
    details = completion.choices[0].message.parsed
    
    logger.info(f"Evenimentul modificat: {details.model_dump_json(indent=2)}")
    
    #Generare raspuns
    return CalendarResponse(
        success = True,
        message = f"Modificarile proiectului '{details.event_identifier}' cu cererile cerute",
        calendar_link=f"calendar://modify?event={details.event_identifier}",
    )
    
def process_calendar_requests(user_input: str) -> Optional[CalendarResponse]:
    '''Functia principala pentru implementarea workflowului de routing'''
    
    logger.info("Procesare request...")
    
    route_result = route_calendar_request(user_input)
    
    if route_result.confidence_score < 0.7:
        logger.info(f"Scor mic de confidenta: {route_result.confidence_score}")
        return None
    
    #Route catre handler-ul corect
    if route_result.request_type == "new_event":
        return handle_new_event(route_result.description)
    elif route_result.request_type == "modify_event":
        return handle_modify_event(route_result.description)
    else:
        logger.warning("Acest tip de request nu este implementat")
        return None
    
#Tesate cu eveniment nou

new_event_input = "Hai sa programam o intalinre cu Alex si Andrei in ziua de luni, la ora 10:00, la restaurantul din centrul orasului"
result = process_calendar_requests(new_event_input)
if result:
    print(f"Raspuns: {result.message}")
    
#Testare cu modificarea evenimentului

modify_event_input = "Poti muta te rog intalnirea cu Alex si Andrei miercuri la ora 16?"
result = process_calendar_requests(modify_event_input)
if result:
    print(f"Raspuns: {result.message}")
    
#Testare cu modificarea evenimentului

invalid_input = "Cum e vremea azi?"
result = process_calendar_requests(invalid_input)
if not result:
    print("Raspuns: Nu am putut procesa request-ul")