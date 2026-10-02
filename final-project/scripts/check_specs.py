"""Check the extracted specifications in specs.json against the brochure text."""

from __future__ import annotations

import re

from app.specs import FIELDS, load_specs
from app.store import chunks_for

COATINGS = {
    "ptfe", "pvdf", "epdm", "halar", "goma butilo", "hule vulcanizado",
    "ebonita", "neopreno", "fibra de vidrio", "pulido sanitario",
}


def _forms(value: float) -> set[str]:
    forms = {f"{value:g}"}
    if value >= 1000:
        forms |= {f"{int(value):,}".replace(",", " "), str(int(value))}
    return forms


def main() -> None:
    specs = load_specs()
    problems = []
    bounds = 0
    for spec in specs.values():
        text = re.sub(r"\s+", " ", " ".join(c.text for c in chunks_for(spec.source)))
        squashed = text.replace(" ", "")

        for field, label, _ in FIELDS:
            r = getattr(spec, field)
            for value in (r.min, r.max):
                if value is None:
                    continue
                bounds += 1
                if not any(f in text for f in _forms(value)):
                    problems.append(f"{spec.title}: {label} {value:g} isn't in the brochure text")

        coatings = [m for m in spec.materials if m.lower() in COATINGS]
        if coatings:
            problems.append(f"{spec.title}: coatings listed as materials: {coatings}")

        # The PDF splits words, so labels are matched with the spaces removed.
        if "DIÁMETRODEANCLA" not in squashed and spec.anchor_diameter_mm.max is not None:
            problems.append(f"{spec.title}: anchor diameter without a DIÁMETRO DE ANCLA label")
        if "DIÁMETRODEHÉLICE" in squashed and spec.propeller_diameter_mm.max is None:
            problems.append(f"{spec.title}: DIÁMETRO DE HÉLICE in the text but no propeller diameter")

    print(f"models: {len(specs)}, numeric bounds checked: {bounds}")
    print("\n".join(problems) if problems else "no problems found")


if __name__ == "__main__":
    main()
