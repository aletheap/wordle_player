#!/usr/bin/env python3
# coding: utf-8

# Wordle Player
# Plays every possible game of Wordle and prints stats on the progress and results
# Inspired by: https://bert.org/2021/11/24/the-best-starting-word-in-wordle/
# Wordle: https://www.powerlanguage.co.uk/wordle/

import datetime
import json
import math
import multiprocessing as mp
import os
import re
import time
from collections import Counter

import fire
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.colors import ListedColormap
from tqdm import tqdm

MY_DIR = os.path.dirname(os.path.realpath(__file__))


class WordlePlayer:
    black = 1
    yellow = 2
    green = 3
    # green = "🟩"
    # yellow = "🟨"
    # black = "⬛"
    first_wordle_date = datetime.date(2021, 6, 19)

    def __init__(self, solutions, word_freqs, wordle_number=None, wordlen=5):
        if wordle_number is None:
            wordle_number = (datetime.date.today() - self.first_wordle_date).days
        self.wordle_number = wordle_number
        self.wordle_date = self.first_wordle_date + datetime.timedelta(days=wordle_number)
        self.solutions = solutions
        self.word_freqs = word_freqs
        self.wordlen = wordlen

        self._solution = self.solutions[wordle_number]
        self.won_game = False
        self.guesses = []
        self.all_results = []
        self.color_lines = []
        self.num_guesses = 0

        self.in_word = set([])
        self.chars = []
        for _ in range(wordlen):
            self.chars.append({"no": set([]), "yes": None})

        self._update()

    def _update(self):
        self.regexes = self._update_regexes()
        self.filtered_words = self._filter_words()
        self.letter_scores = self._score_letters()
        self.word_scores = self._score_words()

    def _re_str_for_pos(self, pos):
        if self.chars[pos]["yes"]:
            return self.chars[pos]["yes"]
        elif self.chars[pos]["no"]:
            return "[^" + "".join(sorted(list(self.chars[pos]["no"]))) + "]"
        else:
            return "."

    def _update_regexes(self):
        regexes = []
        main_regex_split = [self._re_str_for_pos(i) for i in range(self.wordlen)]
        main_regex = "^" + "".join(main_regex_split) + "$"
        for letter in self.in_word:
            regexes.append(re.compile(f"^.*{letter}"))
        return [re.compile(main_regex)] + [re.compile(r) for r in regexes]

    def _matches_all_regexes(self, word):
        for r in self.regexes:
            if not r.match(word):
                return False
        return True

    def _filter_words(self):
        return [w for w in self.word_freqs if self._matches_all_regexes(w)]

    def _score_letters(self):
        letter_counter = Counter([(i, l) for w in self.filtered_words for i, l in enumerate(w)])
        letter_scores = dict(letter_counter)
        M = max(letter_scores.values())
        letter_scores = {k: v / M for k, v in letter_scores.items()}
        return letter_scores

    def _score_one_word(self, word):
        avg_letter_score = sum([self.letter_scores[x] for x in enumerate(word)]) / self.wordlen
        unique_letters = len(set(word))
        return (avg_letter_score * unique_letters) + self.word_freqs[word]

    def _score_words(self):
        return list(reversed(sorted([(self._score_one_word(w), w) for w in self.filtered_words])))

    def wrong_position(self, letter, position):
        letter = letter.lower()
        self.chars[position]["no"].add(letter)
        self.in_word.add(letter)

    def correct(self, letter, position):
        letter = letter.lower()
        self.chars[position]["yes"] = letter

    def not_in_word(self, letter, position=None):
        letter = letter.lower()
        for position in range(self.wordlen):
            self.chars[position]["no"].add(letter)

    def add_result(self, word, result):
        # color_line = ""
        color_line = []
        for i, r in enumerate(result):
            f = {"G": self.correct, "Y": self.wrong_position, "B": self.not_in_word}[r]
            f(word[i], i)
            color_line.append({"G": self.green, "Y": self.yellow, "B": self.black}[r])

        # color_line += " " * blacks
        self.color_lines.append(color_line)
        if result == "".join(["G"] * len(word)):
            self.won_game = True

    def next_word(self):
        self._update()
        if len(self.word_scores) > 0:
            return self.word_scores[0][1]
        else:
            return None

    def get_color_grid(self):
        return self.color_lines

    def guess(self, word):
        result = []
        for i, letter in enumerate(word):
            if self._solution[i] == letter:
                result.append("G")
            elif letter in self._solution:
                result.append("Y")
            else:
                result.append("B")
        result = "".join(result)
        self.add_result(word, result)
        self.num_guesses += 1
        return result

    def play(self):
        for trie in range(1, 7):
            next_word = self.next_word()
            if next_word is None:
                break
            self.guess(next_word)
            output = {
                "won": self.won_game,
                "guesses": trie,
                "color_grid": self.get_color_grid(),
                "wordle_number": self.wordle_number,
            }
            if output["won"]:
                break
        output["time"] = time.time()
        return output

    # def play_interactive(self):
    #    input_re = re.compile("^" + ("[cpn]") * self.wordlen + "$")
    #    while not self.won_game:
    #        word = self.next_word()
    #        print(f'\n{"="*20}\nTry: "{word.upper()}"\n{"="*20}', flush=True)
    #        word_result = ""
    #        while not input_re.match(word_result):
    #            print(f"\nType one for each letter of {word.upper()}:")
    #            print("'c' = correct position")
    #            print("'p' = correct letter in wrong position")
    #            print("'n' = letter not in word")
    #            word_result = input("(for example 'nccpn'): ")
    #        self.add_result(word, word_result)
    #    print("\n\nCongratulations! You won!\n")
    #    print(self.get_color_grid())


