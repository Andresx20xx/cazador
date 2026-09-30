# cazador

Un agente que vive en GitHub Actions. Sin servidor, sin llaves pagas.

Cada 6 horas se despierta, lee su `runbook.md` (su memoria), caza
herramientas experimentales de IA en GitHub y Hacker News, le pide a un
modelo gratuito que califique los hallazgos, archiva todo en `hallazgos/`
y se vuelve a dormir. La unica continuidad entre despertares son los
archivos de este repo.

## Para prenderlo (3 pasos)

1. Cree un repo **privado** nuevo en GitHub que se llame `cazador` y suba
   estos archivos.
2. En el repo: Settings → Secrets and variables → Actions → New repository secret.
   Cree estos 3:
   - `LLM_API_KEY` → su llave de un proveedor gratuito
     (ej. NVIDIA build.nvidia.com — la pega usted, nadie mas la ve)
   - `LLM_BASE_URL` → la URL base (ej. `https://integrate.api.nvidia.com/v1`)
   - `LLM_MODEL` → el modelo (ej. `nvidia/nemotron-3-super-120b-a12b`)
3. Vaya a la pestana Actions y dele "Enable workflows". Tambien puede
   dispararlo a mano con "Run workflow".

## Costo

- GitHub Actions: ~4 corridas/dia x ~3 min = ~360 min/mes
  (el plan gratis trae 2000 min/mes en repos privados).
- Modelos: $0 con tiers gratuitos.
- Fuentes de caceria (GitHub Search, Hacker News): gratis, sin llave.

## Archivos

- `.github/workflows/cazador.yml` — el despertador (cron cada 6h)
- `agent/loop.py` — el cazador
- `agent/brain.py` — cliente del modelo (OpenAI-compatible)
- `runbook.md` — su memoria: turno, temas, vistos, errores
- `hallazgos/` — un archivo por caceria
