# Deutsch Master Anki — Codex instructions

## Goal
Build a compact Ukrainian-language German grammar course for Anki covering A1–B2.

## Non-negotiable design
- Keep the existing metallic light-gray card design in `css/metallic.css`.
- Text must stay dark gray / near black and readable in Anki light and night modes.
- No illustrations, SVG, animations, or decorative complexity.
- Each card should contain one concise rule and at least one natural German example.
- Add one typical mistake only when genuinely useful.
- Explanations are in Ukrainian; German examples remain German.

## Content principles
- Prefer the smallest useful number of cards; avoid near-duplicate drills.
- Prioritize grammar needed in real A1–B2 German and for B1→B2 progression.
- Use accurate standard German.
- One CSV per topic under `data/`.
- CSV schema is exactly: `Front,Back,Level,Topic,Tags`.
- HTML inside `Back` should use the existing CSS classes: `rule`, `example`, `error`, `tip`.
- Every card must have a stable, unique combination of `Front` + `Topic` because `build.py` derives GUIDs from them.

## Deck structure
Top-level deck: `Deutsch Master Grammar`.

Current groups:
- `01 Cases`
- `02 Prepositions`

Next groups to add:
- `03 Word Order`
- `04 Conjunctions`
- `05 Tenses`
- `06 Passive`
- `07 Konjunktiv II`
- `08 Relativsaetze`
- `09 B2 Structures`

Update `deck_for_topic()` in `build.py` whenever new topics are added so every topic lands in a visible subdeck. Never allow a completed topic to fall into `99 Other`.

## Quality checks before committing
1. Parse every CSV with Python `csv.DictReader`.
2. Fail if required fields are missing or empty.
3. Fail on duplicate `(Front, Topic)` pairs.
4. Print counts per CSV and per generated subdeck.
5. Build the `.apkg` successfully with `python build.py`.
6. Do not commit `.venv/`, `output/`, `.DS_Store`, or generated `.apkg` files.

## Important Anki import behavior
Existing notes with the same GUID can remain in their old deck when importing a rebuilt package with a new subdeck structure. During development, if deck hierarchy changes, document that the tester should delete the previous `Deutsch Master Grammar` deck from Anki before doing a fresh import, unless a deliberate migration mechanism has been implemented.

## Current priority
Do not redesign infrastructure unless necessary. Focus on producing complete, accurate topic CSVs and keeping the build reliable.