"""Compare agitator models side by side from their full spec sheets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from google.genai import types
from pydantic import BaseModel

from app.chunk import Chunk
from app.embed import get_client
from app.generate import GENERATE_MODEL
from app.store import chunks_for

NOT_SPECIFIED = "No especificado"
# Models are labelled with a letter instead of their title: the schema only
# allows these values, so Gemini can't answer with a name from the brochure
# text such as "SERIE HELICOIDAL NC(H)".
MODEL_KEYS = ["A", "B", "C", "D"]

class UnknownSourcesError(Exception):
    def __init__(self, sources: list[str]):
        super().__init__(sources)
        self.sources = sources

class Cell(BaseModel):
    model: Literal["A", "B", "C", "D"]
    value: str
    citations: list[int]

class Row(BaseModel):
    aspect: str
    cells: list[Cell]

class Comparison(BaseModel):
    rows: list[Row]


# A fixed list keeps every comparison to the same rows, names and order;
# without it Gemini picked a different set of aspects on each run.
ASPECTS = [
    "Materiales de fabricación",
    "Diámetro de hélice",
    "Diámetro de ancla",
    "Longitud de eje",
    "Potencia del motor",
    "Velocidad de salida",
    "Reductor",
    "Acoplamiento eje-motorreductor",
    "Acoplamiento eje-hélice",
    "Estanqueidad",
    "Volumen del reactor",
]

COMPARE_PROMPT = f"""You compare Autmix industrial agitator models.

Rules:
- Use ONLY the numbered passages. Never use outside knowledge.
- Write in Spanish.
- Make one row for each of these aspects, with exactly these names and in
  this order, whenever any model's passages mention it:
  {", ".join(ASPECTS)}.
  After them, add rows for any other technical aspect the passages mention.
- Each passage starts with "Modelo" and a letter. Each row has one cell
  per model; in "model", write that model's letter.
- Keep values short, like "2 000 - 10 000 mm" or "18.5 - 400 kW".
- Each cell cites the passages its value comes from.
- If a model's passages don't mention an aspect, use "{NOT_SPECIFIED}"
  with no citations.
- Never take a model's value from another model's passages.
- The text was extracted from PDFs and some words are split, e.g.
  "DIÁ METRO" means "DIÁMETRO". Read them as the intended word."""

def _number(chunks: list[Chunk], keys: dict[str, str]) -> tuple[str, dict[int, str]]:
    lines = []
    owner: dict[int, str] = {}
    for n, c in enumerate(chunks, start=1):
        key = keys[c.source]
        lines.append(f"[{n}] Modelo {key} ({c.title}), p. {c.page}: {c.text}")
        owner[n] = key
    return "\n".join(lines), owner

def _check(table: Comparison | None, owner: dict[int, str], models: list[str]) -> list[Row]:
    if table is None:
        return []
    rows = []
    for row in table.rows:
        by_model = {c.model: c for c in row.cells if c.model in models}
        cells = []
        for model in models:
            cell = by_model.get(model)
            valid = [n for n in dict.fromkeys(cell.citations) if owner.get(n) == model] if cell else []

            if cell and valid and cell.value.strip() and cell.value.strip() != NOT_SPECIFIED:
                cells.append(Cell(
                    model=model,
                    value=cell.value.strip(),
                    citations=valid
                ))
            else:
                cells.append(Cell(
                    model=model,
                    value=NOT_SPECIFIED,
                    citations=[]
                ))
        if any(c.citations for c in cells):
            rows.append(Row(
                aspect=row.aspect.strip(),
                cells=cells
            ))
    return rows

@dataclass(frozen=True)
class ComparisonResult:
    titles: list[str]
    rows: list[Row]
    passages: list[tuple[int, Chunk]]

def compare(sources: list[str]) -> ComparisonResult:
    per_source = {s: chunks_for(s) for s in sources}
    missing = [s for s, chunks in per_source.items() if not chunks]

    if missing:
        raise UnknownSourcesError(missing)

    chunks = [c for s in sources for c in per_source[s]]
    titles = [per_source[s][0].title for s in sources]
    keys = dict(zip(sources, MODEL_KEYS))
    context, owner = _number(chunks, keys)

    response = get_client().models.generate_content(
        model=GENERATE_MODEL,
        contents=context,
        config=types.GenerateContentConfig(
            system_instruction=COMPARE_PROMPT,
            temperature=0,
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(thinking_budget=1024),
            response_mime_type="application/json",
            response_schema=Comparison,
        ),
    )
    rows = _check(response.parsed, owner, [keys[s] for s in sources])
    return ComparisonResult(titles=titles, rows=rows, passages=list(enumerate(chunks, start=1)))