#!/usr/bin/env python3
# coding: utf-8

import datetime
import string
from collections import defaultdict

import colors
import numpy as np

from .data import load_word_freqs, load_wordle_data


class WordleGame:
    black = lambda c: colors.color(c, "white", "grey")
    green = lambda c: colors.color(c, "white", "green")
    yellow = lambda c: colors.color(c, "white", "yellow")
    # black = "⬛"
    # green = "🟩"
    # yellow = "🟨"

    wordlen = 5
    first_wordle_date = datetime.date(2021, 6, 19)
    wordle_number = None
    wordle_date = None

    def __init__(
        self,
        solution=None,
        wordle_number=None,
        random_word=False,
        solutions=None,
        valid_words=None,
        word_freqs=None,
        max_guesses=6,
    ):
        assert not (solution and wordle_number), "Cannot specify solution and wordle_number"
        assert not (solution and random_word), "Cannot specify solution and random_word"
        assert not (wordle_number and random_word), "Cannot specify wordle_number and random_word"

        loaded_solutions = None
        if valid_words is None:
            loaded_solutions, valid_words = load_wordle_data()
        if solutions is None:
            if loaded_solutions is None:
                solutions, _ = load_wordle_data()
            else:
                solutions = loaded_solutions

        self.solutions, self.valid_words = solutions, valid_words

        if random_word:
            if word_freqs is None:
                word_freqs = load_word_freqs(only_include_words=self.valid_words)
            words, probs = zip(*word_freqs.items())
            solution = np.random.choice(words, p=probs)

        if not solution:
            if wordle_number is None:
                wordle_number = (datetime.date.today() - self.first_wordle_date).days
            self.wordle_number = wordle_number
            self.wordle_date = self.first_wordle_date + datetime.timedelta(days=wordle_number)
            solution = self.solutions[wordle_number]
        self._solution = solution

        self.won = False
        self.is_finished = False
        self.guesses = []
        self.all_hints = []
        self.keyboard_colors = {c: "white" for c in string.ascii_lowercase}
        self.max_guesses = max_guesses

    def render_char(self, color, ch=" ", ch_color="black", unicode=False):
        if unicode:
            assert ch == " ", "Character not supported for unicode"
            return {"green": "🟩", "yellow": "🟨", "grey": "⬛", "white": "⬜️"}[color]
        else:
            # if color == "white":
            #    return f" {ch.upper()} "
            # else:
            return colors.color(f" {ch.upper()} ", ch_color, color)

    def render_hints(self, hints, word=None, unicode=False):
        join_char = " "
        if word is None:
            word = " " * self.wordlen

        color_line = ""
        for h, c in zip(hints, word):
            color = {"G": "green", "Y": "yellow", "B": "grey", " ": "white"}[h]
            if unicode:
                color_line += self.render_char(color, unicode=True)
            else:
                color_line += self.render_char(color, c)
                color_line += join_char

        return color_line

    def get_color_grid(self, unicode=False, numeric=False):
        if self.wordle_number is not None:
            wordle_num_str = self.wordle_number
        else:
            # wordle_num_str = (
            #    "(" + hashlib.sha1(self._solution.encode("utf8")).hexdigest()[:10] + ")"
            # )
            wordle_num_str = "(" + self._solution + ")"

        if self.won:
            guesses = len(self.guesses)
        else:
            guesses = "X"
        result = f"Wordle {wordle_num_str} {guesses}/{self.max_guesses}\n\n"
        color_lines = [self.render_hints(hints, unicode=unicode) for hints in self.all_hints]
        if unicode:
            result += "\n".join(color_lines)
        else:
            result += "\n\n".join(color_lines)

        return result

    def guess(self, word):
        word = word.strip().lower()
        assert word in self.valid_words, f"Invalid word: {word}"
        assert not self.is_finished, "Game is over"

        self.guesses.append(word)

        if len(self.guesses) == self.max_guesses:
            self.is_finished = True

        hints = [" "] * self.wordlen

        # solution_letters = defaultdict(list)
        # for i, c in enumerate(self._solution):
        #    solution_letters[c].append(i)

        for i, c in enumerate(word):
            if self._solution[i] == c:
                hints[i] = "G"
                self.keyboard_colors[c] = "green"
            elif c in self._solution:
                hints[i] = "Y"
                if self.keyboard_colors[c] != "green":
                    self.keyboard_colors[c] = "yellow"
            else:
                hints[i] = "B"
                if self.keyboard_colors[c] not in ("green", "yellow"):
                    self.keyboard_colors[c] = "grey"

            # if c in solution_letters:
            #    if i in solution_letters[c]:
            #        hints[i] = "G"
            #        self.keyboard_colors[c] = "green"
            #        solution_letters[c].remove(i)
            #    elif solution_letters[c]:
            #        solution_letters[c] = solution_letters[c][1:]
            #        hints[i] = "Y"
            #        if self.keyboard_colors[c] != "green":
            #            self.keyboard_colors[c] = "yellow"
            #    if not solution_letters[c]:
            #        del solution_letters[c]
            # else:
            #    hints[i] = "B"
            #    if self.keyboard_colors[c] not in ("green", "yellow"):
            #        self.keyboard_colors[c] = "grey"

        self.all_hints.append(hints)
        if hints == ["G"] * len(word):
            self.won = True
            self.is_finished = True

        return hints

    def render_keyboard(self):
        kbd_1 = []
        for ch in "qwertyuiop":
            kbd_1.append(self.render_char(ch=ch, color=self.keyboard_colors[ch]))
        kbd_1 = "".join(kbd_1)

        kbd_2 = []
        for ch in "asdfghjkl":
            kbd_2.append(self.render_char(ch=ch, color=self.keyboard_colors[ch]))
        kbd_2 = "".join(kbd_2)

        kbd_3 = []
        for ch in "zxcvbnm":
            kbd_3.append(self.render_char(ch=ch, color=self.keyboard_colors[ch]))
        kbd_3 = "   " + "".join(kbd_3)

        return f"{kbd_1}\n{kbd_2}\n{kbd_3}"

    def play(self):

        if self.wordle_number is not None:
            print(
                f"\nPlaying Wordle {self.wordle_number} - Game date: {self.wordle_date.strftime('%a, %b %d, %Y')}\n"
            )

        guess_num = len(self.guesses) + 1
        color_lines = [self.render_hints(hints=" " * self.wordlen, unicode=False) for _ in range(6)]

        while not self.is_finished:
            prompt = f"Guess {guess_num}: "
            hints = None
            guess = input(prompt)
            try:
                hints = self.guess(guess)
                color_lines[guess_num - 1] = self.render_hints(hints, word=guess, unicode=False)
                guess_num += 1
            except AssertionError as e:
                print(e)

            print("\n\n      " + "\n      ".join(color_lines) + "\n\n")
            print(self.render_keyboard())
            print("")

        print("\n\n" + self.get_color_grid(unicode=True) + "\n\n")

        if self.won:
            print("\nCongratulations! You won!\n")
        else:
            print(f"\nWord was: {self._solution}\n")

        return self.won


class AbsurdleGame(WordleGame):
    def __init__(self, wordle_data_file=None):
        super().__init__(wordle_data_file=wordle_data_file)
        # FIXME
