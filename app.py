"""Kuchenteilung: neidfrei, proportional, effizient? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück der Linie „Abstimmen und Fair Teilen“: n Teams teilen sich zwölf Hallenstunden (ein stetiges Gut, „Kuchen“) und bewerten jede Stunde verschieden. Drei Protokolle (Geteilt und gewählt, Selfridge–Conway,
bewegliches Messer) rechnen EXAKT mit Brüchen; Neidfreiheit, Proportionalität und Pareto-Effizienz werden nachgerechnet, die beste Wohlfahrt unter Nebenbedingungen per linearem Programm. Der Kern liegt in kuc_algorithm.py.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import kuc_constants as C
import kuc_evaluation as ev
from kuc_evaluation import Settings, analyse, num
from kuc_layout import dunkles_design, kopf_css
from kuc_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from kuc_scenario import parse_weights
from kuc_visualization import build_block_series, build_division, build_price_series, build_protocol_series, build_utilities, build_values

st.set_page_config(page_title="Kuchenteilung – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _series_price():
    return ev.series_price()


@st.cache_data(show_spinner=False)
def _series_protocols():
    return ev.series_protocols()


@st.cache_data(show_spinner=False)
def _series_blocks():
    return ev.series_blocks()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in kuc_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🍰 Kuchenteilung: neidfrei, proportional, effizient?")
st.markdown(
    """
Mehrere **Teams** teilen sich **zwölf Stunden Hallenzeit** (8 bis 20 Uhr), und jedes bewertet jede Stunde anders. Weil sich die Zeit beliebig teilen lässt, heißt das Problem **Kuchenteilung**: ein stetiges Gut, das so verteilt werden soll, dass es **gerecht** zugeht.
Gerecht kann heißen: **proportional** (jedes Team bekommt mindestens seinen 1/n-Anteil nach eigener Bewertung), **neidfrei** (kein Team würde ein fremdes Stück seinem eigenen vorziehen) und **effizient** (niemand kann besser gestellt werden, ohne dass ein anderes Team verliert).
Die Demo rechnet **drei klassische Protokolle exakt** (**Geteilt und gewählt** für 2, **Selfridge–Conway** für 3, das **bewegliche Messer** für beliebig viele Teams), prüft die drei Eigenschaften nach und vergleicht mit **linearen Programmen**: der höchsten Wohlfahrt, der besten neidfreien Verteilung und dem nachgebesserten Protokoll.
Verwandt: `mietaufteilung-demo` (neidfreie Preise für Zimmer), `unteilbare-gueter-demo` (ganze Güter fair verteilen) und `gemeinsames-budget-demo` (Verteilen mit Zustimmung).

