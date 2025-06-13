import os
import logging
import asyncio
from langdetect import detect
from cryptography.fernet import Fernet
import pandas as pd
import json
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Genereaza cheia de encriptie (doar o data)
key = Fernet.generate_key()
cipher_suite = Fernet(key)

def encrypt_data(data):
    return cipher_suite.encrypt(data.encode())

def decrypt_data(encrypted_data):
    return cipher_suite.decrypt(encrypted_data).decode()

# Ecnripteaza cheia API
api_key = os.getenv("OPENAI_API_KEY")
encrypted_key = encrypt_data(api_key)
logger.info(f"Cheia API encriptata: {encrypted_key}")

def detect_language(text):
    """Detecteaza limba textului."""
    try:
        language = detect(text)
        logger.info(f"Detected language: {language}")
        return language
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        return None

async def translate_chunk_async(chunk, model, dest_language):
    """Simuleaza o traducere asincrona (inlocuieste cu async API call)"""
    await asyncio.sleep(0.1)  # Simulate async processing
    return f"Translated: {chunk}"

async def process_chunks_async(chunks, model, dest_language):
    """Proceseaza chunk-uri asincron."""
    tasks = [translate_chunk_async(chunk, model, dest_language) for chunk in chunks]
    results = await asyncio.gather(*tasks)
    return results

def track_context(chunks):
    """Da track la contextul intre chunk-uri"""
    context = " ".join(chunks)  # Combina chunk-uri pentru context
    logger.info(f"Tracked context: {context}")
    return context

def save_feedback(feedback, file_path="feedback.txt"):
    """Salveaza feedback-ul userilor intr-in fisier."""
    with open(file_path, "a") as f:
        f.write(f"{feedback}\n")
    logger.info("Feedback saved.")

def generate_report(data):
    """Proceseaza un raport din datele procesate"""
    df = pd.DataFrame(data)
    report_path = "report.csv"
    df.to_csv(report_path, index=False)
    logger.info(f"Report generated at {report_path}")

def load_prompt_template(file_path):
    """Incarca template-ul de prompt dintr-un fisier JSON."""
    with open(file_path, "r") as f:
        template = json.load(f)
    logger.info("Prompt template loaded.")
    return template

# Logica de procesare a chunk-urilor
if __name__ == "__main__":
    chunks = ["chunk1", "chunk2", "chunk3"]  #Inlocuieste cu chunk-uri reale
    model = "gpt-4o"
    dest_language = "English"

    # Detecteaza limba pentru fiecare chunk
    for chunk in chunks:
        language = detect_language(chunk)
        logger.info(f"Processing chunk in language: {language}")

    # Da track la context intre chunk-uri
    context = track_context(chunks)

    # Le proceseaza asincron
    translated_chunks = asyncio.run(process_chunks_async(chunks, model, dest_language))

    # Salveaza feedback-ul utilizatorului
    feedback = input("Please provide feedback for the translation: ")
    save_feedback(feedback)

    # Genereaza raportul
    data = [{"chunk": chunk, "translation": translation} for chunk, translation in zip(chunks, translated_chunks)]
    generate_report(data)

    # Incarca template-ul de prompt
    template = load_prompt_template("prompt_template.json")
    logger.info(f"Using prompt template: {template}")