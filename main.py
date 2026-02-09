from __future__ import annotations

import time
import uuid
import random
from typing import Dict, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response

app = FastAPI(title="REST Challenge (compat app.erikmd)")

# token -> (secret_number, expires_at_epoch_seconds)
TOKENS: Dict[str, Tuple[int, float]] = {}

TOKEN_TTL_SECONDS = 60


def _now() -> float:
    return time.time()


def _purge_expired() -> None:
    now = _now()
    expired = [t for t, (_, exp) in TOKENS.items() if exp <= now]
    for t in expired:
        TOKENS.pop(t, None)


@app.get("/init")
def init(
    quad: str = Query(
        ...,
        pattern=r"^[A-Z]{2,4}$",
        description="Chaîne [A-Z]{2,4}",
        examples=["NAME"],
    )
):
    """
    GET /init?quad=NAME
    Retourne du XML avec un token valable 60s.
    """
    _purge_expired()

    token = uuid.uuid4().hex
    # Nombre à deviner : volontairement simple pour un TP (1..2^31-1)
    secret = random.randint(1, 2_147_483_647)
    expires_at = _now() + TOKEN_TTL_SECONDS
    TOKENS[token] = (secret, expires_at)

    # XML minimal "pédagogique" : root + token + validForSeconds
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<init>
  <quad>{quad}</quad>
  <token>{token}</token>
  <validForSeconds>{TOKEN_TTL_SECONDS}</validForSeconds>
</init>
"""
    return Response(content=xml, media_type="text/xml")


@app.get("/try")
def try_guess(
    token: str = Query(..., description="Token renvoyé par /init"),
    guess: int = Query(
        ...,
        ge=1,
        le=2_147_483_647,
        description="Entier positif sur 32 bits",
    ),
):
    """
    GET /try?token=...&guess=...
    Retourne du JSON indiquant si guess est trop petit/grand/trouvé.
    """
    _purge_expired()

    if token not in TOKENS:
        # 404 est pratique pédagogiquement (token inconnu/expiré)
        raise HTTPException(status_code=404, detail="Unknown or expired token")

    secret, expires_at = TOKENS[token]
    if expires_at <= _now():
        TOKENS.pop(token, None)
        raise HTTPException(status_code=404, detail="Unknown or expired token")

    if guess < secret:
        return {"token": token, "guess": guess, "result": "TOO_SMALL"}
    if guess > secret:
        return {"token": token, "guess": guess, "result": "TOO_BIG"}

    # trouvé
    TOKENS.pop(token, None)
    return {
        "token": token,
        "guess": guess,
        "result": "FOUND",
        "message": "Bravo, nombre trouvé !",
    }