# RAG over Autmix agitator brochures

A retrieval-augmented generation system that answers questions about Autmix
industrial agitators using only their public product brochures. Answers are
written in Spanish, cite the passages they come from as `[n]`, and the system
abstains when the brochures don't contain the answer.

| Layer | Technology | Role |
|---|---|---|
| UI | Streamlit | Upload PDFs, ask questions, show answers with their sources and scores |
| API | FastAPI | `/health`, `/ingest`, `/query` |
| Index | ChromaDB | Persistent store of chunks + vectors, cosine k-NN search |
| Embeddings | Google AI (`gemini-embedding-001`) | One vector per chunk and per question |
| Generation | Google AI (`gemini-3.5-flash`) | Grounded answer from the retrieved chunks |

A question goes from the Streamlit UI (port 8501) to the FastAPI API (port
8000) over HTTP. The API embeds it with Google AI, retrieves the `top_k`
nearest chunks from ChromaDB, and asks Gemini to answer from those chunks only.

The UI never talks to ChromaDB or Google AI directly; everything goes through
the API.

## Corpus

`data/` holds 11 public Autmix brochures (33 pages, about 3,200 words), one per
agitator series: anchors (NC-NCH, NC-NCS, NC-NCT), compact (CT-CTF, CT-CTI,
CT-CTR), horizontal (ZB-ZBP, ZB-ZBR), rotor (RE-RES) and vertical (RT-RTG,
RT-RTN). All of them have a text layer, so no OCR is needed.

## Setup

Requires Python 3.13 (other recent versions may work but weren't tested).

```bash
cd final-project
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

### Google AI key

1. Create a key at [Google AI Studio](https://aistudio.google.com/apikey).
2. Copy `.env.example` to `.env` and paste the key:

   ```
   GOOGLE_API_KEY=your-key
   ```

`.env` is gitignored. The API reads it from `final-project/.env` no matter
which folder you start it from.

**Quota.** On the free tier Google allows only about 20 answer requests per
day for `gemini-3.5-flash`. When the quota runs out, questions fail with
`Error de Google AI: 429 RESOURCE_EXHAUSTED`; that means the quota is used up,
not that the installation is broken. Linking a prepaid billing account in AI
Studio removes the daily limit (each answer costs a fraction of a cent).

## Running

Start the API and the UI in two terminals, both from `final-project/` with the
virtual environment active.

```bash
uvicorn app.main:app --port 8000
```

```bash
streamlit run ui/streamlit_app.py
```

- UI: http://localhost:8501
- API docs: http://localhost:8000/docs

Start uvicorn **without** `--reload`. On Windows the reloader can hang after a
file change: it prints `Reloading...` but keeps serving the old code. Restart
the API by hand after changing anything in `app/`.

### Indexing the corpus

A fresh clone starts with an empty index (`chroma/` is created on first use).
Index the brochures in either of two ways:

- **From the UI:** select the PDFs in *Cargar documentos* and click *Indexar*.
- **From the command line:** `python -m scripts.check_store` indexes every PDF
  in `data/` and runs a test question.

The index lives in `chroma/` and survives restarts. Indexing the same file
again overwrites its chunks instead of duplicating them.

### Trying it

Ask in the UI, or call the API directly:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué materiales de fabricación tiene el agitador RT-RTG?", "top_k": 3}'
```

Expected: an answer listing the RT-RTG materials with `[n]` citations, and the
cited chunks with their source, page and score. A question the brochures
can't answer, such as *¿Cuál es el precio del agitador RT-RTG?*, returns
`"abstained": true` with *No tengo evidencia suficiente en el corpus para
responder.*

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/health` | | API status, whether Chroma is reachable, number of chunks |
| POST | `/ingest` | multipart, field `files` (one or more PDFs) | documents and chunks indexed, plus skipped files with the reason |
| POST | `/query` | `{"question": str, "top_k": 1-10 (default 3), "source": str or null}` | `answer`, `citations` (n, id, title, source, page, text, score, cited), `abstained` |

`source` restricts the search to one file, e.g.
`"Autmix_Mixing_Solutions_Agitadores_Verticales_RT_RTG.pdf"`.

Invalid input is rejected before it reaches the pipeline: blank or overlong
questions and an out-of-range `top_k` return 422, uploads that aren't real PDFs
(checked by content, not extension), are damaged, have no text or exceed 20 MB
are listed in `skipped`. A missing key returns 503 and a Google AI failure
returns 502, so an out-of-domain question never causes a 500.

## How a question is answered

1. **Chunking** (`app/loader.py`, `app/chunk.py`). Each PDF is read page by
   page. Cover pages (under 20 words) are skipped, the contact footer repeated
   on every brochure is cut, and the rest is split into windows of 100 words
   with 25 words of overlap. Each chunk is embedded with the agitator model
   name in front (e.g. `Agitadores Verticales RT-RTG. ...`), because the
   brochures share one template and would otherwise be nearly identical.
2. **Embedding** (`app/embed.py`). Chunks are embedded with
   `task_type=RETRIEVAL_DOCUMENT` and questions with `RETRIEVAL_QUERY`, using
   the same model for both.
3. **Retrieval** (`app/store.py`). Chroma returns the `top_k` nearest chunks
   in cosine space; score = 1 − distance.
4. **Answer** (`app/generate.py`). See the abstention rule below.

### Abstention rule

The system abstains in three cases:

1. **The best chunk scores below `MIN_SCORE` = 0.65** (`app/main.py`). Gemini
   isn't called. Off-topic questions scored 0.53–0.57 in testing, answerable
   ones 0.75–0.80.
2. **Gemini replies with the abstain text.** The prompt tells it to answer
   only from the numbered passages and to reply exactly *No tengo evidencia
   suficiente en el corpus para responder.* when they don't contain the
   answer. This catches in-domain questions with no answer in the brochures,
   such as prices, which score as high as real questions (0.76).
3. **The answer cites no passage.** An answer that can't be traced to the
   corpus is replaced by the abstain text.

## Project structure

```
final-project/
  app/
    main.py         FastAPI app: /health, /ingest, /query
    schemas.py      request and response models
    loader.py       reads a PDF into one record per page
    chunk.py        cleaning and overlapping word windows
    embed.py        Google AI client and embeddings
    store.py        ChromaDB: upsert and top-k query
    generate.py     prompt, Gemini call, citation parsing, abstention
  ui/
    streamlit_app.py
  scripts/          checks run by hand (chunks, embeddings, index)
  utils/vectors.py  cosine similarity used by the checks
  data/             the 11 brochures
  chroma/           persistent index (gitignored, created on first use)
```

## Credits

The word-window chunker, the `Retrieved` result shape, the prompt layout and
the cosine helpers are adapted from the course's `RAG/project/rag/` package.
The brochures are public material from Autmix.
