# Connect-Four-Spielalgorithmus

Der Dienst berechnet Züge für ein 6x7-Connect-Four-Brett. Zusätzlich gibt
es lokale und browserbasierte Demonstratoren, in denen Mensch gegen Random
oder Alpha-Beta-Minimax spielen kann.

## Browser-Spiel

Server starten:

```powershell
pipenv run uvicorn main:app --app-dir src --host 127.0.0.1 --port 8093
```

Danach im Browser öffnen:

```text
http://127.0.0.1:8093/play
```

Die Oberfläche hat getrennte Tabs für das Live-Spiel und die Trainingsläufe.
Algorithmus und Minimax-Schwierigkeit können direkt im Live-Spiel
ausgewählt werden. Die Weboberfläche bietet die interaktiven Stufen 1 bis 6;
höhere Tiefen können wegen der längeren Berechnung weiterhin über die
Konsolen-Demo verwendet werden. Der Browser hält den Spielzustand; der Endpunkt
`POST /web/move` validiert den menschlichen Zug und berechnet den KI-Zug.
Die Browserdemo ist getrennt vom Hardware-Endpunkt `POST /updateBoard`.

Unterhalb des Live-Spiels gibt es ein Trainingspanel. Dort können vorhandene
Läufe ausgewählt, ihre vollständige `config.json` eingesehen und einzelne
Spiele Schritt für Schritt oder automatisch abgespielt werden. Ein Schritt
zeigt das gespeicherte spielerrelative Brett, den Minimax-Lehrzug, Spieler,
Tiefe und das Ergebnis der Partie. Ältere Läufe ohne `game`-/`step`-Metadaten
werden weiterhin automatisch anhand ihrer Brettfolge gruppiert. Zusätzlich
zeigt das Panel eine gemeinsame Chart-Ansicht: oben die Schwierigkeitsverteilung
der Züge im gewählten Spiel, darunter die Verteilung aller Züge des gesamten
Trainingslaufs.

## Lokales Spiel

Mit Pipenv:

```powershell
pipenv install
pipenv run python src/play.py --algorithm minimax --difficulty 4
```

Alternativen:

```powershell
pipenv run python src/play.py --algorithm random
pipenv run python src/play.py --algorithm minimax --difficulty 2 --ai-first
```

`--difficulty` ist die Minimax-Suchtiefe von 1 bis 8. Für Random hat sie
keinen Einfluss.

## Architektur

```text
src/connect_four.py
    Immutable GameState und zentrale Spielregeln
src/algos/
    random_strategy.py        Zufallsstrategie
    minimax_strategy.py       Alpha-Beta-Minimax
src/strategies.py
    Auswahl der konfigurierten Strategie
src/play.py
    lokaler interaktiver Demonstrator
src/main.py
    FastAPI-Schnittstelle für Bildverarbeitung und Hardware
src/board_adapter.py
    Übersetzung des externen h/r/0-Formats
src/training/
    Erzeugung von Minimax-Trainingsdaten
```

`GameState` speichert die Reihen von unten nach oben. Intern gilt:

```text
0  = leer
1  = aktueller eigener Stein
-1 = gegnerischer Stein
```

Spalten sind intern nullbasiert (`0` bis `6`); der Terminal-Demonstrator
zeigt sie für Menschen als `1` bis `7`.

## API

Der FastAPI-Dienst läuft standardmäßig auf Port `8093`:

```powershell
pipenv run uvicorn main:app --app-dir src --host 0.0.0.0 --port 8093
```

`POST /updateBoard` erwartet die im bisherigen Hardwarevertrag definierte
Darstellung mit `Column1` bis `Column7`, `Row1` bis `Row6` und `Difficulty`.
Der berechnete Zug wird an den Hardwaredienst auf Port `8096` weitergegeben.

## Tests

```powershell
pipenv run python -m unittest discover -s tests -v
```

Die Tests decken Spielregeln, Strategien, Board-Konvertierung, API-nahe
Zugauswahl und Trainingsdatenerzeugung ab.

## Trainingsdaten

`src/training/generate_dataset.py` erzeugt Trainingsläufe der Form:

```text
training/data/{Datum_Uhrzeit}/data.json
training/data/{Datum_Uhrzeit}/config.json
```

Beispiel für einen Lauf mit zufälliger Tiefe im Bereich 1 bis 5:

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

Die Ergebnisse werden während der Erzeugung direkt in `data.json` geschrieben
und standardmäßig alle 100 Beispiele mit `flush()` auf die Festplatte
übertragen. Die Batchgröße kann mit `--batch-size` angepasst werden. Dadurch
bleibt der Speicherverbrauch unabhängig von der Gesamtgröße des Datensatzes.
Während eines laufenden oder abgebrochenen Prozesses ist das JSON-Array noch
nicht zwingend syntaktisch abgeschlossen; nach einem erfolgreichen Lauf ist
`data.json` gültiges JSON und `config.json` erhält den Status `completed`.

Mögliche Verteilungen:

- `uniform`: Jede Tiefe im Bereich ist gleich wahrscheinlich.
- `bell`: Tiefen nahe der Mitte des Bereichs sind wahrscheinlicher.

Der erste Zug jeder Partie ist standardmäßig zufällig und wird nicht als
Minimax-Lehrerzug gespeichert. Das kann deaktiviert werden:

```powershell
pipenv run python -m training.generate_dataset --no-random-first-move
```

Mit `--seed` ist ein Lauf reproduzierbar. `config.json` enthält alle
Erzeugungsparameter, den Erstellungszeitpunkt und die Anzahl der Beispiele.
`data.json` enthält pro Beispiel das 42-Felder-Brett, legale Züge, den
Minimax-Zug, den Spieler, die für diesen Zug gezogene Tiefe und das
Spielergebnis. Die Minimax-Tiefe wird für jeden Zug neu aus der konfigurierten
Verteilung gezogen, nicht einmalig pro Partie. Bereits vorhandene Läufe
wurden noch mit der früheren Partie-Logik erzeugt und müssen für eine
per-Zug-Verteilung neu generiert werden.
Generierte Trainingsdaten werden durch `.gitignore` nicht versioniert.

Die Browseransicht liest Läufe über `GET /web/training/runs`; die Spiele und
Schritte werden über `/web/training/runs/{run_id}/games` und
`/web/training/runs/{run_id}/games/{game_index}` geladen.

Das ist die Grundlage für ein späteres CNN oder ViT. Die historischen
Notebook-/Datendateien unter `src/algos/` sind nicht Teil des Laufzeitpfads.