def play_game(wordle_number, solutions, word_freqs, results_q):
    output = WordlePlayer(solutions, word_freqs, wordle_number=wordle_number).play()
    results_q.put(output)
    return output


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
    ax.set_xticks(range(0, total_games + 1, total_games // 10))
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


def save_stats(results, output_file="wordle_stats.png"):
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
    output_file="wordle_grids.png",
    aspect_ratio=1.6,
    mobile_friendly=False,
):
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




def main(
    num_games=None,
    num_threads=None,
    output_file="wordle_grids.png",
    stats_file="wordle_stats.png",
    max_vocab_size=100_000,
    debug=False,
    mobile_friendly=False,
    save_grids=False,
):

    word_freqs, solutions, all_playable_words = load_data_files(max_vocab_size=max_vocab_size)

    num_games = num_games or len(solutions)

    if debug:
        with open(os.path.join(MY_DIR, "results.json")) as f:
            results = json.load(f)
        # with open(os.path.join(MY_DIR, "progress_tracker.json")) as f:
        #    progress_tracker = json.load(f)
    else:
        t0 = time.time()
        m = mp.Manager()
        q = m.Queue()

        # if debug:
        #    play_game(1, solutions, word_freqs, q)
        #    return

        with mp.Pool(num_threads) as p:
            r = [p.apply_async(play_game, (i, solutions, word_freqs, q)) for i in range(num_games)]
            finished = 0
            # progress_tracker = []
            with tqdm(total=num_games, unit="game(s)") as pb:
                while finished < num_games:
                    new_finished = len([1 for x in r if x.ready()])
                    # progress_tracker.append((time.time() - t0, new_finished))
                    pb.update(new_finished - finished)
                    finished = new_finished
            # progress_tracker.append((time.time() - t0, num_games))
            # results = []
            # for x in r:
            #    results.append(x.get())
            results = [x.get() for x in r]
            with open(os.path.join(MY_DIR, "results.json"), "w") as f:
                json.dump(results, f)
            # with open(os.path.join(MY_DIR, "progress_tracker.json"), "w") as f:
            #    json.dump(progress_tracker, f)

    save_stats(results, stats_file)
    if save_grids:
        save_results(results, output_file, mobile_friendly=mobile_friendly)


if __name__ == "__main__":
    fire.Fire(main)
