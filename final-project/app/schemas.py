"""Request and response bodies for the API.

Every field a client sends is validated here, before any handler runs.
"""

from __future__ import annotations
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class QueryRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"question": "¿Qué materiales de fabricación tiene el agitador RT-RTG?", "top_k": 3}
            ]
        },
    )

    question: Question
    top_k: int = Field(3, ge=1, le=10)
    source: str | None = Field(None, max_length=255)

    @field_validator("source")
    @classmethod
    def blank_source_is_none(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class Citation(BaseModel):
    n: int  # the [n] used in the answer
    id: str
    title: str
    source: str
    page: int
    text: str
    score: float
    cited: bool

class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    abstained: bool

class IngestResponse(BaseModel):
    documents: int
    chunks: int
    skipped: list[str]  # files that produced no chunks, with the reason
    warnings: list[str] = []  # indexed, but specifications couldn't be extracted

class SourceInfo(BaseModel):
    source: str
    title: str
    chunks: int

class CompareRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "sources": [
                        "Autmix_Mixing_Solutions_Agitadores_Verticales_RT_RTG.pdf",
                        "Autmix_Mixing_Solutions_Agitadores_Verticales_RT_RTN.pdf",
                    ]
                }
            ]
        }

    )
    sources: list[str] = Field(min_length=2, max_length=4)
    
    @field_validator("sources")
    @classmethod
    def distinct_sources(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("los modelos deben ser distintos")
        return value

class CompareCell(BaseModel):
    value: str
    citations: list[int]


class CompareRow(BaseModel):
    aspect: str
    cells: list[CompareCell]  # one per model, in the same order as CompareResponse.models


class Passage(BaseModel):
    n: int
    id: str
    title: str
    source: str
    page: int
    text: str


class CompareResponse(BaseModel):
    models: list[SourceInfo]
    rows: list[CompareRow]
    passages: list[Passage]


class SpecRange(BaseModel):
    min: float | None = None  # None: open bound, e.g. "Mayor a 20 m3" has no max
    max: float | None = None
    pages: list[int] = []  # brochure pages the values come from


class AgitatorSpecs(BaseModel):
    source: str
    title: str
    tank_volume_m3: SpecRange
    propeller_diameter_mm: SpecRange
    anchor_diameter_mm: SpecRange
    shaft_length_mm: SpecRange
    motor_power_kw: SpecRange
    output_speed_rpm: SpecRange
    materials: list[str]
    materials_pages: list[int]


class SelectRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"tank_volume_m3": 50, "propeller_diameter_mm": 3000, "material": "AISI 316L"}]
        },
    )

    tank_volume_m3: float | None = Field(None, gt=0)
    propeller_diameter_mm: float | None = Field(None, gt=0)
    anchor_diameter_mm: float | None = Field(None, gt=0)
    shaft_length_mm: float | None = Field(None, gt=0)
    motor_power_kw: float | None = Field(None, gt=0)
    output_speed_rpm: float | None = Field(None, gt=0)
    material: str | None = Field(None, max_length=100)

    @field_validator("material")
    @classmethod
    def blank_material_is_none(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @model_validator(mode="after")
    def at_least_one_requirement(self) -> SelectRequest:
        if all(v is None for v in self.model_dump().values()):
            raise ValueError("indica al menos un requisito")
        return self


class Check(BaseModel):
    aspect: str
    required: str
    offered: str
    ok: bool | None  # None: the brochure doesn't give this value
    pages: list[int]


class ModelFit(BaseModel):
    source: str
    title: str
    checks: list[Check]


class SelectResponse(BaseModel):
    matches: list[ModelFit]
    rejected: list[ModelFit]
