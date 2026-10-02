import io
from pathlib import Path

from fastapi import FastAPI, HTTPException, File, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf.errors import PdfReadError
from google.genai import errors

from app.chunk import Chunk, chunk_pages
from app.embed import embed_query, embed_documents
from app.loader import load_pdf
from app.generate import answer
from app.schemas import AgitatorSpecs, Citation, CompareCell, CompareRequest, CompareResponse, CompareRow, Passage, QueryRequest, QueryResponse, IngestResponse, SelectRequest, SelectResponse, SourceInfo
from app.store import Retrieved, count, sources as list_sources, query as search, upsert
from app.compare import UnknownSourcesError, compare as compare_models
from app.specs import load_specs, select as select_models, update_specs
from app.pages import DOCS_DIR, PageNotFoundError, render_page, safe_filename

MAX_FILES = 20
MAX_BYTES = 20 * 1024 * 1024 # 20 MB
PDF_MAGIC = b"%PDF-"
MIN_SCORE = 0.65  # off-topic questions scored 0.53-0.57, answerable ones 0.78-0.80

app = FastAPI(title="MIA RAG Project")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _citations(retrieved: list[Retrieved], cited: tuple[int, ...]) -> list[Citation]:
    return [
        Citation(
            n=r.rank,
            id=r.chunk.id,
            title= r.chunk.title,
            source=r.chunk.source,
            page=r.chunk.page,
            text=r.chunk.text,
            score=round(r.score, 4),
            cited=r.rank in cited
        )
        for r in retrieved
    ]


@app.get("/health")
def health():
    try:
        chunks = count()
        return {"status": "ok", "chroma": "ok", "chunks": chunks}
    except Exception as e:
        return {"status": "degraded", "chroma": f"error: {e}", "chunks": 0}

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    if count() == 0:
        return QueryResponse(
            answer="El índice está vacío: sube documentos antes de preguntar",
            citations=[],
            abstained=True
        )
    try:
        retrieved = search(embed_query(req.question), req.top_k, req.source)
        ans = answer(req.question, retrieved, MIN_SCORE)
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except errors.APIError as e:
        raise HTTPException(502, f"Google AI error: {e}")

    return QueryResponse(
        answer=ans.text,
        citations=_citations(retrieved, ans.citations),
        abstained=not ans.grounded,
    )

@app.post("/ingest", response_model=IngestResponse)
def ingest(files: list[UploadFile] = File(...)) -> IngestResponse:
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"Máximo {MAX_FILES} archivos por carga")

    all_chunks: list[Chunk] = []
    documents = 0
    skipped: list[str] = []

    for upload in files:
        name = safe_filename(upload.filename or "")
        if name is None:
            skipped.append(f"{upload.filename!r}: nombre de archivo no válido")
            continue
        data = upload.file.read(MAX_BYTES + 1)

        if len(data) > MAX_BYTES:
            skipped.append(f"{name}: supera {MAX_BYTES // (1024 * 1024)} MB")
            continue
        if not data.startswith(PDF_MAGIC):
            skipped.append(f"{name}: no es un PDF")
            continue
        
        try:
            chunks = chunk_pages(load_pdf(io.BytesIO(data), source=name))
        except PdfReadError:
            skipped.append(f"{name}: PDF dañado o ilegible")
            continue

        if not chunks:
            skipped.append(f"{name}: sin texto extraíble (¿escaneado?)")
            continue

        all_chunks += chunks
        documents += 1
        # Keep the PDF so its pages can be shown next to citations.
        (DOCS_DIR / name).write_bytes(data)
        render_page.cache_clear()

    if all_chunks:
        try:
            embeddings = embed_documents([c.embed_text for c in all_chunks])
        except RuntimeError as e:
            raise HTTPException(503, str(e))
        except errors.APIError as e:
            raise HTTPException(502, f"Google AI error: {e}")
        upsert(all_chunks, embeddings)

    # The brochure is already indexed at this point, so a failed extraction is
    # reported as a warning instead of failing the whole upload.
    warnings: list[str] = []
    for source in sorted({c.source for c in all_chunks}):
        try:
            update_specs(source)
        except (errors.APIError, ValueError) as e:
            warnings.append(f"{source}: no se pudieron extraer las especificaciones ({e})")

    return IngestResponse(documents=documents, chunks=len(all_chunks), skipped=skipped, warnings=warnings)

@app.get("/sources", response_model=list[SourceInfo])
def sources() -> list[SourceInfo]:
    return [SourceInfo(**s) for s in list_sources()]

@app.post("/compare", response_model=CompareResponse)
def compare(req: CompareRequest) -> CompareResponse:
    try:
        result = compare_models(req.sources)
    except UnknownSourcesError as e:
        raise HTTPException(404, f"No están indexados: {', '.join(e.sources)}")
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except errors.APIError as e:
        raise HTTPException(502, f"Google AI error: {e}")
    
    return CompareResponse(
        models=[
            SourceInfo(
                source=source,
                title=title,
                chunks=sum(1 for _, c in result.passages if c.source == source),
            )
            for source, title in zip(req.sources, result.titles)
        ],
        rows=[
            CompareRow(
                aspect=row.aspect,
                cells=[CompareCell(value=c.value, citations=c.citations) for c in row.cells],
            )
            for row in result.rows
        ],
        passages=[
            Passage(n=n, id=c.id, title=c.title, source=c.source, page=c.page, text=c.text)
            for n, c in result.passages
        ],
    )

@app.get("/specs", response_model=list[AgitatorSpecs])
def specs() -> list[AgitatorSpecs]:
    return list(load_specs().values())

@app.post("/select", response_model=SelectResponse)
def select(req: SelectRequest) -> SelectResponse:
    specs = list(load_specs().values())
    if not specs:
        raise HTTPException(404, "Aún no hay especificaciones extraídas: indexa los catálogos o ejecuta python -m scripts.build_specs")
    return select_models(req, specs)

@app.get("/pages/{source}/{page}", response_class=Response)
def page_image(source: str, page: int) -> Response:
    try:
        image = render_page(source, page)
    except PageNotFoundError as e:
        raise HTTPException(404, str(e))
    return Response(content=image, media_type="image/jpeg", headers={"Cache-Control": "max-age=3600"})
