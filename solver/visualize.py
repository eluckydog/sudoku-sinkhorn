"""
visualize.py - Visualization for Sudoku Field results

Outputs:
  1. Energy/temperature convergence curves
  2. Engine-puzzle heatmaps
  3. Sinkhorn phase diagram (T vs entropy)
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from solver.board import PUZZLE_COLLECTION
from solver.field_compare import SudokuField


def plot_convergence(field: SudokuField, puzzle_name: str, save_path: str = None):
    """Plot convergence curves for all engines on one puzzle"""
    if puzzle_name not in field.results:
        print(f"  [viz] No data for '{puzzle_name}'")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    results = field.results[puzzle_name]
    colors = {"sinkhorn": "#e74c3c", "ga": "#3498db",
              "sa": "#2ecc71", "gradient": "#f39c12",
              "bp": "#9b59b6"}

    # Left: energy/fitness convergence
    ax = axes[0]
    for eng_name, res in results.items():
        if not res.history:
            continue
        h = res.history
        color = colors.get(eng_name, "#999")
        status = "OK" if res.solved else "FAIL"

        if "energy" in h and h["energy"]:
            ax.plot(h["energy"], color=color, label=f"{eng_name} {status}", alpha=0.8)
        elif "best_fitness" in h and h["best_fitness"]:
            ax.plot(h["best_fitness"], color=color, label=f"{eng_name} {status}", alpha=0.8, ls="--")
        elif "violation" in h and h["violation"]:
            ax.plot(h["violation"], color=color, label=f"{eng_name} {status}", alpha=0.8, ls=":")
        elif "max_diff" in h and h["max_diff"]:
            ax.plot(h["max_diff"], color=color, label=f"{eng_name} {status}", alpha=0.8, ls="-.")

    ax.set_xlabel("Iteration (sampled)")
    ax.set_ylabel("Energy / Violation / Fitness")
    ax.set_title(f"Convergence: {puzzle_name}")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Right: Sinkhorn thermodynamics
    ax = axes[1]
    if "sinkhorn" in results:
        h = results["sinkhorn"].history
        if "T" in h and "entropy" in h:
            ax_twin = ax.twinx()
            ax.plot(h["entropy"], color=colors["sinkhorn"], label="Sinkhorn entropy", linewidth=2)
            ax_twin.plot(h["T"], color=colors["sinkhorn"], ls="--", alpha=0.5,
                        label="Temperature T")
            ax.set_xlabel("Iteration")
            ax.set_ylabel("Entropy", color=colors["sinkhorn"])
            ax_twin.set_ylabel("Temperature T")
            ax_twin.legend(fontsize=8, loc="upper right")
            ax.legend(fontsize=8, loc="upper left")
            ax.set_title("Sinkhorn thermodynamic trajectory")
            ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  [viz] Saved: {save_path}")
    plt.close()


def plot_engine_heatmap(field: SudokuField, save_path: str = None):
    """Plot engine-puzzle success rate and time heatmaps"""
    puzzles = list(field.results.keys())
    engines = list(field.engines.keys())

    data = np.zeros((len(puzzles), len(engines)))
    times = np.zeros((len(puzzles), len(engines)))

    for i, p in enumerate(puzzles):
        for j, e in enumerate(engines):
            if e in field.results[p]:
                r = field.results[p][e]
                data[i, j] = 1.0 if r.solved else 0.0
                times[i, j] = r.time_seconds if r.solved else 0.0

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Success rate
    im1 = ax1.imshow(data, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax1.set_xticks(range(len(engines)))
    ax1.set_xticklabels(engines, rotation=45)
    ax1.set_yticks(range(len(puzzles)))
    ax1.set_yticklabels(puzzles)
    ax1.set_title("Success rate (green=solved)")
    for i in range(len(puzzles)):
        for j in range(len(engines)):
            ax1.text(j, i, "OK" if data[i, j] else "XX",
                    ha="center", va="center", fontsize=12, fontweight="bold")
    plt.colorbar(im1, ax=ax1, shrink=0.8)

    # Solve time
    if times.max() > 0:
        im2 = ax2.imshow(times, cmap="YlOrRd", aspect="auto")
        ax2.set_xticks(range(len(engines)))
        ax2.set_xticklabels(engines, rotation=45)
        ax2.set_yticks(range(len(puzzles)))
        ax2.set_yticklabels(puzzles)
        ax2.set_title("Solve time (seconds)")
        for i in range(len(puzzles)):
            for j in range(len(engines)):
                val = f"{times[i, j]:.2f}" if times[i, j] > 0 else "-"
                ax2.text(j, i, val, ha="center", va="center", fontsize=9)
        plt.colorbar(im2, ax=ax2, shrink=0.8)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  [viz] Saved: {save_path}")
    plt.close()


def plot_phase_diagram(field: SudokuField, save_path: str = None):
    """Sinkhorn phase diagram: temperature vs entropy curves"""
    fig, ax = plt.subplots(figsize=(8, 5))

    colors = {"minimal": "#3498db", "medium": "#2ecc71",
              "hard": "#e74c3c", "ai_escargot": "#9b59b6"}

    for pname in field.results:
        if "sinkhorn" not in field.results[pname]:
            continue
        h = field.results[pname]["sinkhorn"].history
        if "T" in h and "entropy" in h and len(h["T"]) > 2:
            T = np.array(h["T"])
            ent = np.array(h["entropy"])
            ax.plot(T, ent, "o-", color=colors.get(pname, "#999"),
                   label=f"{pname}", markersize=4, alpha=0.8)

            # Mark phase transition
            d_ent = np.diff(ent)
            if len(d_ent) > 0:
                phase_idx = np.argmin(d_ent)
                if phase_idx < len(T):
                    ax.axvline(T[phase_idx], color=colors.get(pname, "#999"),
                              ls="--", alpha=0.3)
                    ax.annotate(f"T_c={T[phase_idx]:.2f}",
                               xy=(T[phase_idx], ent[phase_idx]),
                               xytext=(T[phase_idx] * 1.2, ent[phase_idx] + 0.05),
                               fontsize=8, color=colors.get(pname, "#999"))

    ax.set_xlabel("Temperature T")
    ax.set_ylabel("Average Entropy")
    ax.set_title("Sinkhorn Phase Diagram: Entropy vs Temperature")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.invert_xaxis()

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  [viz] Saved: {save_path}")
    plt.close()
