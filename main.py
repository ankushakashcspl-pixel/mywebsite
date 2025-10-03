from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

from ai4bharat.transliteration import XlitEngine

LANG = os.environ.get("XLIT_LANG", "hi")
BEAM = int(os.environ.get("BEAM_WIDTH", "10"))
TOPK_DEFAULT = int(os.environ.get("TOPK", "3"))

API_KEY = os.environ.get("XLIT_API_KEY", "").strip()

app = FastAPI(title="IndicXlit Transliteration API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = XlitEngine(LANG, beam_width=BEAM, rescore=True)

class TransliterateRequest(BaseModel):
    input: str
    topk: int = TOPK_DEFAULT

def check_api_key(request: Request):
    if not API_KEY:
        return
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization Bearer token")
    token = auth.split(" ", 1)[1].strip()
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

@app.get("/")
async def root():
    return {"status": "running", "lang": LANG}

@app.get("/v1/health")
async def health():
    return {"ok": True, "lang": LANG}

@app.post("/api/transliterate")
async def transliterate(req: TransliterateRequest, request: Request):
    check_api_key(request)
    text = (req.input or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="input required")

    words = text.split()
    results = []
    for w in words:
        try:
            out = engine.translit_word(w, topk=req.topk, beam_width=BEAM)
            candidates = out.get(LANG, []) if isinstance(out, dict) else out
            chosen = candidates[0] if candidates else w
        except Exception:
            chosen = w
            candidates = []
        results.append({"input": w, "top1": chosen, "candidates": candidates})

    joined = " ".join([r["top1"] for r in results])
    return {"input": text, "output": joined, "parts": results}
