import os
from typing import Optional
import chromadb

def get_env(name: str, default: Optional[str] = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Variável de ambiente não definida: {name}")
    return val

def get_chroma_collection():
    persist = get_env("VECTOR_PERSIST_DIR", "vectorstore")
    collection_name = get_env("COLLECTION_NAME", "tcc_docs")
    client = chromadb.PersistentClient(path=persist)
    # cria se não existir
    return client.get_or_create_collection(name=collection_name)
