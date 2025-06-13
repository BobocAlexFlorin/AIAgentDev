from typing import Optional
from datetime import datetime
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

#Defineste modelele de date pentru fiecare stagiu

class EventExtraction(BaseModel):
    '''Primul call catre LLM, acesta extrage informatii basic despre eveniment'''
    description: str = Field(description="Raw description of the event")
    is_calendar_event: bool = Field(
        description="Acest text  descrie un eveniment"
    )
    confidence_score: float = Field(description="Confidence intre 0 si 1")
    
class EventDetails(BaseModel):
    '''Al doilea call catre LLM, asta Parse la detalii ale evenimentului'''
    
    name: str = Field(description="Nume Eveniment")
    date: str = Field(description="Data si ora evenimentului, folositi ISO 8601 pentru formatarea acestei valori.")
    duration_minutes: int = Field(description="Durata evenimentului era asteptata in minute")
    participants: list[str] = Field(description="Lista participantilor")
    
class EventConfirmation(BaseModel):
    '''Al treilea call catre LLM, acesta genereaza un mesaj de confirmare'''
    
    confirmation_message: str = Field(description="Mesaj Confirmare:)")
    calendar_link: Optional[str] = Field(description="Generare link in calendar daca este posibil.")
    
    
#Definire functii

def extract_event_info(user_input: str) -> EventExtraction:
    '''Primul call la LLM care sa determine daca inputul e un eveniment din calendar'''
    
    logger.info("Pornire analiza eveniment si extragere")
    logger.debug(f"Textul input:  {user_input}")
    
    today = datetime.now()
    date_context = f"Astazi este {today.strftime('%A, %B %d, %Y')}."
    
    completion = client.beta.chat.completion.parse(
        model=model,
        message = [
            {
                "role": "system",
                "content": f"{date_context} Analizeaza daca textul descrie un eveniment din calendar",
            },
            {"role": "user", "content": user_input},
        ],
        response_format=EventExtraction,
    )
    result = completion.choices[0].message.parsed
    logger.info(
        f"Extragere completa - Este eveniment din Calendar: {result.is_calendar_event}, Confidenta: {result.confidence_scoreL:.2f}"
    )
    return result

def parse_event_details(description: str) -> EventDetails:
    '''Al doilea call la LLM care sa extraga detalii despre eveniment'''
    
    logger.info("Pornire parsing la detalii")
    
    today = datetime.now()
    date_context = f"Astazi este {today.strftime('%A, %B %d, %Y')}."
    
    completion = client.beta.chat.completion.parse(
        model = model,
        messages = [
            {
                "role": "system",
                "content": f"{date_context} Extrage detalii despre eveniment. Cand datiile referentiaza 'urmatoare saptamana' sau date similare, foloseste data curenta ca referinta",
            },
            {"role": "user", "content": description},
        ],
        response_format=EventDetails,
    )
    
    result = completion.choices[0].message.parsed
    logger.info(
        f"Detaliile parsate - Nume: {result.name}, Date: {result.date}, Duratie: {result.duration_minutes} min"
    )
    logger.debug(f"Participantii: {', '.join(result.participants)}")
    return result

def generate_confirmation(event_details: EventDetails) -> EventConfirmation:
    '''Genereaza confirmarea evenimentului'''
    
    logger.info("Genereaza confirmare")
    
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"Genereaza confirmare pentru evenimentul {event_details.name}. Semneaza cu numele tau; Alex.",
            },
            {"role": "user", "content": str(event_details.model_dump())},
        ],
        response_format = EventConfirmation,
    )
    result = completion.choices[0].message.parsed
    logger.info("Mesajul de confirmare a fost generat cu succes")
    return result

#Chainuim functiile impreuna

def process_calendar_request(user_input: str) -> Optional[EventConfirmation]:
    '''Functia principala care implementeaza chainuirea prompturilor cu un gate check'''
    
    logger.info("Pornire procesare calendar")
    logger.debug(f"Input raw: {user_input}")
    
    #Primul call LLM
    initial_extraction = extract_event_info(user_input)
    
    #Gate check: Verifica daca e un eveniment din calendar cu destula confidenta
    if (
        not initial_extraction.is_calendar_event
        or initial_extraction.confidence_score < 0.7
    ):
        logger.warning(f"Gate check esuat - is_calendar_event: {initial_extraction.is_calendar_event}, confidence: {initial_extraction.confidence_score:.2f}")
        return None
    
    logger.info("Gate check trecut cu succes, continuam cu generarea confirmarii")
    
    #Al doilea call LLM
    event_details = parse_event_details(initial_extraction.description)
    
    #Al treilea call LLM
    confirmation = generate_confirmation(event_details)
    
    logger.info("Request calendar a fost completat cu succes")
    return confirmation

#testare chain cu un input valid

user_input = "Poti trimite ub email catre Alex pentru a confirma intalnirea de maine la ora 10:00? Intalnirea va dura 30 de minute si va avea loc la birou. Participanti: Alex, Maria, John."

result = process_calendar_request(user_input)
if result:
    logger.info(f"Confirmare generata: {result.confirmation_message}")
    if result.calendar_link:
        logger.info(f"Link calendar: {result.calendar_link}")
        
#Alta testare cu un input invalid
result = process_calendar_request(user_input)
if result:
    print(f"Confirmare generata: {result.confirmation_message}")
    if result.calendar_link:
        print(f"Link calendar: {result.calendar_link}")
else:
    logger.info("Nu s-a putut genera confirmarea, inputul nu este un eveniment valid din calendar.")