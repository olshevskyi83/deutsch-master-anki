Deutsch Master Anki — starter

1) python3 -m venv .venv
2) source .venv/bin/activate
3) pip install -r requirements.txt
4) python build.py

Result:
output/Deutsch_Master_Grammar_Metallic_SUBDECKS.apkg

Після build скрипт перевіряє CSV, кількість нотаток і карток, а також фактичний
deck ID кожної картки всередині collection.anki2. Для повторного тестування
після зміни структури підколод див. IMPORT_SUBDECKS.txt.
