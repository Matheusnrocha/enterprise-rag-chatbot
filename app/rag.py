import os
from typing import List, Tuple
from openai import OpenAI
from .deps import get_env
from math import isfinite

def embed_chunks(texts: List[str]) -> List[List[float]]:
    client = OpenAI(api_key=get_env("OPENAI_API_KEY"))
    model = get_env("EMBEDDING_MODEL", "text-embedding-3-large")
    # OpenAI python client supports batch embeddings
    resp = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in resp.data]

def embed_query(q: str) -> List[float]:
    return embed_chunks([q])[0]

def generate_answer(prompt: str) -> str:
    client = OpenAI(api_key=get_env("OPENAI_API_KEY"))
    model = get_env("GENERATION_MODEL", "gpt-4o-mini")
    temperature = float(get_env("TEMPERATURE", "0.2"))
    messages = [
        {"role": "system", "content": "Você é um assistente técnico. Responda **apenas** com base no contexto fornecido. Quando faltar contexto, diga o que falta e peça mais detalhes. Cite trechos relevantes resumidamente."},
        {"role": "user", "content": prompt},
    ]
    resp = client.chat.completions.create(model=model, temperature=temperature, messages=messages)
    return resp.choices[0].message.content.strip()
