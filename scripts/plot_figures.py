#!/usr/bin/env python3
"""Render the exact rational phase example, retaining half-open jump endpoints."""
from pathlib import Path
import argparse
import csv
import shutil
from fractions import Fraction as F
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt, font_manager
from matplotlib.ticker import NullLocator

ROOT = Path(__file__).resolve().parents[1]


def configure_fonts():
    files = [ROOT / "fonts" / name for name in
             ("LinLibertine_Rah.ttf", "LinLibertine_RIah.ttf")]
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(f"Packaged Libertine font missing: {path}")
        font_manager.fontManager.addfont(str(path))
    family = font_manager.FontProperties(fname=str(files[0])).get_name()
    plt.rcParams.update({"font.family": family, "font.size": 8.9664,
                         "mathtext.fontset": "custom", "mathtext.rm": family,
                         "mathtext.it": family + ":style=italic",
                         "mathtext.bf": family, "mathtext.fallback": None,
                         "text.usetex": False, "pdf.fonttype": 42,
                         "ps.fonttype": 42, "pdf.use14corefonts": False,
                         "axes.linewidth": .4, "xtick.major.width": .4,
                         "ytick.major.width": .4, "xtick.major.size": 2,
                         "ytick.major.size": 2, "axes.unicode_minus": True})
    print("Font:", family)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "figures")
    parser.add_argument("--paper-dir", type=Path, default=ROOT.parent / "paper" / "figures")
    args = parser.parse_args()
    with (ROOT / "results/paper/phase.csv").open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    configure_fonts()
    fig = plt.figure(figsize=(357.8035 / 72, 123.3153 / 72))
    ax = fig.add_axes([40.8 / 357.8035, 26.6 / 123.3153,
                       315.0 / 357.8035, 94.6 / 123.3153])
    for bound in (F(-3, 8), F(3, 8)):
        ax.plot([0, 1], [float(bound)]*2, color="black", linewidth=.4, dashes=(4, 4))
    for bound in (F(-1, 4), F(1, 4)):
        ax.plot([0, 1], [float(bound)]*2, color=".5", linewidth=.4, dashes=(1, 4))
    actual, excluded = [], []
    for row in rows:
        a, b, value, limit = [F(row[k]) for k in ("left", "right", "left_value", "right_limit")]
        # Exact endpoint values and slopes are read from the existing scientific export.
        assert limit == value - (b-a)
        ax.plot([float(a), float(b)], [float(value), float(limit)], color="black", linewidth=.8)
        actual.append((float(a), float(value)))
        if row["right_closed"] == "True":
            actual.append((float(b), float(limit)))
        else:
            assert row["right_closed"] == "False"
            excluded.append((float(b), float(limit)))
    assert len(rows) == 4 and len(actual) == 5 and len(excluded) == 3
    ax.plot(*zip(*excluded), linestyle="none", marker="o", markersize=3.4,
            markeredgewidth=.5, markeredgecolor="black", markerfacecolor="white",
            clip_on=False, zorder=4)
    ax.plot(*zip(*actual), linestyle="none", marker="o", markersize=3.0,
            markeredgewidth=.4, color="black", clip_on=False, zorder=5)
    ax.set(xlim=(0, 1), ylim=(-.43, .43), xlabel=r"Shared input $s$", ylabel="Output error")
    ax.set_xticks([0, .25, .5, .75, 1], [r"$0$", r"$1/4$", r"$1/2$", r"$3/4$", r"$1$"])
    ax.set_yticks([-.375, -.25, 0, .25, .375],
                 [r"$-3/8$", r"$-1/4$", r"$0$", r"$1/4$", r"$3/8$"])
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(direction="in", pad=4)
    ax.xaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_minor_locator(NullLocator())
    ax.plot(1, -.43, marker=">", markersize=3, color="black", clip_on=False)
    ax.plot(0, .43, marker="^", markersize=3, color="black", clip_on=False)
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / "phase.pdf"
    fig.savefig(path, metadata={"Creator": None, "Producer": None,
                                "CreationDate": None, "ModDate": None})
    plt.close(fig)
    if args.paper_dir.is_dir():
        shutil.copyfile(path, args.paper_dir / path.name)
    print("Rendered phase: 4 rational segments, 5 actual values, 3 excluded limits")


if __name__ == "__main__":
    main()
