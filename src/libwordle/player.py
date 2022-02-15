#!/usr/bin/env python3
# coding: utf-8

# Wordle Player
# Plays every possible game of Wordle and prints stats on the progress and results
# Inspired by: https://bert.org/2021/11/24/the-best-starting-word-in-wordle/
# Wordle: https://www.powerlanguage.co.uk/wordle/

import datetime
import re

from .data import load_data

class WordlePlayer:
    black = 1
    yellow = 2
    green = 3
    # green = "🟩"
    # yellow = "🟨"
    # black = "⬛"
    first_wordle_date = datetime.date(2021, 6, 19)
    wordlen = 5

    def __init__(self, word_freqs=None):
        if word_freqs is None:
            _, _, word_freqs = load_data()

        max_freq = max(word_freqs.values())
        self.word_freqs = {w: f / max_freq for w, f in word_freqs.items()}

        self.in_word = set([])
        self.chars = [{"no": set([]), "yes": None} for _ in range(self.wordlen)]
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
        filtered_words = [w for w in self.word_freqs if self._matches_all_regexes(w)]
        return filtered_words

    def _score_letters(self):
        letter_scores = {L: 0 for L in "abcdefghijklmnopqrstuvwxyz"}

        # measure how close each letter is to dividing the remaining words in half
        # s = 1  means the letter is in exactly half of words
        # s = 0 means the letter is in 0 words or all words
        n_filtered_words = len(self.filtered_words)

        if n_filtered_words > 0:
            for word in self.filtered_words:
                for L in word:
                    letter_scores[L] += 1

            letter_scores = {L: (2 * (f / n_filtered_words)) - 1 for L, f in letter_scores.items()}
            letter_scores = {L: 1 - (abs(f)) for L, f in letter_scores.items()}

        return letter_scores

    def _score_one_word(self, word):
        avg_letter_score = sum([self.letter_scores[c] for c in word]) / len(word)
        unique_letters = len(set(word))
        return avg_letter_score * unique_letters  # + self.word_freqs[word]

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

    def add_hints(self, word, hints):
        for i, r in enumerate(hints):
            f = {"G": self.correct, "Y": self.wrong_position, "B": self.not_in_word}[r]
            f(word[i], i)

    def best_guess(self):
        self._update()
        if len(self.word_scores) > 0:
            return self.word_scores[0][1]
        else:
            return None
