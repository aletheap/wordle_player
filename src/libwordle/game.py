#!/usr/bin/env python3
# coding: utf-8

import datetime
import string
from collections import defaultdict

import colors
import numpy as np

from .data import load_data, WORDLE_START_DATE, WORD_LENGTH


class WordleGame:
    def __init__(self, wordle_number=None, random_word=False, word_data=None, max_guesses=6):
        assert not (
            bool(wordle_number) and bool(random_word)
        ), "cannot specify both wordle_number and random_word"

        # store word data
        if word_data is None:
            solutions, valid_words, word_freqs = load_data()
            word_data = {
                "solutions": solutions,
                "valid_words": valid_words,
                "word_freqs": word_freqs,
            }
        self.solutions = word_data["solutions"]
        self.valid_words = word_data["valid_words"]

        # record solution for this game
        if random_word:
            print("choosing random word")
            words, probs = zip(*word_data["word_freqs"].items())
            self.solution = np.random.choice(words, p=probs)
            self.wordle_number = None
            self.wordle_date = None
        else:
            if wordle_number is None:
                wordle_number = (datetime.date.today() - WORDLE_START_DATE).days
            self.wordle_number = wordle_number
            self.wordle_date = WORDLE_START_DATE + datetime.timedelta(days=wordle_number)
            self.solution = self.solutions[self.wordle_number]

        self.won = False
        self.is_finished = False
        self.all_guesses = []
        self.all_hints = []
        self.max_guesses = max_guesses

    def guess(self, word):
        word = word.strip().lower()

        assert not self.is_finished, "Game is over"
        assert word not in self.all_guesses, f"Already guessed word: {word}"
        assert len(word) == WORD_LENGTH, f"Invalid word length: {word}"
        assert word in self.valid_words, f"Invalid word: {word}"

        hints = [" "] * WORD_LENGTH
        for i, c in enumerate(word):
            if self.solution[i] == c:
                hints[i] = "G"
            elif c in self.solution:
                hints[i] = "Y"
            else:
                hints[i] = "B"

        self.all_hints.append(hints)
        self.all_guesses.append(word)

        if word == self.solution:
            self.won = True

        if self.won or (len(self.all_guesses) == self.max_guesses):
            self.is_finished = True

        return hints


class InteractiveWordleGame:
    def __init__(self, wordle_number=None, random_word=False, word_data=None, max_guesses=6):
        self.game = WordleGame(
            wordle_number=wordle_number,
            random_word=random_word,
            word_data=word_data,
            max_guesses=max_guesses,
        )
        self.all_guesses = []
        self.all_hints = []

    def play(self):
        self.show_start_header()

        while not self.game.is_finished:
            prompt = f"Guess {len(self.all_guesses) + 1}: "
            guess = input(prompt).strip().lower()

            try:
                hints = self.game.guess(guess)
                self.all_guesses.append(guess)
                self.all_hints.append(hints)
            except AssertionError as e:
                print(e)

            self.show_all_hints()

        self.show_game_end()
        return self.game.won

    def show_start_header(self):
        if self.game.wordle_number is not None:
            print(
                f"\nPlaying Wordle {self.game.wordle_number} - Game date: {self.game.wordle_date.strftime('%a, %b %d, %Y')}\n"
            )

    def show_all_hints(self):
        print("\n")
        color_lines = self.render_guesses()
        for line in color_lines:
            print("      " + line)
        print("\n")
        print(self.render_keyboard())
        print("\n")

    def show_game_end(self):
        if self.game.won:
            print("")
            print("Congratulations! You won!")
            print("\n")
            print(self.render_shareable_grid())
            print("\n")
        else:
            print("")
            print(f"Word was: {self.game.solution}")
            print("")

    def render_guesses(self, new_guess=None, new_hints=None):
        lines = []

        # render any existing hints
        for guess, hints in zip(self.all_guesses, self.all_hints):
            line = [self.render_character(c, h) for h, c in zip(hints, guess)]
            lines.append(" ".join(line))

        # add any remaining blank lines
        for _ in range(self.game.max_guesses - len(self.all_guesses)):
            line = [self.render_character(" ", "W") for _ in range(WORD_LENGTH)]
            lines.append(" ".join(line))

        return lines

    def render_keyboard(self):
        # calculate colors for keyboard
        kbd_colors = {L: "W" for L in string.ascii_lowercase}
        priority = {"W": 0, "B": 1, "Y": 2, "G": 3}
        for letter, hint in zip("".join(self.all_guesses), "".join(self.all_hints)):
            if priority[hint] > priority[kbd_colors[letter]]:
                kbd_colors[letter] = hint

        # render the keyboard rows
        rows = []
        for letters in ("qwertyuiop", "asdfghjkl", "zxcvbnm"):
            row = [self.render_character(L, kbd_colors[L]) for L in letters]
            rows.append("".join(row))
        rows[-1] = "   " + rows[-1]

        return "\n".join(rows)

    def render_character(self, c, hint):
        hint_colors = {"G": "green", "Y": "yellow", "B": "grey", "W": "white"}
        return colors.color(f" {c.upper()} ", "black", hint_colors[hint])

    def render_shareable_grid(self):
        emojis = {"G": "🟩", "Y": "🟨", "B": "⬛"}
        if self.game.wordle_number is not None:
            wordle_num_str = self.game.wordle_number
        else:
            wordle_num_str = "(" + self.game.solution + ")"

        if self.game.won:
            guesses = len(self.game.all_guesses)
        else:
            guesses = "X"
        result = f"Wordle {wordle_num_str} {guesses}/{self.game.max_guesses}\n\n"
        color_lines = ["".join([emojis[h] for h in hints]) for hints in self.all_hints]
        result += "\n".join(color_lines)

        return result
