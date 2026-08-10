from pathlib import Path
import csv
import hashlib
import genanki

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)

CSS = (ROOT / "css" / "metallic.css").read_text(encoding="utf-8")
QFMT = (ROOT / "templates" / "front.html").read_text(encoding="utf-8")
AFMT = (ROOT / "templates" / "back.html").read_text(encoding="utf-8")

MODEL_ID = 1607392319

model = genanki.Model(
    MODEL_ID,
    "Deutsch Master Grammar UA Metallic",
    fields=[
        {"name": "Front"},
        {"name": "Back"},
        {"name": "Level"},
        {"name": "Topic"},
    ],
    templates=[{
        "name": "Card 1",
        "qfmt": QFMT,
        "afmt": AFMT,
    }],
    css=CSS,
)

# One stable ID per deck name.
def stable_deck_id(name: str) -> int:
    raw = int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:8], 16)
    return 1_000_000_000 + (raw % 1_000_000_000)

# Map Topic -> visible Anki subdeck.
def deck_for_topic(topic: str) -> str:
    t = topic.lower()

    if "nominativ" in t:
        return "Deutsch Master Grammar::01 Cases::01 Nominativ"
    if "akkusativ vs dativ" in t:
        return "Deutsch Master Grammar::01 Cases::04 Akkusativ vs Dativ"
    if "dativ" in t and "präposition" not in t:
        return "Deutsch Master Grammar::01 Cases::03 Dativ"
    if "genitiv" in t:
        return "Deutsch Master Grammar::01 Cases::05 Genitiv"
    if "akkusativ" in t and "präposition" not in t:
        return "Deutsch Master Grammar::01 Cases::02 Akkusativ"

    if "präpositionen + akkusativ" in t:
        return "Deutsch Master Grammar::02 Prepositions::01 Akkusativ"
    if "präpositionen + dativ" in t:
        return "Deutsch Master Grammar::02 Prepositions::02 Dativ"
    if "скорочення" in t:
        return "Deutsch Master Grammar::02 Prepositions::03 Contractions"
    if "wechselpräpositionen" in t:
        return "Deutsch Master Grammar::02 Prepositions::04 Wechselpräpositionen"
    if "lage vs bewegung" in t:
        return "Deutsch Master Grammar::02 Prepositions::05 Lage vs Bewegung"
    if "часові прийменники" in t:
        return "Deutsch Master Grammar::02 Prepositions::06 Zeit"
    if "місце і напрямок" in t:
        return "Deutsch Master Grammar::02 Prepositions::07 Ort & Richtung"
    if "типові плутанини" in t:
        return "Deutsch Master Grammar::02 Prepositions::08 Typische Verwechslungen"

    return "Deutsch Master Grammar::99 Other"

decks = {}

def get_deck(name: str):
    if name not in decks:
        decks[name] = genanki.Deck(stable_deck_id(name), name)
    return decks[name]

count = 0
counts = {}

for csv_file in sorted(DATA.glob("*.csv")):
    with csv_file.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            deck_name = deck_for_topic(row["Topic"])
            deck = get_deck(deck_name)

            note = genanki.Note(
                model=model,
                fields=[row["Front"], row["Back"], row["Level"], row["Topic"]],
                tags=row.get("Tags", "").split()
            )

            # Stable GUID: repeated builds update the same note instead of duplicating it.
            key = f'{row["Front"]}|{row["Topic"]}'
            note.guid = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]

            deck.add_note(note)
            count += 1
            counts[deck_name] = counts.get(deck_name, 0) + 1

out = OUTPUT / "Deutsch_Master_Grammar_Metallic_SUBDECKS.apkg"
genanki.Package(list(decks.values())).write_to_file(out)

print(f"OK: {out}")
print(f"Cards: {count}")
print("")
print("Subdecks:")
for name in sorted(counts):
    print(f"  {counts[name]:>3}  {name}")
