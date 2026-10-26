"""Einmalige Messung der README-Zahlen (nicht Teil der App): feste Pläne, Ausgabe auf stdout. Die Protokolle sind exakt gerechnet; die Wohlfahrtsverhältnisse stammen aus linearen Programmen (HiGHS)."""

import sys
import time

sys.path.insert(0, ".")
import kuc_constants as C
import kuc_evaluation as ev

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

t0 = time.time()
print("PRESETS")
for name, p in C.PRESETS.items():
    a = ev.analyse(ev.Settings(**p))
    print(name, p["protocol"], p["n"])
    for r in ev.team_rows(a):
        print("   ", r)
    for r in ev.compare_rows(a):
        print("   ", r)
    for line in ev.trace_lines(a):
        print("   ", line)
    print("   ", ev.verdict_state(a))

rows = ev.series_price()
print("REIHE 1 (Preis der Neidfreiheit)")
for r in ev.price_table(rows):
    print("   ", r)
print("   ", ev.verdict_price(rows))
rows = ev.series_protocols()
print("REIHE 2 (Protokolle)")
for r in ev.protocol_table(rows):
    print("   ", r)
print("   ", ev.verdict_protocols(rows))
rows = ev.series_blocks()
print("REIHE 3 (Zersplitterung)")
for r in ev.block_table(rows):
    print("   ", r)
print("   ", ev.verdict_blocks(rows))
print("sec", round(time.time() - t0, 1))
