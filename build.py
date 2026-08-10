from pathlib import Path
import csv
import hashlib
import json
import sqlite3
import tempfile
import zipfile
import genanki

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)

CSS = (ROOT / "css" / "metallic.css").read_text(encoding="utf-8")
QFMT = (ROOT / "templates" / "front.html").read_text(encoding="utf-8")
AFMT = (ROOT / "templates" / "back.html").read_text(encoding="utf-8")

MODEL_ID = 1607392319
REQUIRED_FIELDS = ("Front", "Back", "Level", "Topic", "Tags")

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

csv_counts = {}
deck_counts = {}
expected_guid_deck = {}
seen_keys = set()

for csv_file in sorted(DATA.glob("*.csv")):
    with csv_file.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != list(REQUIRED_FIELDS):
            raise ValueError(
                f"{csv_file.name}: expected CSV header {','.join(REQUIRED_FIELDS)}; "
                f"got {','.join(reader.fieldnames or [])}"
            )

        csv_count = 0
        for line_number, row in enumerate(reader, start=2):
            missing = [field for field in REQUIRED_FIELDS if not (row.get(field) or "").strip()]
            if missing:
                raise ValueError(
                    f"{csv_file.name}:{line_number}: empty required field(s): {', '.join(missing)}"
                )

            key = (row["Front"], row["Topic"])
            if key in seen_keys:
                raise ValueError(
                    f"{csv_file.name}:{line_number}: duplicate (Front, Topic): {key!r}"
                )
            seen_keys.add(key)

            deck_name = deck_for_topic(row["Topic"])
            if deck_name.endswith("::99 Other"):
                raise ValueError(
                    f"{csv_file.name}:{line_number}: completed topic is not mapped to a subdeck: "
                    f"{row['Topic']!r}"
                )
            deck = get_deck(deck_name)

            note = genanki.Note(
                model=model,
                fields=[row["Front"], row["Back"], row["Level"], row["Topic"]],
                tags=row.get("Tags", "").split()
            )

            # Stable GUID: repeated builds update the same note instead of duplicating it.
            guid_key = f'{row["Front"]}|{row["Topic"]}'
            note.guid = hashlib.sha1(guid_key.encode("utf-8")).hexdigest()[:10]
            if note.guid in expected_guid_deck:
                raise ValueError(f"GUID collision for {key!r}: {note.guid}")
            expected_guid_deck[note.guid] = deck_name

            deck.add_note(note)
            csv_count += 1
            deck_counts[deck_name] = deck_counts.get(deck_name, 0) + 1
        csv_counts[csv_file.name] = csv_count

if not csv_counts:
    raise ValueError("No CSV files found in data/")

deck_ids = [deck.deck_id for deck in decks.values()]
if len(deck_ids) != len(set(deck_ids)):
    raise ValueError("Stable deck ID collision detected")

out = OUTPUT / "Deutsch_Master_Grammar_Metallic_SUBDECKS.apkg"
genanki.Package(list(decks.values())).write_to_file(out)

def validate_package(package_path: Path):
    """Validate the generated collection, including each card's actual deck ID."""
    with zipfile.ZipFile(package_path) as package, tempfile.NamedTemporaryFile() as db_file:
        db_file.write(package.read("collection.anki2"))
        db_file.flush()

        connection = sqlite3.connect(db_file.name)
        try:
            decks_json = json.loads(connection.execute("SELECT decks FROM col").fetchone()[0])
            actual_notes = connection.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            actual_cards = connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
            rows = connection.execute(
                "SELECT notes.guid, cards.did FROM notes JOIN cards ON cards.nid = notes.id"
            ).fetchall()
        finally:
            connection.close()

    expected_notes = len(expected_guid_deck)
    if actual_notes != expected_notes:
        raise ValueError(f"Package note count mismatch: expected {expected_notes}, got {actual_notes}")
    if actual_cards != expected_notes:
        raise ValueError(f"Package card count mismatch: expected {expected_notes}, got {actual_cards}")

    actual_deck_counts = {}
    for guid, deck_id in rows:
        deck = decks_json.get(str(deck_id))
        if not deck:
            raise ValueError(f"Card for GUID {guid} references unknown deck ID {deck_id}")
        actual_deck_name = deck["name"]
        expected_deck_name = expected_guid_deck.get(guid)
        if expected_deck_name != actual_deck_name:
            raise ValueError(
                f"Card deck mismatch for GUID {guid}: expected {expected_deck_name!r}, "
                f"got {actual_deck_name!r}"
            )
        actual_deck_counts[actual_deck_name] = actual_deck_counts.get(actual_deck_name, 0) + 1

    if actual_deck_counts != deck_counts:
        raise ValueError(
            f"Package subdeck counts mismatch: expected {deck_counts!r}, got {actual_deck_counts!r}"
        )
    return actual_notes, actual_cards, actual_deck_counts


note_count, card_count, verified_deck_counts = validate_package(out)

print(f"OK: {out}")
print(f"CSV files: {len(csv_counts)}")
print("CSV rows:")
for name in sorted(csv_counts):
    print(f"  {csv_counts[name]:>3}  {name}")
print(f"Notes: {note_count}")
print(f"Cards: {card_count}")
print("Cards per subdeck (verified in collection.anki2):")
for name in sorted(verified_deck_counts):
    print(f"  {verified_deck_counts[name]:>3}  {name}")
