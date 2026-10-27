"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

CELLS = 12                          # der „Kuchen“: zwölf Stunden Hallenzeit, 8 bis 20 Uhr
START_HOUR = 8
WEIGHT_MAX = 9                      # Bewertungen je Stunde: ganze Zahlen von 0 bis WEIGHT_MAX

N_MIN, N_MAX, DEFAULT_N = 2, 6, 3
SEED_MAX, DEFAULT_SEED = 9999, 4

MODELS = {
    "unabh": "Unabhängig (jedes Team würfelt seine Vorlieben)",
    "aehnlich": "Ähnlich (alle wollen dieselben Stunden)",
    "gegen": "Gegensätzlich (jedes Team will einen eigenen Block)",
}
MODEL_SHORT = {"unabh": "Unabhängig", "aehnlich": "Ähnlich", "gegen": "Gegensätzlich"}
DEFAULT_MODEL = "unabh"

PROTOCOLS = {
    "geteilt": "Geteilt und gewählt (2 Teams)",
    "selfridge": "Selfridge–Conway (3 Teams)",
    "messer": "Bewegliches Messer (beliebig viele)",
}
PROTOCOL_SHORT = {"geteilt": "Geteilt und gewählt", "selfridge": "Selfridge–Conway", "messer": "Bewegliches Messer"}
PROTOCOL_PEOPLE = {"geteilt": 2, "selfridge": 3, "messer": None}
DEFAULT_PROTOCOL = "messer"

# Referenzverteilungen neben dem gewählten Protokoll
REFERENCES = {
    "wohlfahrt": "Höchste Wohlfahrt (jede Stunde an das Team, das sie am meisten will)",
    "neidfrei": "Neidfrei mit höchster Wohlfahrt",
    "nachgebessert": "Protokoll nachgebessert (niemand schlechter, bei neidfreiem Protokoll weiter neidfrei)",
}
REFERENCE_SHORT = {"wohlfahrt": "Höchste Wohlfahrt", "neidfrei": "Neidfrei, beste Wohlfahrt", "nachgebessert": "Nachgebessert"}

TEAM_COLORS = ["#4c78a8", "#e8a838", "#2F6B65", "#b04a3a", "#7b6fa8", "#8c6d31"]
COLOR_ALERT = "#c0392b"

# Feste Reihen (Zufallsinstanzen mit festen Zufalls-Seeds; Anteile exakt gezählt, Wohlfahrtsverhältnisse numerisch)
SERIES_SEED = 200000
SERIES_RUNS = 200
SERIES_NS = (2, 3, 4, 5)
SERIES_PROTOCOL_CASES = (("geteilt", 2), ("messer", 2), ("selfridge", 3), ("messer", 3), ("messer", 4), ("messer", 5))

NL = chr(10)

PRESETS = {
    "Drei Teams, zwölf Stunden": {"n": 3, "model": "unabh", "seed": 4, "protocol": "messer", "weights": ""},
    "Geteilt und gewählt verschenkt Wohlfahrt": {
        "n": 2, "model": "unabh", "seed": 4, "protocol": "geteilt",
        "weights": NL.join(["1 1 1 1 1 1 3 3 3 3 3 3", "3 3 3 3 3 3 0 0 1 1 1 1"]),
    },
    "Selfridge–Conway mit Kürzung": {
        "n": 3, "model": "unabh", "seed": 4, "protocol": "selfridge",
        "weights": NL.join(["1 1 1 1 1 1 1 1 1 1 1 1", "3 3 3 3 1 1 1 1 2 2 2 2", "1 1 1 1 2 2 2 2 2 2 2 2"]),
    },
    "Bewegliches Messer: Neid ab drei Teams": {
        "n": 3, "model": "unabh", "seed": 5, "protocol": "messer",
        "weights": NL.join(["1 1 1 1 1 1 3 3 3 3 3 3", "1 1 1 1 1 1 1 1 1 1 1 1", "1 1 1 1 1 1 1 1 1 1 1 1"]),
    },
    "Neidfreiheit kostet etwas": {
        "n": 2, "model": "unabh", "seed": 4, "protocol": "geteilt",
        "weights": NL.join(["9 1 0 5 9 0 0 5 2 2 0 2", "9 1 9 5 9 0 0 5 2 0 1 1"]),
    },
    "Fünf Teams, eigene Blöcke": {"n": 5, "model": "gegen", "seed": 29, "protocol": "messer", "weights": ""},
}
PRESET_HELP = {
    "Drei Teams, zwölf Stunden": "Voreinstellung: drei Teams mit zufälligen Vorlieben für zwölf Hallenstunden, bewegliches Messer.",
    "Geteilt und gewählt verschenkt Wohlfahrt": "Team 1 schneidet bei 16 Uhr, Team 2 nimmt die linke Seite: neidfrei, aber die Stunden 14 bis 16 Uhr will Team 1 sehr und Team 2 gar nicht; ein Übertrag dieser Stunden an Team 1 brächte Team 1 25 Prozentpunkte mehr, ohne dass Team 2 verliert.",
    "Selfridge–Conway mit Kürzung": "Team 2 kürzt das erste Drittel bei 10:40 Uhr, Team 3 wählt das zweite Stück; die Kürzung teilt Team 3. Am Ende beneidet niemand: die Nutzen sind 37,0, 38,9 und 42,2 %.",
    "Bewegliches Messer: Neid ab drei Teams": "Team 2 ruft zuerst (bei 12 Uhr, ein Drittel nach seiner Bewertung), Team 1 folgt bei 16 Uhr; das letzte Stück (16 bis 20 Uhr) wäre Team 1 die Hälfte wert gewesen, sein eigenes ist ihm nur ein Drittel wert: es beneidet Team 3.",
    "Neidfreiheit kostet etwas": "Zwei Teams mit fast gleichen Vorlieben: die höchste Wohlfahrt wäre nicht neidfrei, die beste neidfreie Verteilung verliert 4,2 % davon.",
    "Fünf Teams, eigene Blöcke": "Jedes der fünf Teams will einen eigenen Block: das bewegliche Messer erreicht nur 40,1 % der Höchstwohlfahrt.",
}
