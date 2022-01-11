#!/usr/bin/env python3
# coding: utf-8

# Wordle Player
# Plays every possible game of Wordle and prints stats on the progress and results
# Inspired by: https://bert.org/2021/11/24/the-best-starting-word-in-wordle/
# Wordle: https://www.powerlanguage.co.uk/wordle/

import json
import multiprocessing as mp
import os
import re
import string
import sys
import time
import urllib.request
from collections import Counter

import fire
from tqdm import tqdm

DATA_URL = "https://bert.org/assets/posts/wordle/words.json"


class WordlePlayer:
    green = "🟩"
    black = "⬛"
    yellow = "🟨"

    def __init__(self, wordle_number, solutions, all_valid_words, wordlen=5):
        self.wordle_number = wordle_number
        self.solutions = solutions
        self.all_valid_words = all_valid_words
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
        return [w for w in self.all_valid_words if self._matches_all_regexes(w)]

    def _score_letters(self):
        letter_scores = {}
        for letter in string.ascii_lowercase:
            for pos in range(self.wordlen):
                score = len([w for w in self.filtered_words if w[pos] == letter])
                letter_scores[(pos, letter)] = score
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
        color_line = ""
        for i, r in enumerate(result):
            f = {"c": self.correct, "p": self.wrong_position, "n": self.not_in_word}[r]
            f(word[i], i)
            color_line += {"c": self.green, "p": self.yellow, "n": self.black}[r]

        self.color_lines.append(color_line)
        if result == "".join(["c"] * len(word)):
            self.won_game = True

    def next_word(self):
        self._update()
        return self.word_scores[0][1]

    def get_color_grid(self):
        text = "Wordle {} {}/6\n\n".format(self.wordle_number, len(self.color_lines))
        text += "\n".join(self.color_lines)
        text += "\n"
        return text

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
            self.guess(self.next_word())
            output = {
                "won": self.won_game,
                "guesses": trie,
                "color_grid": self.get_color_grid(),
            }
            if output["won"]:
                break
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


def play_game(wordle_number, solutions, all_valid_words, results_q):
    output = WordlePlayer(wordle_number, solutions, all_valid_words).play()
    results_q.put(output)
    return output


def make_hist(scores, hist_width=20):
    scores = {k: v for k, v in scores}
    max_guesses = max(scores.keys())
    max_games = max(scores.values())
    total_games = sum(scores.values())
    scaled_scores = {k: round(hist_width * v / max_games) for k, v in scores.items()}
    pct_scores = {k: 100 * v / total_games for k, v in scores.items()}
    hist_lines = []
    for i in range(1, max_guesses + 1):
        pct = f"({pct_scores.get(i, 0):.1f}%)".rjust(7, " ")
        hist_lines.append(f"{i:2} {pct} | " + "*" * scaled_scores.get(i, 0))
    return "\n".join(hist_lines)


def main(num_games=None, num_threads=None, output_file="wordle_results.txt"):
    if not os.path.exists("words.json"):
        print("Downloading words.json...")
        urllib.request.urlretrieve(DATA_URL, "words.json")

    with open("words.json", "r") as f:
        data = json.load(f)

    solutions = data["solutions"]
    all_valid_words = sorted(list(set(solutions) | set(data["herrings"])))
    num_games = num_games or len(solutions)

    t0 = time.time()
    m = mp.Manager()
    q = m.Queue()
    with mp.Pool(num_threads) as p:
        r = [p.apply_async(play_game, (i, solutions, all_valid_words, q)) for i in range(num_games)]
        finished = 0
        with tqdm(total=num_games, unit="game(s)") as pb:
            while finished < len(r):
                new_finished = len([1 for x in r if x.ready()])
                pb.update(new_finished - finished)
                finished = new_finished
        results = [x.get() for x in r]
    t1 = time.time()
    num_seconds = t1 - t0

    total_games = len(results)
    total_wins = len([r for r in results if r["won"]])
    avg_guesses = sum([r["guesses"] for r in results]) / total_games
    pct_wins = 100 * (total_wins / total_games)
    pct_losses = 100 - pct_wins

    with open(output_file, "w") as f:
        f.write("Wordle Game Stats:\n")
        f.write("\n")
        f.write(f"Played: {num_games} games\n")
        f.write(f"Time:   {num_seconds:.1f} seconds\n")
        f.write(f"Speed:  {num_games / num_seconds:.1f} games/s\n")
        f.write(f"Wins:   {total_wins} ({pct_wins:.1f}%)\n")
        f.write(f"Losses: {total_games - total_wins} ({pct_losses:.1f}%)\n")
        f.write("\n")
        f.write(f"Avg Guesses: {avg_guesses:.01f} / game\n")
        scores = Counter([r["guesses"] for r in results])
        f.write(make_hist(scores.most_common()) + "\n")
        f.write("\n\n\n")
        color_grids = [x["color_grid"] for x in results]
        for c in color_grids:
            f.write(c + "\n")
    sys.stderr.flush()
    print("\nResults written to " + output_file)


if __name__ == "__main__":
    fire.Fire(main)
