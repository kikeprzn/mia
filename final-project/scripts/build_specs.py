"""Extract the specifications of every indexed brochure into specs.json."""

from __future__ import annotations

from app.specs import FIELDS, SPECS_PATH, _describe, update_specs
from app.store import sources


def main() -> None:
    for s in sources():
        spec = update_specs(s["source"])
        print(f"\n{spec.title}")
        for field, label, unit in FIELDS:
            r = getattr(spec, field)
            print(f"  {label:<20} {_describe(r, unit):<26} p. {r.pages}")
        print(f"  {'Materiales':<20} {', '.join(spec.materials) or 'sin dato'}  p. {spec.materials_pages}")
    print(f"\nsaved to {SPECS_PATH}")


if __name__ == "__main__":
    main()
