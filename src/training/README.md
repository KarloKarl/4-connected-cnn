# Training

Dieses Verzeichnis erzeugt und analysiert Minimax-basierte Trainingsdaten.

## Dateien

| Datei | Zweck |
|---|---|
| [`generate_dataset.py`](./generate_dataset.py) | Simuliert Partien und schreibt Trainingsbeispiele. |
| [`viewer.py`](./viewer.py) | Lädt Läufe, gruppiert Partien und berechnet Verteilungen. |
| [`__init__.py`](./__init__.py) | Paketdefinition. |

## Pipeline

1. `choose_depth` zieht pro Zug eine Minimax-Tiefe aus `uniform` oder `bell`.
2. `iter_game_examples` simuliert Partien und erzeugt ein Beispiel je Zug.
3. `encode_state` speichert das Brett aus Sicht des aktuellen Spielers.
4. `write_dataset_stream` schreibt große Läufe inkrementell als JSON-Array.
5. `generate_and_save_run` speichert zusätzlich `config.json` mit Status und
   vollständiger Konfiguration.
6. `viewer.load_run` bereitet gespeicherte Läufe für die Webansicht auf.

## CLI

```powershell
$env:PYTHONPATH = "src"
pipenv run python -m training.generate_dataset `
  --games 100 `
  --min-depth 1 `
  --max-depth 5 `
  --heuristic current `
  --output-root data/training
```

Ein Lauf enthält:

```text
data/training/<lauf-id>/data.json    Trainingsbeispiele
data/training/<lauf-id>/config.json  Konfiguration und Status
```

Für große Datenmengen `generate_and_save_run` beziehungsweise den Streaming-
Writer verwenden, damit nicht alle Beispiele gleichzeitig im Arbeitsspeicher
liegen. `player_configs` ermöglicht asymmetrische Tiefen und Verteilungen für
Spieler `1` und `-1`.
