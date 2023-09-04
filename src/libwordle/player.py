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
import time

# from collections import Counter
from collections import defaultdict

import numpy as np
from tqdm import tqdm

from libwordle.data import WORD_LENGTH, load_data, load_word_freqs, load_wordle_data
from libwordle.game import WordleGame
from libwordle.visualization import save_results, save_stats

from .data import load_data


class WordlePlayer:
    black = 1
    yellow = 2
    green = 3
    # green = "🟩"
    # yellow = "🟨"
    # black = "⬛"
    wordlen = 5

    def __init__(self, words, freqs, hints, opening_word=None):
        # if word_freqs is None:
        #    _, _, word_freqs = load_data()
        # self.word_freqs = word_freqs

        self.words = words
        self.freqs = freqs
        self.hints_tensor = hints
        self.opening_word = str(opening_word)
        self.all_guesses = []
        self.all_hints = []

        self.won = False
        self.letters_in_word = set([])
        self.letters_not_in_word = set([])
        self.chars = [{"no": set([]), "yes": None} for _ in range(self.wordlen)]
        self._update()

    def _update(self):
        self.regexes = self._update_regexes()
        self.filtered_words = self._filter_words()
        # self.word_scores = self._score_words()
        # print(f"{self.regexes=}")

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
        for letter in self.letters_in_word:
            regexes.append(re.compile(f"^.*{letter}"))
        if self.letters_not_in_word:
            regexes.append(
                re.compile(
                    "[^" + "".join(self.letters_not_in_word) + "]{" + str(self.wordlen) + "}"
                )
            )
        return [re.compile(main_regex)] + [re.compile(r) for r in regexes]

    def _matches_all_regexes(self, word):
        for r in self.regexes:
            if not r.match(word):
                return False
        return True

    def _filter_words(self):
        return [w for w in self.pre_calculated_hints["words"] if self._matches_all_regexes(w)]

    # def _score_one_word(self, word):
    #     freqs = defaultdict(float)
    #     for solution in self.filtered_words:
    #         result = ""
    #         for i, letter in enumerate(word):
    #             if letter == solution[i]:
    #                 result += "G"
    #             elif letter in solution:
    #                 result += "Y"
    #             else:
    #                 result += "B"
    #         freqs[result] += 1  # self.word_freqs[solution]
    #     s = sum(freqs.values())
    #     probs = [v / s for v in freqs.values()]
    #     h = self._entropy(probs)
    #     return h

    def best_guess(self):
        if len(self.all_guesses) == 0 and self.opening_word is not None:
            return self.opening_word

        self._update()
        # we only care about words we haven't ruled out yet
        idx_filter = np.isin(self.words, self.filtered_words)
        words = self.words[idx_filter]
        hints_tensor = self.hints_tensor[idx_filter, :][:, idx_filter]
        hints_tensor = np.expand_dims(hints_tensor, -1)
        hints_strings = np.expand_dims(np.expand_dims(np.unique(hints_tensor), 0), 0)

        hints_booleans = (
            hints_tensor == hints_strings
        )  # boolean tensor: (guesses, solutions, hints_strings)
        hints_probs = hints_booleans.mean(axis=1)  # (guesses, probabilities of each hint string)
        hints_probs += (hints_probs == 0) * 1e-12  # avoid log(0) errors
        h = (-hints_probs * np.log2(hints_probs)).sum(
            axis=1
        )  # hint string distribution entropy for each possible guess word

        # return the guess that maximizes entropy of hint string distribution
        return words[np.argmax(h)]

    def wrong_position(self, letter, position):
        letter = letter.lower()
        self.chars[position]["no"].add(letter)
        self.letters_in_word.add(letter)

    def correct(self, letter, position):
        letter = letter.lower()
        self.chars[position]["yes"] = letter

    def not_in_word(self, letter, position=None):
        letter = letter.lower()
        self.letters_not_in_word.add(letter)

    def clean_hints(self, hints):
        if isinstance(hints, list):
            hints = "".join(hints)
        return hints.strip().upper()

    def valid_hints(self, hints):
        if not isinstance(hints, str):
            return False
        if not len(hints) == self.wordlen:
            return False
        hints_s = set(self.clean_hints(hints))
        return hints_s.issubset(set("GYB"))

    def add_hints(self, word, hints):
        hints = self.clean_hints(hints)
        self.all_guesses.append(word)
        self.all_hints.append(word)
        # print(f"Adding hints: {hints}")
        if hints == "G" * 5:
            self.won = True
        for i, h in enumerate(hints):
            f = {"G": self.correct, "Y": self.wrong_position, "B": self.not_in_word}[h]
            f(word[i], i)

    # def best_guess(self):
    #     self._update()
    #     if len(self.word_scores) > 0:
    #         return self.word_scores[0][1]
    #     else:
    #         return None


