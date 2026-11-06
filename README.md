> **Transparenzhinweis:** Ab Commit [`e654e0192c1b8f0d31c2220e9bd7c60fba5b66ec`](https://github.com/KarloKarl/4-connected-cnn/commit/e654e0192c1b8f0d31c2220e9bd7c60fba5b66ec) wurde bei Entwicklung, Überarbeitung und Dokumentation dieses Projekts KI eingesetzt.

# Connect Four

Connect-Four-Spielalgorithmus mit zentraler Spielzustandslogik, Random- und
Alpha-Beta-Minimax-Strategie, FastAPI-Webapp und Minimax-basiertem
Datensatzgenerator.

## Schnellstart

```powershell
pipenv install
pipenv run uvicorn main:app --app-dir src --host 127.0.0.1 --port 8094
```

Anschließend [http://127.0.0.1:8094/play](http://127.0.0.1:8094/play) öffnen.

Die interaktive API-Dokumentation ist unter
[http://127.0.0.1:8094/docs](http://127.0.0.1:8094/docs) verfügbar.
Die alternative ReDoc-Dokumentation steht unter
[http://127.0.0.1:8094/redoc](http://127.0.0.1:8094/redoc) bereit.

### Dockerfile bauen

```powershell
docker build -t connect-four .
docker run --rm -p 8094:8094 -v "${PWD}/data:/app/data" connect-four
```

Das Image installiert die Pipenv-Abhängigkeiten aus `Pipfile.lock` und startet
den Webservice auf Port 8094. Datensätze bleiben durch das Volume erhalten.

### Docker Compose

Mit einer `compose.yaml` im Projektverzeichnis:

```yaml
services:
  connect-four:
    build: .
    ports:
      - "8094:8094"
    volumes:
      - ./data:/app/data
```

Starten und beenden:

```powershell
docker compose up --build
docker compose down
```

Die Webapp ist anschließend unter
[http://localhost:8094/play](http://localhost:8094/play) erreichbar.

Die Webapp bietet:

- **Live-Spiel:** Mensch gegen Random oder Minimax (Schwierigkeit 1–6)
- **Daten generieren:** benannte Datensatzläufe im Hintergrund starten
- **Nachvollziehen:** Spiele, Züge, Minimax-Tiefen und Ergebnisse analysieren
- **Symmetrische oder asymmetrische Schwierigkeit:** getrennte Konfigurationen
  und Verteilungen für Spieler 1 und -1

## Datensätze per CLI

```powershell
$env:PYTHONPATH = "src"
pipenv run python -m training.generate_dataset `
  --games 1000 `
  --min-depth 1 `
  --max-depth 5 `
  --distribution uniform `
  --batch-size 100 `
  --seed 42
```

Läufe werden standardmäßig unter `data/training/<lauf-id>/` gespeichert:

- `data.json`: Trainingsbeispiele
- `config.json`: vollständige Erzeugungskonfiguration und Status

`uniform` verteilt Tiefen gleichmäßig, `bell` bevorzugt mittlere Tiefen.
Die Tiefe wird für jeden Minimax-Zug neu gezogen. Der erste Zug ist
standardmäßig zufällig; mit `--no-random-first-move` wird er deterministisch
erzeugt.

Die Bewertungsfunktion kann über `--heuristic` gewählt werden:

```powershell
pipenv run python -m training.generate_dataset --heuristic ws22_minimax
```

Verfügbar sind `current` (Standard), `ws22_minimax` und `ws22_window`. Die
beiden WS22-Varianten reproduzieren die historischen Heuristiken getrennt von
der aktuellen Implementierung.

Für Tree-Learning können zusätzlich alle besuchten Minimax-Zustände gespeichert
werden:

```powershell
pipenv run python -m training.generate_dataset `
  --games 100 `
  --tree-learning
```

Dann enthält jedes Beispiel `tree_nodes` mit Brett, legalen Zügen, Suchwert,
Resttiefe und `exact`. Alpha-Beta-Cutoffs werden als nicht-exakt markiert.
Die Option ist bewusst opt-in, da sie die Datensatzgröße stark erhöhen kann.

Für ein dynamisches, spielerrelatives Lernziel kann zusätzlich die
Depth-Heuristic aktiviert werden:

```powershell
pipenv run python -m training.generate_dataset `
  --games 100 `
  --depth-heuristic `
  --depth-penalty 0.01
```

Die Beispiele behalten `result` als finales Partiefazit und erhalten zusätzlich
`target`. Ein schneller Sieg wird stärker belohnt, eine verzögerte Niederlage
weniger stark bestraft. Die Begrenzung auf `[-1, 1]` hält das Signal stabil.

## Lokales Terminalspiel

```powershell
pipenv run python src/play.py --algorithm minimax --difficulty 4
pipenv run python src/play.py --algorithm random
```

## Tests

```powershell
$env:PYTHONPATH = "src"
pipenv run python -m unittest discover -s tests -v
```

## Struktur

```text
src/connect_four.py              Spielzustand und Regeln
src/algos/                       Random und Alpha-Beta-Minimax
src/training/generate_dataset.py Datensatzgenerator
src/training/viewer.py           Trainingslauf-Auswertung
src/main.py                      FastAPI-Webapp und API
web/                             HTML, JavaScript und CSS
tests/                           Unit- und API-Tests
```

Weitere technische Details stehen in der [technischen Dokumentation unter
`src/README.md`](./src/README.md).

## API

- `GET /docs` – Swagger UI
- `GET /redoc` – ReDoc
- `GET /play` – Webapp
- `POST /web/move` – Live-Spielzug
- `POST /web/training/runs` – Datensatzlauf starten
- `GET /web/training/runs` – Läufe auflisten
- `GET /web/training/runs/{run_id}/status` – Laufstatus
- `GET /web/training/runs/{run_id}/games` – Spiele eines Laufs
- `GET /web/training/runs/{run_id}/games/{game_index}` – Spielschritte
- `POST /updateBoard` – bestehende Hardware-Schnittstelle

### Hardware-Schnittstelle

Die Hardwaresteuerung sendet das vollständige Brett per `POST /updateBoard`.
Das JSON enthält `Column1` bis `Column7`, jeweils mit `Row1` bis `Row6`, sowie
`Difficulty`:

```json
{
  "Column1": {"Row1": "h", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
  "Column2": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
  "Column3": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
  "Column4": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
  "Column5": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
  "Column6": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
  "Column7": {"Row1": "0", "Row2": "0", "Row3": "0", "Row4": "0", "Row5": "0", "Row6": "0"},
  "Difficulty": 4
}
```

Zulässige Zellwerte sind ausschließlich `"0"` (leer), `"h"` (Mensch) und
`"r"` (Roboter). `Row1` ist die unterste, `Row6` die oberste Zeile;
`Column1` ist links und `Column7` rechts. `Difficulty` ist die Minimax-Tiefe
von 1 bis 6.

Die Antwort beschreibt die Aktion:

```json
{
  "status": "move",
  "winner": null,
  "move": {"col": 3, "row": 0},
  "message": "Roboterzug an die Hardwaresteuerung gesendet."
}
```

`move.col` und `move.row` sind nullbasiert. Bei `status: "game_over"` ist
`winner` entweder `"HUMAN"`, `"ROBOT"` oder `"DRAW"`, und es wird kein
weiterer Roboterzug erwartet. Die API benachrichtigt die
Hardwaresteuerung intern über `http://172.17.0.1:8096/move` beziehungsweise
`/end`. Die vollständigen interaktiven Schemas und Beispiele stehen unter
[`/docs`](http://127.0.0.1:8094/docs) beim Endpunkt `POST /updateBoard`.
