# Algorithmen

Dieses Verzeichnis enthält die Zugstrategien und Bewertungsfunktionen des
Connect-Four-Projekts.

## Dateien

| Datei | Zweck |
|---|---|
| [`minimax_strategy.py`](./minimax_strategy.py) | Alpha-Beta-Minimax mit konfigurierbarer Suchtiefe und Heuristik. |
| [`heuristics.py`](./heuristics.py) | Aktuelle sowie historische WS22-Heuristiken. |
| [`random_strategy.py`](./random_strategy.py) | Wählt zufällig einen legalen Zug. |
| [`__init__.py`](./__init__.py) | Paketdefinition. |

## Heuristiken

Die Standardauswahl ist `current`. Sie bewertet jede Position aus Sicht des
übergebenen Spielers:

| Muster | Wert |
|---|---:|
| Eigene Viererkette | `+100` |
| Gegnerische Viererkette | `-100` |
| Eigene offene Dreierkette | `+5` |
| Gegnerische offene Dreierkette | `-6` |
| Eigene offene Zweierkette | `+2` |
| Gegnerische offene Zweierkette | `-2` |
| Eigener Stein in der Mittelspalte | `+3` |
| Gegnerischer Stein in der Mittelspalte | `-3` |

`_windows` erzeugt alle horizontalen, vertikalen und diagonalen Fenster mit
vier Feldern. Die Heuristik bewertet Muster, prüft aber nicht die unmittelbare
Spielbarkeit eines freien Feldes. Tatsächliche Gewinne werden vorher in
`MinimaxStrategy._search` mit deutlich höheren Terminalwerten behandelt.

Die historischen Profile `ws22_minimax` und `ws22_window` sind für Vergleiche
und reproduzierbare Trainingsläufe verfügbar. Neue Strategien sollten die
Heuristik über `get_heuristic` auswählen, statt Bewertungslogik zu duplizieren.

## Verwendung

```python
from algos.minimax_strategy import MinimaxStrategy

strategy = MinimaxStrategy(depth=4, heuristic="current")
move = strategy.choose_move(state)
```
