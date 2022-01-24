#!/usr/bin/env python3
# coding: utf-8

# Wordle Player
# Plays every possible game of Wordle and prints stats on the progress and results
# Inspired by: https://bert.org/2021/11/24/the-best-starting-word-in-wordle/
# Wordle: https://www.powerlanguage.co.uk/wordle/

import json
import math
import multiprocessing as mp
import os
import re
import string
import sys
import time
from collections import Counter

import fire
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.colors import ListedColormap
from tqdm import tqdm


class WordlePlayer:
    black = 1
    yellow = 2
    green = 3
    # green = "🟩"
    # yellow = "🟨"
    # black = "⬛"

    def __init__(self, wordle_number, solutions, word_freqs, wordlen=5):
        self.wordle_number = wordle_number
        self.solutions = solutions
        self.word_freqs = self._process_word_freqs(word_freqs)
        self.wordlen = wordlen

        self._solution = self.solutions[wordle_number]
        self.won_game = False
        self.guesses = []
        self.all_results = []
        self.color_lines = []

        self.in_word = set([])
        self.chars = []
        for _ in range(wordlen):
            self.chars.append({"no": set([]), "yes": None})

        self._update()

    def _process_word_freqs(self, word_freqs):
        # normalize the frequencies
        total = sum([w[1] for w in word_freqs.items()])
        return {w[0]: w[1] / total for w in word_freqs.items()}

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
        letter_scores = {}
        for letter in string.ascii_lowercase:
            for pos in range(self.wordlen):
                score = len([w for w in self.filtered_words if w[pos] == letter])
                freq_score = sum(
                    [self.word_freqs[w] for w in self.filtered_words if w[pos] == letter]
                )
                letter_scores[(pos, letter)] = score * freq_score
        return letter_scores

    def _score_one_word(self, word):
        score = 0
        for i, letter in enumerate(word):
            score += self.letter_scores[(i, letter)]
        score = score / len(word)
        score = score - (5 - len(set(word)))
        uniq_chars = len(set([c for c in word]))
        uniq_score = uniq_chars / len(word)
        score = score * uniq_score
        return score

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
            f = {"c": self.correct, "p": self.wrong_position, "n": self.not_in_word}[r]
            f(word[i], i)
            color_line.append({"c": self.green, "p": self.yellow, "n": self.black}[r])

        # color_line += " " * blacks
        self.color_lines.append(color_line)
        if result == "".join(["c"] * len(word)):
            self.won_game = True

    def next_word(self):
        self._update()
        if len(self.word_scores) > 0:
            return self.word_scores[0][1]
        else:
            return None

    def get_color_grid(self):
        # text = "Wordle {} {}/6\n\n".format(self.wordle_number, len(self.color_lines))
        # text += "\n".join(self.color_lines)
        # text += "\n"
        # return text
        return self.color_lines

    def guess(self, word):
        s = self._solution
        result = []
        for i, letter in enumerate(word):
            if s[i] == letter:
                result.append("c")
            elif letter in s:
                result.append("p")
            else:
                result.append("n")
        result = "".join(result)
        self.add_result(word, result)
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
    output = WordlePlayer(wordle_number, solutions, word_freqs).play()
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
    ax.set_title("Average: {:.1f} guesses per game".format(avg_guesses))
    ax.invert_yaxis()


def draw_games_per_sec(ax, progress_tracker):

    x = [0]
    y = [0]
    prev_secs = 0
    prev_total = 0
    for secs, total in progress_tracker:
        if (total > prev_total) and (secs - prev_secs >= 1):
            x.append(secs)
            y.append((total - prev_total) / (secs - prev_secs))
            prev_secs = secs
            prev_total = total
    # x = [p[0] for p in progress_tracker]
    # y = [p[1] for p in progress_tracker]
    total_games = progress_tracker[-1][1]
    total_seconds = progress_tracker[-1][0]
    speed = total_games / total_seconds

    ax.plot(x, y, color="black")
    # ax.set_yticks(range(1, 7))
    # ax.set_ylim(0, 7)
    ax.set_xlim(0, x[-1])
    # ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))

    # avg_guesses = sum(x) / len(x)
    ax.set_title(
        f"Played {total_games} games in {total_seconds:.1f} seconds ({speed:.1f} games/sec)"
    )
    ax.set_xlabel("seconds")
    ax.set_ylabel("games / sec")


