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

- `GET /play` – Webapp
- `POST /web/move` – Live-Spielzug
- `POST /web/training/runs` – Datensatzlauf starten
- `GET /web/training/runs` – Läufe auflisten
- `GET /web/training/runs/{run_id}/status` – Laufstatus
- `GET /web/training/runs/{run_id}/games` – Spiele eines Laufs
- `GET /web/training/runs/{run_id}/games/{game_index}` – Spielschritte
- `POST /updateBoard` – bestehende Hardware-Schnittstelle
