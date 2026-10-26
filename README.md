# Kuchenteilung: neidfrei, proportional, effizient? – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-kuchenteilung-demo.streamlit.app/)** -->

Stück der Linie **Abstimmen und Fair Teilen** (Konzepte-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“). Verwandt: [mietaufteilung-demo](https://github.com/sebastian-hanisch/mietaufteilung-demo) (neidfreie Preise für Zimmer), [unteilbare-gueter-demo](https://github.com/sebastian-hanisch/unteilbare-gueter-demo) (ganze Güter fair verteilen), [gemeinsames-budget-demo](https://github.com/sebastian-hanisch/gemeinsames-budget-demo) (Verteilen mit Zustimmung) und [sitzverteilung-demo](https://github.com/sebastian-hanisch/sitzverteilung-demo) (Sitze auf Verbände).
Die Demo fragt: **Mehrere Teams teilen sich zwölf Stunden Hallenzeit, und jedes bewertet jede Stunde anders. Die Zeit lässt sich beliebig teilen („Kuchenteilung“). Was leisten die klassischen Protokolle (Geteilt und gewählt, Selfridge–Conway, bewegliches Messer), und was kostet die Fairness gegenüber der effizientesten Verteilung?** Geprüft werden drei Eigenschaften: **proportional** (jedes Team bekommt nach eigener Bewertung mindestens 1/n), **neidfrei** (kein Team zöge ein fremdes Stück dem eigenen vor) und **Pareto-effizient** (niemand kann besser gestellt werden, ohne dass ein anderes Team verliert).

Der Kern ist eigener Code (`fractions`, `numpy`, `scipy`): die drei Protokolle rechnen **exakt mit Brüchen** (jeder Schnittpunkt löst eine lineare Gleichung innerhalb einer Stunde), die Referenzverteilungen sind **lineare Programme** über den Anteilen je Stunde (HiGHS). Unabhängige Orakel in den Tests zählen bei kleinen Instanzen **alle Ecken des zulässigen Bereichs mit Brüchen** auf, suchen Schnittpunkte durch Halbierung und prüfen Neidfreiheit und Proportionalität aus den Zellanteilen neu.

## Warum dieses Problem

Wer eine Halle, einen Tag oder ein Grundstück teilt, hört oft: „Geteilt und gewählt ist fair.“ Das stimmt (neidfrei, proportional) – aber **fair heißt nicht effizient**. Die Demo zeigt, dass die Protokolle fast nie Pareto-effizient sind: bei **3.600** geprüften Protokollergebnissen waren es **26** (0,7 %). Sie verschenken im Mittel 16 bis 32 % der möglichen Gesamtzufriedenheit (Summe der Nutzen: 84,3 % der Höchstwohlfahrt bei Geteilt und gewählt, 77,7 % bei Selfridge–Conway, 68,2 % bei fünf Teams mit dem Messer). Man bekäme sie **ohne einen Verlierer** zurück: nachgebessert liegen die Protokolle bei 97 bis 100 % (in den Zeilen mit gegensätzlichen Vorlieben bei 91 bis 96 %).
Der Plan erwartete: „Neidfreiheit kostet Effizienz.“ Das **trifft für diese Zufallsvorlieben nicht zu**: die beste neidfreie Verteilung verliert im Mittel nur **0,7 %** der Höchstwohlfahrt (schlechtester Fall 9,2 %). Was Effizienz kostet, ist nicht die Neidfreiheit, sondern das **Protokoll**. Dazu kommt der Preis in der Praxis: effiziente Verteilungen **zerstückeln** die Hallenzeit (bis zu 3,4 Blöcke je Team statt eines).

## Modell

**Kuchen.** Das Intervall [0, 12] aus zwölf Stunden (8 bis 20 Uhr). Jedes Team vergibt je Stunde ein ganzzahliges Gewicht von 0 bis 9; die Bewertung ist stückweise konstant und auf 1 für den ganzen Kuchen normiert. Innerhalb einer Stunde ist jede Minute gleich viel wert.
**Protokolle** (Gleichstand: kleinere Teamnummer). *Geteilt und gewählt (2 Teams):* Team 1 schneidet bei seiner Hälfte, Team 2 wählt die höher bewertete Seite (bei Gleichstand die linke). *Selfridge–Conway (3 Teams):* Team 1 schneidet in drei gleiche Stücke, Team 2 kürzt das höchstbewertete auf das zweitbeste, Team 3 wählt (hat es das gekürzte Stück nicht, bekommt es Team 2), die Kürzung teilt das Team ohne gekürztes Stück in drei gleiche Teile, es wählen der Halter des gekürzten Stücks, Team 1, der Teiler. *Bewegliches Messer (Dubins–Spanier, beliebig viele):* wer zuerst ruft (links vom Messer 1/n wert), bekommt das Stück; das letzte Team den Rest.
**Referenzen.** *Höchste Wohlfahrt:* jede Stunde an das Team mit der höchsten Dichte (nicht neidfrei). *Neidfrei, beste Wohlfahrt:* größte Summe der Nutzen unter „kein Neid“. *Nachgebessert:* größte Summe der Nutzen, ohne dass ein Team unter seinen Protokollnutzen fällt (und neidfrei, wenn das Protokoll es war). *Preis der Neidfreiheit* = 1 − beste neidfreie Wohlfahrt / höchste Wohlfahrt.
Formeln und Lesehilfe stehen im 📐-Expander der App.

## Methodik

- **Kern** (`kuc_algorithm.py`): Bewertung und Schnittpunkte (`quantile`), die drei Protokolle mit Ablaufprotokoll (`trace`), Neid, Proportionalität, Überdeckung, Zellanteile, die linearen Programme (`optimize`), Pareto-Prüfung (`pareto_improvement`).
- **Szenario und Auswertung** (`kuc_scenario.py`, `kuc_evaluation.py`): drei Erzeuger für die Gewichte (unabhängig, ähnlich, gegensätzlich), Texteingabe mit Prüfung (eine Zeile je Team, zwölf Zahlen), vier Verteilungen mit allen Kennzahlen, Ablauftext, drei feste Reihen, alle Verdikte als reine Funktionen.
- **Oberfläche** (`app.py`): sechs Schnellstart-Szenarien (von Hand nachgerechnet), Protokoll, Zahl der Teams, Vorlieben, Zufalls-Seed, Textfeld für eigene Bewertungen, Bewertungskurven, Zeitstreifen der vier Verteilungen, Tabellen für Stücke und Neid, Kernfrage mit Vergleich der vier Verteilungen, drei Reiter mit festen Reihen, Annahmen und Formeln.

## Befunde (gemessen, keine Behauptungen)

Die Protokolle sind **exakt gerechnet**; die Wohlfahrtsverhältnisse stammen aus linearen Programmen (Toleranz 10⁻⁷, Anzeige auf eine Stelle). Die drei Reihen zählen je Zeile **200 Zufallsinstanzen** mit festen Zufalls-Seeds (zwölf Stunden, Gewichte 0 bis 9).

| Frage | Befund | Test |
|---|---|---|
| Stimmt der Kern? | Lineare Programme gleich der **exakten Eckenaufzählung** mit Brüchen (ohne Nebenbedingung, neidfrei, proportional, mit Untergrenzen); Schnittpunkte gleich der Halbierung und exakt (Wert genau der Zielwert, links davon kleiner); Geteilt und gewählt, Selfridge–Conway (auch mit Gleichständen und Nullgewichten) und Messer erzeugen vollständige, überschneidungsfreie Verteilungen; eine Rasterprobe findet nie ein besseres neidfreies Ergebnis als das LP. | `test_oracle_kuchenteilung.py`, `test_algorithm.py` |
| Welche Eigenschaften haben die Protokolle? | **Geteilt und gewählt** und **Selfridge–Conway** sind in allen 200 Instanzen jeder Zeile **neidfrei und proportional**. Das **Messer** ist immer proportional und mit zwei Teams neidfrei, **ab drei Teams in keiner von 1.800 Instanzen**: der erste Rufer bewertet die beiden übrigen Stücke zusammen mit genau 2/3, also eines mit mehr als 1/3. | `test_claims.py::test_envy_freeness_proportionality_and_efficiency_counts`, `test_oracle_kuchenteilung.py::test_the_first_caller_of_the_knife_values_the_rest_at_exactly_two_thirds` |
| Sind sie effizient? | **Nein, fast nie:** nur **26 von 3.600** Protokollergebnissen sind Pareto-effizient (Geteilt und gewählt: 3 von 200 bei ähnlichen und 14 bei gegensätzlichen Vorlieben, 0 bei unabhängigen). | `test_claims.py::test_envy_freeness_proportionality_and_efficiency_counts` |
| Wie viel Wohlfahrt bleibt liegen? | Summe der Nutzen im Verhältnis zur Höchstwohlfahrt, unabhängige Vorlieben: Geteilt und gewählt **80,9 %**, Selfridge–Conway 78,3 %, Messer mit 3 / 4 / 5 Teams 75,9 / 73,8 / 73,2 %. Bei gegensätzlichen Vorlieben fällt das Messer von 80,6 % (2 Teams) auf **44,6 %** (5 Teams). Nachgebessert (niemand schlechter): 99,7 % (Geteilt und gewählt, unabhängig), 96,8 % (Messer, 5 Teams), 90,9 bis 95,8 % bei gegensätzlichen Vorlieben. | `test_claims.py::test_welfare_of_the_protocols_and_after_improvement` |
| Was kostet Neidfreiheit? | Beste neidfreie Wohlfahrt im Verhältnis zur Höchstwohlfahrt: **im Mittel 99,3 %** über 2.400 Instanzen (Preis **0,7 %**), unabhängige Vorlieben 2 / 3 / 4 / 5 Teams: 100,0 / 99,7 / 99,3 / 98,5 %; **schlechtester Fall 90,8 %** (5 Teams, ähnliche Vorlieben). Bei gegensätzlichen Vorlieben ist die höchste Wohlfahrt schon neidfrei (Preis 0). Der Preis wächst mit der Zahl der Teams. | `test_claims.py::test_price_of_envy_freeness_mean_and_worst_case` |
| Wie oft ist die höchste Wohlfahrt schon neidfrei? | Unabhängige Vorlieben, 2 / 3 / 4 / 5 Teams: in 174 / 97 / 23 / 6 von 200 Instanzen; ähnliche Vorlieben: 52 / 17 / 2 / 0. | `test_claims.py::test_how_often_the_highest_welfare_is_already_envy_free` |
| Zersplitterung | Mittlere Zahl getrennter Blöcke je Team (unabhängige Vorlieben, 2 / 3 / 4 / 5 Teams): Messer immer **1,0**, höchste Wohlfahrt 3,35 / 2,89 / 2,41 / 2,00, beste neidfreie Verteilung 3,39 / 3,16 / 2,84 / 2,56. | `test_claims.py::test_blocks_per_team` |
| Schnellstart-Szenarien | Alle von Hand nachgerechnet: **Geteilt und gewählt** (Team 1 schneidet bei 16 Uhr, Team 2 nimmt links mit 9/11, Team 1 bleibt bei 1/2; ein Tausch gäbe Team 1 3/4), **Selfridge–Conway mit Kürzung** (Nutzen 10/27, 7/18, 19/45; Team 2 kürzt bei 10:40 Uhr), **Messer: Neid ab drei Teams** (Team 1 beneidet Team 3: 1/2 gegen 1/3), **Neidfreiheit kostet etwas** (Preis 4,2 %), **fünf Teams mit eigenen Blöcken** (Messer: 40,1 % der Höchstwohlfahrt). | `test_presets.py`, `test_algorithm.py` |
| Plan gegen Messung | Der Plan erwartete „Neidfreiheit kostet Effizienz (Messen über Zufallsbewertungen)“. Gemessen: **kaum** (0,7 % im Mittel); die Lücke liegt beim Protokoll (8 bis 51 Prozentpunkte zwischen Protokollergebnis und Nachbesserung). | – |

## Ehrliche Grenzen

- **Ehrliche Bewertungen.** Jedes Team nennt seine wahre Bewertung; wer die anderen kennt, kann taktieren (das ist ein eigenes Thema, siehe `taktisch-waehlen-demo`).
- **Stückweise konstant und additiv.** Wer zusammenhängende Blöcke braucht (ein Spiel dauert 90 Minuten), hat keine additive Bewertung; die Demo zählt nur die Blöcke.
- **Erzeugte Vorlieben.** Die Befunde gelten für die drei Erzeuger (unabhängige Gewichte 0 bis 9, ähnliche Grundform mit Rauschen, eigene Blöcke); echte Vorlieben können mehr Neid-Kosten haben. Der **schlechteste Fall** der Reihe (9,2 %) ist der schlechteste in 200 Instanzen je Zeile, keine Schranke.
- **Selfridge–Conway gilt nur für drei Teams.** Neidfreie Protokolle für beliebig viele Teams gibt es (Aziz und Mackenzie, aus dem Gedächtnis), sie brauchen eine riesige Zahl von Schritten und sind hier nicht umgesetzt; für vier bis sechs Teams zeigt die Demo nur das Messer (proportional) und die Referenzen aus den linearen Programmen.
- **Die Referenzen sind Rechnungen, keine Protokolle.** Sie setzen voraus, dass jemand alle Bewertungen kennt. Die LP-Ergebnisse sind numerisch (HiGHS) mit Toleranz 10⁻⁷; bei mehreren gleich guten Verteilungen kann die gezeigte Zeitaufteilung je Plattform verschieden sein (die Wohlfahrt nicht).
- **Gleichstände.** Kleinere Teamnummer; Geteilt und gewählt: bei gleicher Bewertung beider Seiten nimmt Team 2 die linke.
- **Literatur** (aus dem Gedächtnis, nicht im Original geprüft): Steinhaus (1948); Dubins und Spanier (1961); Selfridge und Conway (um 1960); Aziz und Mackenzie (FOCS 2016); Caragiannis u. a. zum Preis der Fairness.

## Befunde und Korrekturen gegenüber dem Plan

- **Port:** 9197.
- **Plan:** „stetiges Gut (Zeitfenster, Fläche), stückweise konstante Bewertungen; Geteilt-und-gewählt (2), Selfridge–Conway (3), bewegliches Messer; Neidfreiheit, Proportionalität, Effizienz; Einordnung Aziz–Mackenzie“. Umgesetzt (Aziz–Mackenzie als Einordnung in Annahmen und Literatur).
- **Neu gegenüber dem Plan:** die **Referenzverteilungen aus linearen Programmen** (höchste Wohlfahrt, beste neidfreie, nachgebessertes Protokoll) und der **Preis der Neidfreiheit**; die **Zersplitterung** als praktische Kosten; eigene Bewertungen per Textfeld.
- **Vormessung („Hook früh vormessen“)** vor dem Bau (120 Instanzen je Zelle, anderes Skript): Geteilt und gewählt und Selfridge–Conway neidfrei, Messer ab drei Teams nie, Protokolle fast nie Pareto-effizient, Neidfreiheit kostet höchstens wenige Prozent: dieselbe Rangfolge wie hier; **keine Zahl daraus** steht in dieser README.
- **Reglerspanne:** Teams 2 bis 6 (eigene Eingabe: 2 bis 6 Zeilen), Gewichte 0 bis 9, zwölf Stunden fest.

## Verifikation

- **Kern:** jede Einheit an Mini-Fällen von Hand (Geteilt und gewählt mit 1/2 gegen 9/11, Selfridge–Conway mit Kürzung bis 10/27, 7/18, 19/45, Messer mit Neid, Gleichstände, Schnittpunkte in Zellen mit Dichte 0, Preis der Neidfreiheit 19/18 gegen 11/10).
- **Orakel:** exakte Eckenaufzählung für die linearen Programme, Halbierung für die Schnittpunkte, Neuberechnung aus Zellanteilen, Ketten (neidfrei ⇒ proportional ⇒ Wohlfahrt unter der Höchstwohlfahrt), Raster-Gegenprobe, Eigenschaften über Hunderte Zufallsinstanzen mit vielen Gleichständen.
- **Reihen und Texte:** jede Zahl dieser README in `tests/test_claims.py`; Verdikte, Tabellen, Ablauftexte und Eingabefehler als reine Funktionen (`tests/test_verdicts.py`), Randfälle und Adresszeile (`tests/test_edge_cases.py`).
- **Presets, Layout, Oberfläche:** wie in allen Demos (Presets vollständig und im Regelbereich, keines auf dem oberen Rand der Teamzahl, kein Preset entsteht durch Änderung eines einzigen Reglers, Schnellstart oben, aktives Preset hervorgehoben, AppTest jeder Button und jeder Regler an den Rändern, Footer, Laufzeit-Importe).
- **Mutationsprüfung** (`tools/mutate_demo.py`): 140 Stellen im Kern `kuc_algorithm.py`, **138 gefangen**, **2 als äquivalent festgehalten** (`x < end` gegen `x <= end` in `quantile`: die Schleife endet über `j < m` ohne anderes Ergebnis; `hi > lo` gegen `>=` in `value`: ein leeres Stück trägt null bei). Der erste Lauf ließ 10 überleben: **vier Mutanten an drei echten Lücken** (eine Gleitkomma-Überschreitung der Zellgrenze in `pieces_from_shares`, ein `end` hinter dem Kuchen in `quantile` mit zwei Mutanten, ein negatives Gewicht bei positiver Summe in `valuation`; je ein neuer Test), **vier Mutanten an zwei überflüssigen Absicherungen** (`lower[i] > 0` im LP und `v[j] > 0` in `quantile`: beide Fälle sind ohne die Prüfung gleich richtig, die Prüfungen wurden entfernt) und die zwei äquivalenten.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `kuc_algorithm.py` | Kern: Schnittpunkte, drei Protokolle, Eigenschaften, lineare Programme |
| `kuc_constants.py` | Regler-Grenzen, feste Reihen, Farben, Presets |
| `kuc_evaluation.py` | Analyse, Tabellen, Ablauftexte, Verdikte, drei feste Reihen |
| `kuc_layout.py` | Fester Kopf (Stylesheet) |
| `kuc_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `kuc_scenario.py` | Gewichte (drei Erzeuger), Texteingabe |
| `kuc_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `messen.py` | Einmalige Messung der Zahlen in dieser README (nicht Teil der App) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Kern, Orakel, Reihen und Claims, Verdikte, Randfälle, Szenario, Presets, Abbildungen, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Neidfreie Protokolle für beliebig viele Teams** (Aziz und Mackenzie): eine riesige Zahl von Schritten, kein lehrreiches Bild; die Referenz aus dem LP zeigt, was neidfrei möglich wäre.
- **Zusammenhängende Stücke erzwingen** (jedes Team genau ein Block): ein anderes Problem, das Neidfreiheit nicht immer erlaubt.
- **Taktisches Verhalten, Schätzfehler der Bewertungen, verschieden große Ansprüche** der Teams (gewichtete Anteile): jeweils ein eigenes Thema.
- **Mehrere Tage oder Räume:** die Halle ist ein einziger Tag mit zwölf Stunden.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
