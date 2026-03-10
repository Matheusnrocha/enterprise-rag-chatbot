# app/main.py
import os
from typing import List

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .schemas import ChatRequest, ChatResponse, ContextItem
from .deps import get_chroma_collection, get_env
from .rag import embed_query, generate_answer

app = FastAPI(title="RAG Chatbot TCC")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, col=Depends(get_chroma_collection)):
    # 1) Recuperação (RAG interno)
    q_emb = embed_query(req.message)
    k = max(1, min(req.k, 10))

    results = col.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    contexts: List[ContextItem] = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    # Converter distância L2 -> score heurístico (quanto maior, melhor)
    scores = []
    for d in dists:
        try:
            s = 1.0 / (1.0 + float(d))
        except Exception:
            s = 0.0
        scores.append(s)

    for text, meta, score in zip(docs, metas, scores):
        contexts.append(
            ContextItem(
                source=meta.get("source", "desconhecido"),
                chunk=text[:800],
                score=float(score),
            )
        )

    # 2) Se o score estiver baixo, responda que faltou base nos docs
    min_score = float(get_env("RETRIEVAL_MIN_SCORE", "0.45"))
    best_score = max((c.score for c in contexts), default=0.0)

    if len(contexts) == 0 or best_score < min_score:
        msg = (
            "Não encontrei base suficiente nos documentos internos para responder com segurança. "
            "Tente reformular a pergunta ou adicione documentos mais relevantes."
        )
        return ChatResponse(answer=msg, contexts=contexts)

    # 3) Geração baseada SOMENTE no contexto interno
    ctx_text = "\n\n".join(
        [f"[{i+1}] ({c.source})\n{c.chunk}" for i, c in enumerate(contexts)]
    )
    prompt = f"""
    CONTEXTO INTERNO (RAG):
    {ctx_text}

    PERGUNTA: {req.message}

    INSTRUÇÕES:
    - Responda baseado EXCLUSIVAMENTE no CONTEXTO INTERNO.
    - Seja objetivo; quando possível, traga passos de ação.
    - Se faltar contexto, diga explicitamente o que está faltando.
    - Ao final, liste as fontes no formato [1], [2], ...
    """.strip()

    answer = generate_answer(prompt)
    return ChatResponse(answer=answer, contexts=contexts)
