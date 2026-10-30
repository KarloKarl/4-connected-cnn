# Technische Umsetzung

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
Spieler.

[`training/viewer.py`](./training/viewer.py) lädt und gruppiert gespeicherte
Läufe, dekodiert spielerrelative Bretter und berechnet die
Schwierigkeitsverteilungen für die Webansicht.

