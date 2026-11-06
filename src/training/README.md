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

Mit `tree_learning=True` beziehungsweise `--tree-learning` werden zusätzlich
alle während jeder Minimax-Suche besuchten Zustände im jeweiligen Beispiel
unter `tree_nodes` gespeichert. Jeder Knoten enthält seinen player-relativen
Brettzustand, die legalen Züge, den Suchwert und die Resttiefe. Bei
Alpha-Beta-Cutoffs markiert `exact: false`, dass der Wert eine Schranke ist.
Die Option ist standardmäßig deaktiviert, damit bestehende Datensätze und
Dateigrößen unverändert bleiben.

Mit `depth_heuristic=True` beziehungsweise `--depth-heuristic` wird zusätzlich
zu `result` ein spielerrelativer `target` gespeichert. Der Zielwert liegt
zwischen `-1` und `1`: Ein schneller Sieg liegt näher bei `1`, eine
hinausgezögerte Niederlage näher bei `0` als eine sofortige Niederlage.
`depth_penalty` beziehungsweise `--depth-penalty` definiert den Abzug pro
verbleibendem Zug und hat standardmäßig den Wert `0.01`. `result` bleibt
unverändert und kann weiterhin als binäres Partiefazit verwendet werden.

Mit `symmetry_augmentation=True` beziehungsweise
`--symmetry-augmentation` wird jedes Beispiel zusätzlich horizontal gespiegelt
gespeichert. Dabei werden Brett, Zug, legale Züge und vorhandene `tree_nodes`
konsistent gespiegelt. Die Datensatzmenge verdoppelt sich ohne zusätzliche
Minimax-Suche; `symmetry` unterscheidet `original` und `horizontal_flip`.

## CLI

```powershell
$env:PYTHONPATH = "src"
pipenv run python -m training.generate_dataset `
  --games 100 `
  --min-depth 1 `
  --max-depth 5 `
  --heuristic current `
  --tree-learning `
  --depth-heuristic `
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
Spieler `1` und `-1`. Alle drei Lernoptionen sind außerdem im Webformular
unter **Weitere Optionen** verfügbar.
