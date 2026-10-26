"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import kuc_constants as C
import kuc_evaluation as ev


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.28), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _hour_axis(fig, title="Uhrzeit"):
    fig.update_xaxes(tickvals=list(range(0, C.CELLS + 1, 2)), ticktext=[ev.clock(x) for x in range(0, C.CELLS + 1, 2)], range=[0, C.CELLS], title_text=title)
    return fig


def build_values(a):
    """Wie wichtig jede Stunde jedem Team ist: Anteil am Gesamtwert des Kuchens je Stunde (Stufen)."""
    fig = go.Figure()
    for i, v in enumerate(a.vals):
        ys = [float(d) for d in v] + [float(v[-1])]
        fig.add_trace(go.Scatter(x=list(range(C.CELLS + 1)), y=ys, mode="lines", name=ev.team(i), line=dict(color=C.TEAM_COLORS[i], width=2.5, shape="hv"),
                                 hovertemplate="ab %{x}: %{y:.1%} des Kuchens je Stunde<extra>" + ev.team(i) + "</extra>"))
    _hour_axis(fig)
    fig.update_yaxes(title_text="Wert je Stunde", tickformat=".0%", rangemode="tozero")
    return _base(fig, height=300)


def build_division(a):
    """Wer bekommt wann die Halle: je Verteilung (Protokoll und Referenzen) eine Zeile, Stücke als farbige Streifen."""
    fig = go.Figure()
    rows = [a.divisions[k] for k in ("protokoll", "wohlfahrt", "neidfrei", "nachgebessert")]
    labels = [d.name for d in rows]
    shown = set()
    for d, label in zip(rows, labels):
        for i, piece in enumerate(d.pieces):
            for (lo, hi) in piece:
                fig.add_trace(go.Bar(
                    y=[label], x=[float(hi - lo)], base=[float(lo)], orientation="h", name=ev.team(i), marker_color=C.TEAM_COLORS[i], showlegend=i not in shown,
                    legendgroup=ev.team(i), hovertemplate=f"{ev.team(i)}: {ev.clock(lo)}–{ev.clock(hi)}<extra>{label}</extra>", marker_line_color="rgba(255,255,255,0.8)", marker_line_width=1))
                shown.add(i)
    fig.update_layout(barmode="overlay")
    _hour_axis(fig)
    fig.update_yaxes(autorange="reversed", title_text="")
    return _base(fig, height=300)


def build_utilities(a):
    """Nutzen je Team in den vier Verteilungen; die gestrichelte Linie ist der gerechte Anteil 1/n (Proportionalität)."""
    fig = go.Figure()
    xs = [ev.team(i) for i in range(a.n)]
    for key in ("protokoll", "wohlfahrt", "neidfrei", "nachgebessert"):
        d = a.divisions[key]
        fig.add_trace(go.Bar(x=xs, y=d.util, name=d.name, hovertemplate="%{x}: %{y:.1%}<extra>" + d.name + "</extra>"))
    fig.add_hline(y=1 / a.n, line_color="rgba(128,128,128,0.8)", line_dash="dash", annotation_text="gerechter Anteil 1/n", annotation_position="top left")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Nutzen (Anteil am Gesamtwert)", tickformat=".0%", rangemode="tozero")
    return _base(fig, height=340)


def build_price_series(rows):
    """Preis der Neidfreiheit: Verlust an Höchstwohlfahrt im Mittel (Säulen) und im schlechtesten Fall (Rauten) je Zahl der Teams und Vorlieben."""
    fig = go.Figure()
    colors = {"unabh": "#4c78a8", "aehnlich": "#e8a838", "gegen": "#2F6B65"}
    for model in C.MODELS:
        sel = [r for r in rows if r["model"] == model]
        fig.add_trace(go.Bar(x=[f"{r['n']} Teams" for r in sel], y=[1 - r["ef_mean"] for r in sel], name=f"{C.MODEL_SHORT[model]}: Mittel", marker_color=colors[model],
                             hovertemplate="%{x}: %{y:.1%} verloren<extra>" + C.MODEL_SHORT[model] + "</extra>"))
        fig.add_trace(go.Scatter(x=[f"{r['n']} Teams" for r in sel], y=[1 - r["ef_min"] for r in sel], mode="markers", name=f"{C.MODEL_SHORT[model]}: schlechtester Fall", showlegend=False,
                                 marker=dict(symbol="diamond", size=9, color=colors[model], line=dict(color="#222", width=1)), hovertemplate="%{x}: %{y:.1%} verloren (schlechtester Fall)<extra>" + C.MODEL_SHORT[model] + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Verlust an Höchstwohlfahrt durch Neidfreiheit", tickformat=".0%", rangemode="tozero")
    fig.update_xaxes(type="category")
    return _base(fig, height=360)


def build_protocol_series(rows):
    """Summe der Nutzen im Verhältnis zur Höchstwohlfahrt je Protokoll und Vorlieben; die Rauten zeigen den Wert nach dem Nachbessern."""
    fig = go.Figure()
    colors = {"unabh": "#4c78a8", "aehnlich": "#e8a838", "gegen": "#2F6B65"}
    cases = list(dict.fromkeys((r["protocol"], r["n"]) for r in rows))
    labels = [f"{C.PROTOCOL_SHORT[p]}, {n}" for p, n in cases]
    for model in C.MODELS:
        sel = {(r["protocol"], r["n"]): r for r in rows if r["model"] == model}
        fig.add_trace(go.Bar(x=labels, y=[sel[c]["ratio_sum"] for c in cases], name=C.MODEL_SHORT[model], marker_color=colors[model], hovertemplate="%{x}: %{y:.1%}<extra>" + C.MODEL_SHORT[model] + "</extra>"))
        fig.add_trace(go.Scatter(x=labels, y=[sel[c]["fixed_sum"] for c in cases], mode="markers", name=f"{C.MODEL_SHORT[model]}: nachgebessert", showlegend=False,
                                 marker=dict(symbol="diamond", size=9, color=colors[model], line=dict(color="#222", width=1)), hovertemplate="%{x}: %{y:.1%} nachgebessert<extra>" + C.MODEL_SHORT[model] + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Summe der Nutzen / Höchstwohlfahrt", tickformat=".0%", range=[0, 1.05])
    fig.update_xaxes(title_text="Protokoll, Zahl der Teams", type="category")
    return _base(fig, height=380)


def build_block_series(rows):
    """Zahl der Blöcke je Team über der Zahl der Teams: Messer (immer 1), höchste Wohlfahrt, beste neidfreie Verteilung."""
    fig = go.Figure()
    for key, name, color in (("messer", "Bewegliches Messer", "#b04a3a"), ("wohlfahrt", "Höchste Wohlfahrt", "#4c78a8"), ("neidfrei", "Neidfrei, beste Wohlfahrt", "#2F6B65")):
        fig.add_trace(go.Scatter(x=[f"{r['n']} Teams" for r in rows], y=[r[key] for r in rows], mode="lines+markers", name=name, line=dict(color=color, width=2.5),
                                 hovertemplate="%{x}: %{y:.2f} Blöcke je Team<extra>" + name + "</extra>"))
    fig.update_yaxes(title_text="Blöcke je Team (Mittel)", rangemode="tozero")
    fig.update_xaxes(type="category")
    return _base(fig, height=320)
