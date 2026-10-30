# Gamestate
- Einheitliches Board
  - 7 Spalten
  - 6 Reihen
  - Repräsentation der Steine
    - -1 --> Gegnerischer Stein (aus sicht des CNNs)
    - 0 --> Unbelegt
    - 1 --> Eigener Stein (aus sicht des CNNs)
    --> Geeignete Repräsnetaion für CNN da es simpel Eigene/Generische Steine filtern kann

# Speildurchführung 
- Klare Schnittstellen um Gegner auszuwählen
  - Eingehend
    - Modus
    --> CNN / MiniMax
    - Schwierigkeit
    --> 0 - 10
    (*Relevant für Gruppe: Spielsteurung*)
  - Intern
    - Dynamisch zwischen Modus wechseln (Aktuell ist MiniMax gehardcoded)
    - Schwierigkeit (Wie bisher)
- (Schiedsrichter)

# CNN Training
- Optimierung Codebasis
    - **Heuristik**
- Erzeugen von Trainingsdaten
    - Mit sehr tiefem Minimax
    - Leistung > Latenz
    - Minimax gegen sich selbst spielen lassen
      - Ausgangssituation
      - Entscheidung (Spalte 1-7)
- Modell Designen
  - Eingang:
    - 6(Zeilen) x 7 (Spalten) 
    - Wertebereich: {-1,0,1}
  - Ausgang
    - 7 Werte (jeweils Bewertung für eine Spalte)
  - Topologie
    - **Experimentell bestimmen**