#!/usr/bin/env python3
"""loop.py — el cazador.

Se despierta (cron de GitHub Actions), lee su runbook (su memoria),
caza herramientas experimentales de IA en fuentes gratuitas sin llave,
le pide al cerebro que califique, archiva hallazgos y actualiza el runbook.
La unica continuidad entre despertares son los archivos del repo.

Fuentes sin llave: GitHub Search API + Hacker News (Algolia).
"""
import datetime
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brain import chat  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNBOOK = os.path.join(ROOT, "runbook.md")
HALLAZGOS = os.path.join(ROOT, "hallazgos")

UA = {"User-Agent": "cazador/1.0"}


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def github_search(query, per_page=8):
    """Repos recientemente movidos sobre el tema."""
    q = urllib.request.quote(query)
    url = (f"https://api.github.com/search/repositories?q={q}"
           f"&sort=updated&order=desc&per_page={per_page}")
    d = get(url)
    out = []
    for it in d.get("items", []):
        out.append({
            "id": "gh:" + it["full_name"],
            "titulo": it["full_name"],
            "desc": (it.get("description") or "")[:220],
            "stars": it.get("stargazers_count", 0),
            "url": it["html_url"],
            "lang": it.get("language") or "?",
        })
    return out


def hn_search(query, per_page=8):
    """Historias de Hacker News sobre el tema."""
    q = urllib.request.quote(query)
    url = (f"https://hn.algolia.com/api/v1/search?query={q}"
           f"&tags=story&hitsPerPage={per_page}")
    d = get(url)
    out = []
    for h in d.get("hits", []):
        out.append({
            "id": "hn:" + str(h["objectID"]),
            "titulo": h.get("title") or "",
            "desc": "",
            "stars": h.get("points") or 0,
            "url": f"https://news.ycombinator.com/item?id={h['objectID']}",
            "lang": "discusion",
        })
    return out


TEMAS = [
    ("agentes IA locales y open-source",
     "local AI agent open source", "local AI agent selfhosted"),
    ("coding agents gratis",
     "free coding agent open source", "free AI coding assistant"),
    ("IA que controla el celular",
     "AI phone agent android", "android phone AI agent"),
    ("voz y audio con IA local",
     "local voice AI open source", "open source text to speech agent"),
    ("automatizacion serverless y agentes 24/7",
     "serverless AI agent cron", "always-on AI agent github actions"),
    ("modelos open-weight nuevos",
     "new open weights model", "open source LLM release"),
]


def leer_runbook():
    with open(RUNBOOK, encoding="utf-8") as f:
        txt = f.read()
    turno = int(re.search(r"turno:\s*(\d+)", txt).group(1))
    vistos = set(re.findall(r"^- (.+)$", txt.split("## Vistos")[1].split("##")[0], re.M)
                 ) if "## Vistos" in txt else set()
    errores = ""
    if "## Errores" in txt:
        errores = txt.split("## Errores")[1].strip()[-800:]
    return txt, turno, vistos, errores


def guardar_runbook(txt, turno, vistos, nuevos_ids):
    vistos = list(vistos | set(nuevos_ids))[-250:]
    base = txt.split("## Vistos")[0].rstrip() + "\n"
    base = re.sub(r"turno:\s*\d+", f"turno: {turno}", base)
    base += "\n## Vistos\n" + "".join(f"- {v}\n" for v in vistos)
    base += "\n## Errores\n(nada por ahora)\n"
    with open(RUNBOOK, "w", encoding="utf-8") as f:
        f.write(base)


def main():
    os.makedirs(HALLAZGOS, exist_ok=True)
    txt, turno, vistos, errores = leer_runbook()
    tema_es, q_gh, q_hn = TEMAS[turno % len(TEMAS)]
    print(f"[cazador] turno {turno} | tema: {tema_es}")

    candidatos = []
    try:
        candidatos += github_search(q_gh)
    except Exception as e:
        print(f"[cazador] github fallo: {e}")
    try:
        candidatos += hn_search(q_hn)
    except Exception as e:
        print(f"[cazador] hn fallo: {e}")

    nuevos = [c for c in candidatos if c["id"] not in vistos]
    print(f"[cazador] candidatos: {len(candidatos)} | nuevos: {len(nuevos)}")
    if not nuevos:
        guardar_runbook(txt, turno + 1, vistos, [])
        print("[cazador] nada nuevo, a dormir.")
        return

    # El cerebro califica en UNA sola llamada (cuidar el rate limit gratis)
    lista = "\n".join(
        f"{i+1}. {c['titulo']} ({c['lang']}, {c['stars']}★) — {c['desc']} — {c['url']}"
        for i, c in enumerate(nuevos[:12])
    )
    veredicto = chat([
        {"role": "system", "content":
         "Eres un cazador de herramientas de IA experimentales. Te gustan las "
         "cosas raras que funcionan y casi nadie conoce. Odias el marketing."},
        {"role": "user", "content":
         f"Tema de la caceria: {tema_es}.\n\nCandidatos:\n{lista}\n\n"
         "Elige los 3 mas experimentales, reales y gratuitos (o open-source). "
         "Para cada uno: nombre, una linea de que hace, una linea de por que "
         "es raro/interesante, y su nivel de humo (bajo/medio/alto). "
         "Formato markdown compacto. Si ninguno vale la pena, dilo de frente."},
    ], max_tokens=1200)

    ahora = datetime.datetime.now(datetime.timezone.utc)
    slug = ahora.strftime("%Y-%m-%d-%H%M")
    path = os.path.join(HALLAZGOS, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Caceria {slug} UTC — {tema_es}\n\n{veredicto}\n")
    print(f"[cazador] hallazgo guardado: {path}")

    guardar_runbook(txt, turno + 1, vistos, [c["id"] for c in nuevos])
    print("[cazador] runbook actualizado. A dormir.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Auto-curado: deja el error en el runbook para el proximo despertar
        print(f"[cazador] ERROR: {e}")
        try:
            with open(RUNBOOK, encoding="utf-8") as f:
                t = f.read()
            t = t.replace("## Errores\n(nada por ahora)",