Weiter unten: die **Kernfrage**, der Abschnitt **🔬 Feste Reihen** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So wird gerechnet", expanded=True):
    st.markdown(
        """
Jedes Team gibt jeder der zwölf Stunden ein **Gewicht** von 0 bis 9; daraus wird die **Bewertung**: der Wert einer Zeitspanne ist ihr Anteil am Gesamtgewicht, der ganze Tag ist 100 % wert. Innerhalb einer Stunde ist jede Minute gleich viel wert.
1. **Geteilt und gewählt (2 Teams):** Team 1 schneidet so, dass beide Seiten für es gleich viel wert sind (je 50 %); Team 2 wählt die Seite, die es höher bewertet.
2. **Selfridge–Conway (3 Teams):** Team 1 schneidet in drei gleich bewertete Stücke; Team 2 kürzt das von ihm am höchsten bewertete, bis es dem zweitbesten gleicht; Team 3 wählt, Team 2 bekommt das gekürzte, wenn Team 3 es nicht nimmt; die Kürzung teilt das Team, das das gekürzte Stück nicht hat, in drei gleiche Teile, und es wählen zuerst das Team mit dem gekürzten Stück, dann Team 1, zuletzt das teilende.
3. **Bewegliches Messer (beliebig viele):** das Messer wandert von 8 Uhr nach rechts; wer zuerst ruft (das Stück links ist ihm 1/n wert), bekommt es und scheidet aus. Das letzte Team bekommt den Rest.
4. **Referenzen (lineare Programme):** *Höchste Wohlfahrt*: jede Stunde an das Team mit dem höchsten Gewicht (nicht neidfrei). *Neidfrei, beste Wohlfahrt*: die größte Summe der Nutzen unter der Nebenbedingung „kein Neid“. *Nachgebessert*: die größte Summe der Nutzen, bei der kein Team schlechter dasteht als im Protokoll (und bei einem neidfreien Protokoll auch weiter kein Neid).
5. **Gleichstand:** die kleinere Teamnummer. Die Protokolle rechnen mit Brüchen (keine Rundungsfehler), die linearen Programme mit HiGHS (Toleranz 10⁻⁷).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

weights_valid, _ = parse_weights(st.session_state["weights_text"])
with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Verfahren**")
    protocol = st.selectbox("Protokoll", list(C.PROTOCOLS), format_func=C.PROTOCOLS.get, key="protocol_select", help="Wer wie schneidet und wählt. Passt das Protokoll nicht zur Zahl der Teams, rechnet die Demo das bewegliche Messer.")
    st.markdown("**Teams**")
    n = st.slider("Zahl der Teams", *bounds("n_slider"), key="n_slider", disabled=weights_valid is not None, help="Wie viele Teams die Halle teilen. Bei eigenen Bewertungen bestimmt die Zahl der Zeilen den Wert.")
    model = st.selectbox("Vorlieben", list(C.MODELS), format_func=C.MODELS.get, key="model_select", disabled=weights_valid is not None, help="Wie die Bewertungen erzeugt werden.")
    seed = st.number_input("Zufalls-Seed der Bewertungen", *bounds("seed_input"), key="seed_input", step=1, disabled=weights_valid is not None)
    st.button("🎲 Neue Bewertungen erzeugen", width="stretch", on_click=randomize_seed, disabled=weights_valid is not None)
    st.markdown("**Eigene Bewertungen (optional)**")
    weights = st.text_area("Gewichte je Team und Stunde", key="weights_text", height=120, placeholder="eine Zeile je Team, zwölf Zahlen von 0 bis 9\nz. B. 1 1 1 1 1 1 3 3 3 3 3 3",
                           help=f"{C.N_MIN} bis {C.N_MAX} Zeilen, je {C.CELLS} ganze Zahlen von 0 bis {C.WEIGHT_MAX} (eine je Stunde ab 8 Uhr), getrennt durch Komma oder Leerzeichen. Leer lassen, um sie erzeugen zu lassen.")

sync_query_params({"n_slider": int(n), "model_select": model, "seed_input": int(seed), "protocol_select": protocol, "weights_text": weights})

settings = Settings(n=int(n), model=model, seed=int(seed), protocol=protocol, weights=weights)
a = _analysis(settings)
for message in a.errors:
    st.warning(message)
if a.note:
    st.info(a.note)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

d = a.divisions["protokoll"]
st.markdown("## 🎯 Ergebnis")
m1, m2, m3 = st.columns(3)
m1.metric(f"{d.name}: neidfrei", ev.yes_no(d.ef), delta="niemand beneidet" if d.ef else f"{len(d.envy)} Neidfälle", delta_color="off")
m2.metric("Summe der Nutzen", ev.pct(d.ratio), delta=f"{num(d.welfare, 2)} von höchstens {num(a.bound, 2)}", delta_color="off")
m3.metric("Pareto-effizient", ev.yes_no(d.pareto), delta="nichts zu verbessern" if d.pareto else f"nachgebessert {ev.pct(a.divisions['nachgebessert'].ratio)}", delta_color="off")
if a.source == "eingegeben":
    st.caption(f"Die eingegebenen Bewertungen bestimmen die Zahl der Teams ({a.n}); Vorlieben und Zufalls-Seed haben keine Wirkung.")
st.markdown("**So bewerten die Teams die zwölf Stunden**")
st.plotly_chart(build_values(a), width="stretch", key="values_chart")
st.markdown("**Wer bekommt wann die Halle**")
st.plotly_chart(build_division(a), width="stretch", key="division_chart")
st.caption("Je Zeile eine Verteilung: oben das gewählte Protokoll, darunter die drei Referenzen. Ein Team kann mehrere getrennte Blöcke bekommen.")
st.table(ev.team_rows(a))
for line in ev.trace_lines(a):
    st.markdown(f"- {line}")
st.markdown("**Wie bewertet jedes Team die Stücke der anderen?** (Spalte = Stück, Zeile = bewertendes Team; wer ein fremdes Stück höher bewertet als das eigene, beneidet.)")
st.table(ev.envy_rows(a))

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was kostet Fairness, und was verschenken die Protokolle?")
kind, text = ev.verdict_state(a)
getattr(st, kind)(text)
st.markdown("**Die vier Verteilungen im Vergleich**")
st.table(ev.compare_rows(a))
st.plotly_chart(build_utilities(a), width="stretch", key="utilities_chart")
st.caption("Nutzen = Wert des eigenen Stücks in Prozent des ganzen Kuchens nach der eigenen Bewertung. Die Summe der Nutzen („Wohlfahrt“) wird mit der höchsten möglichen Summe verglichen (jede Stunde an das Team, das sie am meisten will).")

st.markdown("---")

# --- Reihen --------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Feste Reihen")
st.caption(
    f"Feste Programme, unabhängig von den Reglern: je Zeile {C.SERIES_RUNS} Zufallsinstanzen mit festen Zufalls-Seeds (zwölf Stunden, Gewichte 0 bis 9); die Protokolle sind exakt gerechnet, "
    "die Wohlfahrtsverhältnisse numerisch (lineare Programme). Jede Reihe rechnet auf Klick in wenigen Sekunden bis zu einer halben Minute."
)
tab1, tab2, tab3 = st.tabs(["Was kostet Neidfreiheit?", "Was können die Protokolle?", "Wie zerstückelt ist die Halle?"])
with tab1:
    st.markdown("**Preis der Neidfreiheit.** Beste neidfreie Wohlfahrt im Verhältnis zur höchsten Wohlfahrt, Mittel und schlechtester Fall je Zahl der Teams und Vorlieben; zum Vergleich die beste proportionale Verteilung. „ohne Verlust“: in so vielen Instanzen ist die höchste Wohlfahrt schon neidfrei.")
    if st.button("Reihe rechnen", key="price_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_price()
        st.session_state["price_done"] = time.perf_counter() - t0
    if "price_done" in st.session_state:
        rows = _series_price()
        st.plotly_chart(build_price_series(rows), width="stretch", key="price_chart")
        st.table(ev.price_table(rows))
        kind, text = ev.verdict_price(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['price_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab2:
    st.markdown("**Protokolle im Vergleich.** In wie vielen Instanzen ist das Ergebnis neidfrei, proportional und Pareto-effizient, wie hoch ist die Summe der Nutzen im Verhältnis zur Höchstwohlfahrt, und wie hoch nach dem Nachbessern (niemand schlechter)?")
    if st.button("Reihe rechnen", key="protocol_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_protocols()
        st.session_state["protocol_done"] = time.perf_counter() - t0
    if "protocol_done" in st.session_state:
        rows = _series_protocols()
        st.plotly_chart(build_protocol_series(rows), width="stretch", key="protocol_chart")
        st.table(ev.protocol_table(rows))
        kind, text = ev.verdict_protocols(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['protocol_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab3:
    st.markdown("**Zersplitterung.** Mittlere Zahl getrennter Zeitblöcke je Team: das Messer schneidet immer zusammenhängende Stücke, die effizienten Verteilungen zerlegen die Zeit (unabhängige Vorlieben).")
    if st.button("Reihe rechnen", key="blocks_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_blocks()
        st.session_state["blocks_done"] = time.perf_counter() - t0
    if "blocks_done" in st.session_state:
        rows = _series_blocks()
        st.plotly_chart(build_block_series(rows), width="stretch", key="blocks_chart")
        st.table(ev.block_table(rows))
        kind, text = ev.verdict_blocks(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['blocks_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Jedes Team kennt und nennt seine Bewertung ehrlich** | Die Protokolle belohnen Ehrlichkeit nicht von selbst: wer die anderen kennt, kann beim Schneiden und Kürzen taktieren. | `taktisch-waehlen-demo` |
| **Bewertungen sind stückweise konstant und addieren sich** | Innerhalb einer Stunde ist jede Minute gleich viel wert; wer zusammenhängende Blöcke braucht (ein Spiel dauert 90 Minuten), hat keine additive Bewertung. | diese Demo (Zersplitterung) |
| **Zeit ist beliebig teilbar** | Reale Zeitfenster haben Mindestlängen und Wechselzeiten; die Demo zählt nur die Blöcke. | – |
| **Selfridge–Conway ist hier das Protokoll für genau drei Teams** | Für beliebig viele Teams gibt es neidfreie Protokolle (Aziz und Mackenzie, aus dem Gedächtnis) mit einer riesigen Zahl von Schritten; die Demo zeigt sie nicht. | – |
| **Das bewegliche Messer ist nur proportional** | Ab drei Teams ist das Ergebnis fast nie neidfrei, weil das erste Team, das ruft, die beiden anderen Stücke zusammen mit 2/3 bewertet (Befund der Reihen). | diese Demo |
| **Die Referenzen sind Rechnungen, keine Protokolle** | Die höchste Wohlfahrt und die beste neidfreie Verteilung setzen voraus, dass jemand alle Bewertungen kennt und rechnet. | – |
| **Modell, kein Befund über Hallenplanung** | Die Zahlen sagen, was die Rechnung für erzeugte oder eingegebene Bewertungen liefert, nicht, wie Vereine tatsächlich teilen sollten. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Bewertung.** Der Kuchen ist $[0, m]$ mit $m = 12$ Stunden. Team $i$ hat die Dichte $v_{ij} = w_{ij} / \sum_j w_{ij}$ auf der Stunde $j$; der Wert eines Stücks $S$ ist $V_i(S) = \int_S v_i$, $V_i([0,m]) = 1$.

**Eigenschaften.** Eine Verteilung $(S_1, \dots, S_n)$ ist *proportional*, wenn $V_i(S_i) \ge 1/n$; *neidfrei*, wenn $V_i(S_i) \ge V_i(S_k)$ für alle $i, k$; *Pareto-effizient*, wenn es keine Verteilung gibt, in der alle mindestens so gut und ein Team besser dasteht.

**Lineares Programm.** Da innerhalb einer Stunde alles gleich viel wert ist, genügen die Anteile $x_{ij} \in [0,1]$ der Stunde $j$ für Team $i$ ($\sum_i x_{ij} = 1$):
$$ \max \sum_{i,j} v_{ij}\, x_{ij} \quad \text{unter} \quad \sum_j v_{ij} x_{ij} \ge \sum_j v_{ij} x_{kj} \;\; (\text{neidfrei}), \qquad \sum_j v_{ij} x_{ij} \ge u_i \;\; (\text{nicht schlechter}). $$
Die höchste Wohlfahrt ist $\sum_j \max_i v_{ij}$ (jede Stunde an das Team mit der höchsten Dichte). Der **Preis der Neidfreiheit** ist $1 - \text{beste neidfreie Wohlfahrt} / \text{höchste Wohlfahrt}$.

**Geteilt und gewählt:** Team 1 wählt $x$ mit $V_1([0,x]) = 1/2$. **Bewegliches Messer:** Team $i$ ruft beim kleinsten $x$ mit $V_i([a, x]) = 1/n$. Beide Schnittpunkte liegen in einer Stunde mit Dichte $> 0$ und lösen eine lineare Gleichung (exakt).

**Literatur** (aus dem Gedächtnis, nicht im Original geprüft): Steinhaus (1948) zur Proportionalität, Dubins und Spanier (1961) zum beweglichen Messer, Selfridge und Conway (um 1960) zur Neidfreiheit bei drei Personen, Aziz und Mackenzie (FOCS 2016) zum neidfreien Protokoll für beliebig viele Personen, Caragiannis u. a. (2012) zum Preis der Fairness.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
