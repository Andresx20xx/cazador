#!/usr/bin/env python3
"""brain.py — cliente OpenAI-compatible minimalista para el cazador.

Lee la llave solo de variables de entorno (en Actions: GitHub Secrets).
Nunca imprime ni guarda la llave.
"""
import json
import os
import time
import urllib.request


def _env(name):
    v = os.environ.get(name, "").strip()
    if not v:
        raise RuntimeError(f"falta variable de entorno {name}")
    return v


def chat(messages, max_tokens=1500, temperature=0.4, retries=3):
    base = _env("LLM_BASE_URL").rstrip("/")
    model = _env("LLM_MODEL")
    key = _env("LLM_API_KEY")
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()
    last = None
    for i in range(retries):
        req = urllib.request.Request(
            base + "/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + key,
                "User-Agent": "cazador/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            return d["choices"][0]["message"]["content"].strip()
        except Exception as e:
            last = e
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"el cerebro no respondio tras {retries} intentos: {last}")
