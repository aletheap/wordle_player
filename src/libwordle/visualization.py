#!/usr/bin/env python3
# coding: utf-8

# Wordle Player
# Plays every possible game of Wordle and prints stats on the progress and results
# Inspired by: https://bert.org/2021/11/24/the-best-starting-word-in-wordle/
# Wordle: https://www.powerlanguage.co.uk/wordle/

import math
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.colors import ListedColormap


def draw_guesses_hist(ax, results):
    x = [r["guesses"] for r in results]

    ax.hist(
        x,
        orientation="horizontal",
        bins=range(0, 8),
        rwidth=0.9,
        # density=True,
        align="left",
        color="black",
    )
    ax.set_yticks(range(1, 7))
    ax.set_ylim(0, 7)
    ax.set_ylabel("guesses")
    ax.set_xlabel("games")
    # ax.set_xlim(0, len(x))
    # ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))

    avg_guesses = sum(x) / len(x)
    title = "Average: {:.1f} guesses per game".format(avg_guesses)
    ax.set_title(title)
    ax.invert_yaxis()
    return title


def draw_games_per_sec(ax, results, bucket_size=1):
    times = np.array(sorted([x["time"] for x in results]))
    times = times - times[0]
    times2 = np.expand_dims(times, 0)
    time_deltas = times2 - times2.T
    rates = (time_deltas <= bucket_size) * (time_deltas > 0)
    rates = rates.sum(0)

    total_games = len(results)
    total_seconds = times[-1]
    speed = total_games / total_seconds

    x = times
    y = rates

    ax.plot(x, y, color="black")
    ax.set_xlim(0, x[-1])

    title = f"Played {total_games} games in {total_seconds:.1f} seconds ({speed:.1f} games/sec)"
    ax.set_title(title)
    ax.set_xlabel("seconds")
    ax.set_ylabel("games / sec")
    return title


def draw_wins_losses(ax, results):
    total_games = len(results)
    x = np.array([float(r["won"]) for r in results])
    wins = x.sum()
    losses = (1 - x).sum()
    win_pct = x.mean() * 100
    loss_pct = (1 - x).mean() * 100
    cmap = ListedColormap(["red", "limegreen"])

    ax.barh([1], [wins], label="Wins", color="limegreen")
    ax.barh([1], [losses], left=wins, label="Losses", color="red")
    # ax.matshow(np.expand_dims(x, 0), cmap=cmap, aspect="auto")
    ax.set_ylabel("win / loss")
    ax.set_xlabel("games")
    title = f"Won {wins:.0f} of {total_games:.0f} games ({win_pct:.1f}%)"
    ax.set_title(title)
    ax.set_yticks([])
    ax.set_xticks(range(0, total_games + 1, total_games // 10 if total_games > 10 else 1))
    # ax.set_xticks(x_ticks)
    # ax.set_xticklabels([])
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=total_games))
    ax.set_xlim(0, total_games)
    ax.xaxis.set_ticks_position("bottom")
    return title


def drawgame(ax, wordle_number, mat):
    cmap = ListedColormap(["black", "gold", "limegreen"])
    vmin = 1
    vmax = 3
    tries = len(mat)
    title = f"Wordle {wordle_number} {tries}/6"
    if min(mat[-1]) == 3:
        title_color = "black"
    else:
        title_color = "red"

    ax.matshow(mat, vmin=vmin, vmax=vmax, cmap=cmap)
    ax.set_title(f"Wordle {wordle_number} {tries}/6", color=title_color)
    ax.tick_params(axis="x", colors="w")
    ax.tick_params(axis="y", colors="w")
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")

    ax.set_xticks(np.arange(-0.5, 5, 1), colors="w")
    ax.set_yticks(np.arange(-0.5, 6, 1), colors="w")
    ax.grid(color="white", linestyle="-", linewidth=2)
    # ax.axis(colors='w')


def save_stats(results, output_dir="."):
    output_file = os.path.join(output_dir, "wordle_stats.png")

    print(f"Saving stats to {output_file}", flush=True)

    grid_h = 3
    grid_w = 3
    fig = plt.figure(figsize=(grid_w * 2, grid_h * 2))
    grid = plt.GridSpec(grid_h, grid_w)  # , wspace=0.4, hspace=0.3)

    # wins, losses
    ax = fig.add_subplot(grid[0, :grid_w])
    wins_str = draw_wins_losses(ax, results)

    # add histogram of tries
    ax = fig.add_subplot(grid[1, :grid_w])
    guesses_str = draw_guesses_hist(ax, results)

    # draw games per second
    ax = fig.add_subplot(grid[2, :grid_w])
    speed_str = draw_games_per_sec(ax, results)

    fig.suptitle("Wordle Player Stats")
    plt.tight_layout()
    fig.savefig(output_file)
    print(f"Saved stats to {output_file}", flush=True)

    print(wins_str)
    print(guesses_str)
    print(speed_str)


def save_results(
    results,
    output_dir=".",
    aspect_ratio=1.6,
    mobile_friendly=False,
):
    output_file = os.path.join(output_dir, "wordle_grids.png")
    print(f"Saving grids to {output_file}", flush=True)

    results = sorted(results, key=lambda x: x["wordle_number"])

    total_games = len(results)
    width = math.ceil(math.sqrt(total_games * aspect_ratio))
    if mobile_friendly:
        width = 16
    height = math.ceil(total_games / width)
    print(f"{height=}", flush=True)
    print(f"{width=}", flush=True)

    fig = plt.figure(figsize=(width * 2, height * 2))
    grid = plt.GridSpec(height, width)  # , wspace=0.4, hspace=0.3)

    for i, r in enumerate(results):
        # print(f"{i=}", flush=True)
        grid_x = i % width
        grid_y = i // width
        # print(f"grid_args = ({grid_y}, {grid_x})", flush=True)
        ax = fig.add_subplot(grid[grid_y, grid_x])
        drawgame(ax, r["wordle_number"], r["color_grid"])
    plt.tight_layout()
    fig.savefig(output_file)
    plt.close()
    print(f"Saved grids to {output_file}", flush=True)