def draw_wins_losses(ax, results):
    total_games = len(results)
    x = np.array([float(r["won"]) for r in results])
    # x_ticks = np.where(x == 0)[0]
    # print(f"{x_ticks=}")
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
    ax.set_title(f"Won {wins:.0f} of {total_games:.0f} games ({win_pct:.1f}%)")
    ax.set_yticks([])
    ax.set_xticks(range(0, total_games + 1, total_games // 10))
    # ax.set_xticks(x_ticks)
    # ax.set_xticklabels([])
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=total_games))
    ax.set_xlim(0, total_games)
    ax.xaxis.set_ticks_position("bottom")


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


def save_stats(results, progress_tracker, output_file="wordle_stats.png"):
    print(f"Saving stats to {output_file}", flush=True)

    grid_h = 3
    grid_w = 3
    fig = plt.figure(figsize=(grid_w * 2, grid_h * 2))
    grid = plt.GridSpec(grid_h, grid_w)  # , wspace=0.4, hspace=0.3)

    # wins, losses
    ax = fig.add_subplot(grid[0, :grid_w])
    draw_wins_losses(ax, results)

    # add histogram of tries
    ax = fig.add_subplot(grid[1, :grid_w])
    draw_guesses_hist(ax, results)

    # draw games per second
    ax = fig.add_subplot(grid[2, :grid_w])
    draw_games_per_sec(ax, progress_tracker)

    fig.suptitle("Wordle Player Stats")
    plt.tight_layout()
    fig.savefig(output_file)
    print(f"Saved stats to {output_file}", flush=True)


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
):

    # Load all Wordle words. Source: "https://bert.org/assets/posts/wordle/words.json"
    dir_path = os.path.dirname(os.path.realpath(__file__))

    data_file = os.path.join(dir_path, "words.json")
    with open(data_file, "r") as f:
        data = json.load(f)
    solutions = data["solutions"]
    herrings = set(data["herrings"])
    all_valid_words = set(solutions) | herrings

    with open(os.path.join(dir_path, "word_freqs.json"), "r") as f:
        word_freqs = json.load(f)

    word_freqs = sorted(word_freqs.items(), key=lambda x: x[1], reverse=True)

    # wordle will not allow words other than solutions or herrings so we should
    # enforce the same behavior:
    word_freqs = {k: v for k, v in word_freqs[:max_vocab_size] if k in all_valid_words}

    print(f"{len(word_freqs)=}")
    print(f"{len(solutions)=}")
    print(f"{len(herrings)=}")
    print(f"{len(all_valid_words)=}")
    print(f"{len(all_valid_words - set(word_freqs.keys()))=}")
    print(f"{len(set(solutions) - set(word_freqs.keys()))=}")
    # print(f"{solutions - set(word_freqs.keys())=}")
    # assert len(all_valid_words) == len(
    #    set(word_freqs.keys()) & all_valid_words
    # ), "Some words are not in the word list"

    num_games = num_games or len(solutions)

    if debug:
        with open(os.path.join(dir_path, "results.json")) as f:
            results = json.load(f)
        with open(os.path.join(dir_path, "progress_tracker.json")) as f:
            progress_tracker = json.load(f)
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
            progress_tracker = []
            with tqdm(total=num_games, unit="game(s)") as pb:
                while finished < num_games:
                    new_finished = len([1 for x in r if x.ready()])
                    progress_tracker.append((time.time() - t0, new_finished))
                    pb.update(new_finished - finished)
                    finished = new_finished
            progress_tracker.append((time.time() - t0, num_games))
            # results = []
            # for x in r:
            #    results.append(x.get())
            results = [x.get() for x in r]
            with open(os.path.join(dir_path, "results.json"), "w") as f:
                json.dump(results, f)
            with open(os.path.join(dir_path, "progress_tracker.json"), "w") as f:
                json.dump(progress_tracker, f)

    save_stats(results, progress_tracker, stats_file)
    save_results(results, output_file, mobile_friendly=mobile_friendly)
    # with open(output_file, "w") as f:
    #    f.write(format_results(results, num_seconds))
    # sys.stderr.flush()


if __name__ == "__main__":
    fire.Fire(main)
