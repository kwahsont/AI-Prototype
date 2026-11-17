"""Draw the system diagram for the report.

Run from the project root:  python src/figures.py
Output: docs/system_diagram.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "system_diagram.png"

INK = "#2c2c2a"
MUTED = "#6b6a63"
ML = "#2a78d6"       # the machine-learning step
OTHER = "#e9e8e2"    # everything that is rules or data

# (x, y, title, detail, is_ml)
BOXES = [
    (1.0, 3.0, "Student survey", "56 answers:\nhow likely to eat there\nin rain, exams, holidays…", False),
    (4.0, 3.0, "Assumptions", "Survey → multipliers\ne.g. rain ×0.70\n(docs/assumptions.md)", False),
    (7.0, 3.0, "Simulation", "250 days of footfall\n+ noise, labelled\nlow / medium / high", False),
    (10.0, 3.0, "Decision tree", "Learns risk from day,\ncalendar, weather,\nclass load", True),
    (13.0, 3.0, "Dashboard", "Advisor · Week planner\nLog a day · Model", False),
]
W, H = 2.4, 1.7


def box(ax, x, y, title, detail, is_ml):
    face = ML if is_ml else OTHER
    text = "white" if is_ml else INK
    ax.add_patch(FancyBboxPatch((x - W / 2, y - H / 2), W, H,
                                boxstyle="round,pad=0.02,rounding_size=0.15",
                                facecolor=face, edgecolor="none"))
    ax.text(x, y + 0.45, title, ha="center", va="center", fontsize=12,
            fontweight="bold", color=text)
    ax.text(x, y - 0.2, detail, ha="center", va="center", fontsize=8.5, color=text,
            linespacing=1.4)


def arrow(ax, start, end, **kw):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14,
                                 color=kw.pop("color", MUTED), linewidth=1.5, **kw))


def main():
    fig, ax = plt.subplots(figsize=(13, 4.6))
    ax.set_xlim(-0.4, 14.4)
    ax.set_ylim(1.05, 4.6)
    ax.axis("off")

    for b in BOXES:
        box(ax, *b)
    for (x1, *_), (x2, *_) in zip(BOXES, BOXES[1:]):
        arrow(ax, (x1 + W / 2 + 0.05, 3.0), (x2 - W / 2 - 0.05, 3.0))

    # Feedback loop: real logged days go back into training.
    arrow(ax, (13.0, 3.0 - H / 2 - 0.05), (10.0, 3.0 - H / 2 - 0.05),
          connectionstyle="arc3,rad=-0.45", linestyle="--")
    ax.text(11.5, 1.25, "Log a day: real leftovers are added to the training data → retrain",
            ha="center", fontsize=9, color=MUTED, style="italic")

    ax.text(10.0, 4.15, "Machine learning", ha="center", fontsize=9, color=ML, fontweight="bold")
    ax.text(4.0, 4.15, "Rules and data we wrote down", ha="center", fontsize=9, color=MUTED)
    ax.set_title("Village 2 cafeteria waste advisor — how the prototype works (SIMULATED data)",
                 fontsize=12, color=INK, pad=6)

    OUTPUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUTPUT, dpi=160, bbox_inches="tight", facecolor="white")
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()
