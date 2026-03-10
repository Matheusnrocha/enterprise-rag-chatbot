import os
import argparse
from typing import List
import re
from pathlib import Path

import chromadb
from openai import OpenAI

# carrega variáveis de ambiente (OPENAI_API_KEY, etc.)
from dotenv import load_dotenv
load_dotenv()

# ---------------------------
# Leitura de arquivos
# ---------------------------

def read_txt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return path.read_text(encoding="latin-1", errors="ignore")

def read_pdf(path: Path) -> str:
    # 1) pypdf (rápido e leve)
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        text = "\n".join(parts)
        if text.strip():
            return text
    except Exception as e:
        print(f"[WARN] pypdf falhou em {path.name}: {e}")

    # 2) fallback: unstructured (melhor para PDFs “chatos”/scans OCR)
    try:
        from unstructured.partition.pdf import partition_pdf
        elements = partition_pdf(filename=str(path))
        text = "\n".join((el.text or "") for el in elements)
        if text.strip():
            return text
    except Exception as e:
        print(f"[WARN] unstructured.pdf falhou em {path.name}: {e}")

    return ""

def read_docx(path: Path) -> str:
    # 1) python-docx
    try:
        from docx import Document as DocxDoc
        doc = DocxDoc(str(path))
        text = "\n".join(p.text for p in doc.paragraphs)
        if text and text.strip():
            return text
    except Exception as e:
        print(f"[WARN] python-docx falhou em {path.name}: {e}")

    # 2) fallback: docx2txt (muito resiliente)
    try:
        import docx2txt
        text = docx2txt.process(str(path)) or ""
        if text.strip():
            return text
    except Exception as e:
        print(f"[WARN] docx2txt falhou em {path.name}: {e}")

    return ""

# ---------------------------
# Chunking
# ---------------------------

def split_chunks(text: str, size: int, overlap: int) -> List[str]:
    # saneamento defensivo
    try:
        size = max(1, int(size))
        overlap = max(0, int(overlap))
    except Exception:
        size, overlap = 1000, 200

    if overlap >= size:
        overlap = max(0, size // 5)

    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    stride = size - overlap
    n = len(text)

    for start in range(0, n, stride):
        end = min(start + size, n)
        chunks.append(text[start:end])
        if end >= n:
            break
    return chunks

# ---------------------------
# Embeddings (em lotes)
# ---------------------------

def embed_texts(texts: List[str], api_key: str, model: str, batch_size: int = 128) -> List[List[float]]:
    client = OpenAI(api_key=api_key)
    embeddings: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        resp = client.embeddings.create(model=model, input=batch)
        embeddings.extend([d.embedding for d in resp.data])
    return embeddings

# ---------------------------
# Main
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Ingestão de documentos para Chroma")
    parser.add_argument("--source", default=os.getenv("DOCS_DIR", "data/docs"))
    parser.add_argument("--persist", default=os.getenv("VECTOR_PERSIST_DIR", "vectorstore"))
    parser.add_argument("--collection", default=os.getenv("COLLECTION_NAME", "tcc_docs"))
    parser.add_argument("--chunk_size", type=int, default=int(os.getenv("CHUNK_SIZE", "1000")))
    parser.add_argument("--chunk_overlap", type=int, default=int(os.getenv("CHUNK_OVERLAP", "200")))
    parser.add_argument("--embedding_model", default=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"))
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Defina OPENAI_API_KEY")

    client = chromadb.PersistentClient(path=args.persist)
    col = client.get_or_create_collection(name=args.collection)

    support = {
        ".pdf": read_pdf,
        ".docx": read_docx,
        ".txt": read_txt,
    }

    src = Path(args.source)
    if not src.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {src}")

    docs = []
    for p in src.glob("**/*"):
        if p.is_file() and p.suffix.lower() in support:
            print(f"Lendo {p}")
            try:
                raw = support[p.suffix.lower()](p)
                if not raw.strip():
                    continue
                parts = split_chunks(raw, args.chunk_size, args.chunk_overlap)
                for i, ch in enumerate(parts):
                    docs.append((ch, str(p), f"{p.name}#chunk{i}"))
            except Exception as e:
                import traceback
                print(f"ERRO em {p}: {e}")
                traceback.print_exc()

    if not docs:
        print("Nenhum documento legível encontrado.")
        return

    texts = [d[0] for d in docs]
    print(f"Gerando embeddings de {len(texts)} chunks...")
    embeds = embed_texts(texts, api_key=api_key, model=args.embedding_model)

    ids = [d[2] for d in docs]
    metadatas = [{"source": d[1]} for d in docs]

    print("Gravando no Chroma...")
    col.upsert(documents=texts, embeddings=embeds, metadatas=metadatas, ids=ids)
    print(f"OK! Coleção '{args.collection}' atualizada em '{args.persist}'.")

if __name__ == "__main__":
    main()
