# Technische Umsetzung

## Einstieg

Die Python-Quellen sind nach Verantwortlichkeiten aufgeteilt:

- [`connect_four.py`](./connect_four.py) – unveränderlicher Spielzustand und
  Regeln.
- [`board_adapter.py`](./board_adapter.py) – Übersetzung der Hardwarewerte
  `0`, `h` und `r` in den internen Spielzustand.
- [`strategies.py`](./strategies.py) – zentrale Strategie-Fabrik.
- [`play.py`](./play.py) – lokales Terminalspiel.
- [`main.py`](./main.py) – FastAPI, Webapp und Hardwarekompatibilität.
- [`algos/README.md`](./algos/README.md) – Strategien und Heuristiken.
- [`training/README.md`](./training/README.md) – Datensatzpipeline und Viewer.

## Spielkern

[`connect_four.py`](./connect_four.py) enthält den unveränderlichen
`GameState` mit Brett, aktuellem Spieler, legalen Zügen sowie Gewinn- und
Unentschieden-Erkennung. Intern ist das Brett 6 × 7 groß; `0` steht für ein
leeres Feld, `1` und `-1` für die beiden Spieler.

## Strategien

- [`algos/random_strategy.py`](./algos/random_strategy.py) wählt zufällige
  legale Züge.
- [`algos/minimax_strategy.py`](./algos/minimax_strategy.py) verwendet
  Alpha-Beta-Minimax mit konfigurierbarer Suchtiefe und Heuristik.
- [`algos/heuristics.py`](./algos/heuristics.py) kapselt die aktuelle
  Heuristik sowie die beiden historischen WS22-Bewertungsprofile
  `ws22_minimax` und `ws22_window`.
- [`strategies.py`](./strategies.py) erzeugt die konfigurierte Strategie.

## Webapp und API

[`main.py`](./main.py) stellt die FastAPI-Endpunkte bereit, validiert
Spielzüge und bedient die statischen Dateien aus `web/`. Dataset-Läufe werden
über einen Hintergrund-Executor gestartet. Die Statusdaten werden in
`data/training/<lauf-id>/config.json` fortgeschrieben.

## Dataset-Pipeline

[`training/generate_dataset.py`](./training/generate_dataset.py) simuliert
Minimax-Partien und speichert pro Zug Brett, legale Züge, gewählten Zug,
Spieler, Suchtiefe und Partieergebnis. Die Tiefe wird für jeden Zug neu
gezogen. Symmetrische Läufe verwenden eine gemeinsame Konfiguration;
asymmetrische Läufe wählen Tiefe und Verteilung abhängig vom aktuellen
Spieler. Über `heuristic` beziehungsweise die CLI-Option `--heuristic` kann
die Bewertungsfunktion für einen Lauf ausgewählt werden; `current` bleibt der
Standard.

[`training/viewer.py`](./training/viewer.py) lädt und gruppiert gespeicherte
Läufe, dekodiert spielerrelative Bretter und berechnet die
Schwierigkeitsverteilungen für die Webansicht.

## Zentrale Funktionen

| Funktion | Verantwortung |
|---|---|
| `GameState.legal_moves()` | freie Spalten ermitteln |
| `GameState.drop_piece()` | neuen unveränderlichen Brettzustand erzeugen |
| `GameState.winner()` | horizontale, vertikale und diagonale Gewinne erkennen |
| `MinimaxStrategy.choose_move()` | besten legalen Zug bestimmen |
| `current_heuristic()` | Position aus Spielersicht bewerten |
| `generate_and_save_run()` | Trainingslauf streamingfähig speichern |
| `load_run()` | Lauf für Analyse und Webansicht aufbereiten |