class AutomatedTeam:
    @classmethod
    def parallel_play(
        cls,
        output_dir=".",
        save_grids=True,  # if True, save grids to output_dir
        num_threads=None,  # defaults to all available cores
        max_games=3000,  # max number of games to play
    ) -> None:
        """Play all possible Wordle games using multiple processor cores,
        and print stats on the progress and results. Also saves the results
        to a JSON file and produces a plot of the results."""

        solutions, valid_words, word_freqs = load_data()
        precalculated_hints = WordleHints.precalulate_all_hints()
        results_file = os.path.join(output_dir, "results.json")
        num_games = min(len(solutions), max_games)

        with mp.Pool(num_threads) as p:
            r = [
                p.apply_async(
                    cls.play_one_game,
                    (i, solutions, valid_words, precalculated_hints),
                )
                for i in range(num_games)
            ]
            finished = 0
            with tqdm(total=num_games, unit="game(s)", smoothing=0) as pb:
                while finished < num_games:
                    new_finished = len([1 for x in r if x.ready()])
                    pb.update(new_finished - finished)
                    finished = new_finished
            results = [x.get() for x in r]
            with open(results_file, "w") as f:
                json.dump(results, f)

        save_stats(results, output_dir)
        if save_grids:
            save_results(results, output_dir)

    @classmethod
    def play_one_game(cls, wordle_number, solutions, valid_words, precalculated_hints):
        game = WordleGame(
            wordle_number=wordle_number,
            word_data={
                "solutions": solutions,
                "valid_words": valid_words,
            },
        )
        player = WordlePlayer(**precalculated_hints)

        all_hints = []

        while not game.is_finished:
            word = player.best_guess()
            hints = game.guess(word)
            all_hints.append(hints)
            player.add_hints(word, hints)

        color_grid = []
        for hints in all_hints:
            grid_line = [{"B": 1, "Y": 2, "G": 3}[h] for h in hints]
            color_grid.append(grid_line)

        output = {
            "won": game.won,
            "guesses": len(game.all_guesses),
            "color_grid": color_grid,
            "wordle_number": wordle_number,
            "time": time.time(),
        }

        return output


class WordleHints:
    cache = None
    cache_file = "pre_calculated_hints"

    def __init__(self):
        pass

    @classmethod
    def precalulate_all_hints(cls):
        """Precalculate the hints for all possible guesses and solutions"""
        if cls.cache is None:
            if not os.path.exists(cls.cache_file + ".npz"):
                word_freqs = sorted(list(load_word_freqs().items()))
                words, freqs = list(zip(*word_freqs))
                d = {
                    "words": np.array(words),
                    "freqs": np.array(freqs),
                    "hints": np.zeros((len(words), len(words)), dtype=np.uint8),
                }
                for i, guess in enumerate(tqdm(words, desc="pre-calculating hints")):
                    for j, solution in enumerate(words):
                        hints = WordleGame.calculate_hints(guess, solution)
                        d["hints"][i, j] = cls.hints_to_byte(hints)
                print("calculating best first word (this will take a while)...")
                dummy_player = WordlePlayer(**d)
                opening_word = dummy_player.best_guess()
                print(f'best first word word: "{opening_word}"')
                d["opening_word"] = np.array(opening_word)
                print("saving pre-calculated hints to disk...")
                np.savez_compressed(cls.cache_file, **d)
            cls.cache = dict(np.load(cls.cache_file + ".npz"))
        return cls.cache

    @staticmethod
    def hints_to_byte(hints: str):
        """Convert a string of hints to a byte"""
        t = np.array([{"B": 0, "Y": 1, "G": 2}[h] for h in hints])
        places = t * (3 ** np.arange(len(t) - 1, -1, -1))
        return places.sum().astype(np.uint8)
