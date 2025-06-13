from openai import OpenAI
import tiktoken
from concurrent.futures import ThreadPoolExecutor, as_completed

api_key = "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"  # Inlocuieste cu cheia ta API OpenAI

client = OpenAI(api_key=api_key)

tokenizer = tiktoken.get_encoding("o200k_base")

with open("aa.txt", "r", encoding="utf-8") as file:
    text = file.read()
    
chunks = text.split('\n\n')
ntokens = []
for chunk in chunks:
    ntokens.append(len(tokenizer.encode(chunk)))
    
print("Marimea celui mai mare chunk: ", max(ntokens))
print("Marimea celui mai mic chunk: ", min(ntokens))
print("Numarul de chunks: ", len(chunks))

def group_chunks(chunks, ntokens, max_len=15000, hard_max_len=16000):
    '''Grupam chunk-uri cat mai mici, pentru a nu depasi limita de tokeni si a.i. sa formeze chunkuri de maxim o pagina'''
    
    batches = []
    cur_batch = ""
    cur_tokens = 0
    
    # Iteram prin chunk-uri si le adaugam in loturi
    for chunk, ntoken in zip(chunks, ntokens):
        #scoatem chunk-urile care sunt prea mari
        if ntoken > hard_max_len:
            print(f"Avertizre: Chunk-ul a fost omis deoarece este prea lung ({ntoken} tokeni > limita de tokeni ({hard_max_len}) Preview: '{chunk[:50]}...')")
            continue
        
        #daca e loc in batch-ul curent, adaugam chunk-ul
        if cur_tokens + 1 + ntoken <=max_len:
            cur_batch += "\n\n" + chunk
            cur_tokens += 1 + ntoken #adauga un token pentru doua linii noi
            #altfel, inregistreaza batch-ul si incepe unul nou
        else:
            batches.append(cur_batch)
            cur_batch = chunk
            cur_tokens = ntoken
        
    if cur_batch: #adauga ultimul batch daca exista
        batches.append(cur_batch)
        
    return batches

chunks = group_chunks(chunks, ntokens)
print("Numarul de batch-uri: ", len(chunks))
             
def translate_chunk(chunk, model='gpt-4o',
                    dest_language='English',
                    sample_translation=(
                    r"\poglavje{Osnove Geometrije} \label{osn9Geom}",
                    r"\chapter{The basics of Geometry} \label{osn9Geom}")):
    prompt = f'''Translate only the text from the following document into {dest_language}.
    
"""
{sample_translation[0]}
{chunk}"""

{sample_translation[1]}
'''
    response = client.chat.completions.create(
        messages=[{"role": "user", "content":prompt}],
        model=model,
        temperature=0,
        top_p=1,
        max_tokens=15000,
    )
    result = response.choices[0].message.content.strip()
    result = result.replace('"""', '')
    return result
print(translate_chunk(chunks[2], model='gpt-4o', dest_language='English'))

dest_language = 'English'

translated_chunks = []
for i, chunk in enumerate(chunks):
    print(str(i+1) + " / " + str(len(chunks)))
    # tranducem fiecare chuuink
    translated_chunks.append(translate_chunk(chunk, model='gpt-4o', dest_language=dest_language))
    
    #uneste rezultatele
    result = "\n\n".join(translated_chunks)
    
    #salvam rezultatul final
    with open(f"translated_{dest_language}.txt", "w", encoding="utf-8") as file:
        file.write(result)

#Functie pentru a traduce un chunk folosind ThreadPoolExecutor
def translate_chunk_wrapper(chunk, model='gpt-4o', dest_language='English'):
    return translate_chunk(chunk, model=model, dest_language=dest_language)

#Setam limba de destinatie
dest_language = 'English'

#Initializm o lista goala pentru a stoca chunkurile traduse
translated_chunks = []

#Folosim ThreadPoolExecutor pentru a traduce chunkurile in paralel
with ThreadPoolExecutor(max_workers=5) as executor:
    #Submitem fiecare task pentru traducere
    futures = {executor.submit(translate_chunk_wrapper, chunk, model='gpt-4o', dest_language=dest_language): i for i, chunk in enumerate(chunks)}
    
    #Procesare taskuri finalizate
    for future in as_completed(futures):
        i = futures[future]
        try:
            translated_chunk = future.result()
            translated_chunks.append(translated_chunk)
            print(f"Chunk {i+1} /  {len(chunks)} tradus cu succes.")
        except Exception as e:
            print(f"Chunk {i+1} / {len(chunks)} a esuat cu eroarea: {e}")
            
#Impreunam chunkurile traduse
result = '\n\n'.join(translated_chunks)

#Salvam rezultatul final
with open(f"translated_{dest_language}.txt", "w", encoding="utf-8") as file:
    file.write(result)
    
    
    
    