#!/usr/bin/env python3
# coding: utf-8

import datetime
import os
from collections import defaultdict

import colors
import fire

from .data import load_wordle_data

MY_DIR = os.path.dirname(os.path.realpath(__file__))

# print((color(' ', '', 'green') + ' ') +  3 * (color(' ', '', 'yellow') + ' ') + color(' ', '', 'grey'))


class WordleGame:
    black = colors.color(" ", "", "grey")
    green = colors.color(" ", "", "green")
    yellow = colors.color(" ", "", "yellow")
    # black = "⬛"
    # green = "🟩"
    # yellow = "🟨"

    wordlen = 5
    first_wordle_date = datetime.date(2021, 6, 19)
    wordle_number = None
    wordle_date = None

    def __init__(self, solution=None, wordle_number=None, wordle_data_file=None):
        assert not (solution and wordle_number), "Cannot specify solution and wordle_number"

        self.solutions, self.valid_words = load_wordle_data(wordle_data_file)

        if not solution:
            if wordle_number is None:
                wordle_number = (datetime.date.today() - self.first_wordle_date).days
            self.wordle_number = wordle_number
            self.wordle_date = self.first_wordle_date + datetime.timedelta(days=wordle_number)
            solution = self.solutions[wordle_number]
        self._solution = solution

        self.won = False
        self.guesses = []
        self.all_hints = []

    def render_hints(self, hints):
        color_line = [{"G": self.green, "Y": self.yellow, "B": self.black}[c] for c in hints]
        return color_line

    def get_color_grid(self):
        if self.wordle_number is not None:
            wordle_num_str = self.wordle_number
        else:
            wordle_num_str = f"({self._solution})"

        result = f"Wordle {wordle_num_str} {len(self.guesses)}/6\n"
        color_lines = [self.render_hints(hints) for hints in self.all_hints]
        result += "\n".join(color_lines)

        return result

    def guess(self, word):
        word = word.strip().lower()
        assert word in self.valid_words, "Invalid word: {word}"
        assert len(self.guesses) <= 6, "Already guessed 6 words"

        self.guesses.append(word)

        hints = [" "] * self.wordlen

        solution_letters = defaultdict(list)
        for i, c in enumerate(self._solution):
            solution_letters[c].append(i)

        for i, c in enumerate(word):
            if c in solution_letters:
                if i in solution_letters[c]:
                    hints[i] = "G"
                    solution_letters[c].remove(i)
                elif solution_letters[c]:
                    solution_letters[c] = solution_letters[c][1:]
                    hints[i] = "Y"
                if not solution_letters[c]:
                    del solution_letters[c]
            else:
                hints[i] = "B"

        self.all_hints.append(hints)
        if hints == ["G"] * len(word):
            self.won = True

        return "".join(hints), self.won, len(self.guesses)

    # def play(self):
    #    for trie in range(1, 7):
    #        next_word = self.next_word()
    #        if next_word is None:
    #            break
    #        self.guess(next_word)
    #        output = {
    #            "won": self.won,
    #            "guesses": trie,
    #            "color_grid": self.get_color_grid(),
    #            "wordle_number": self.wordle_number,
    #        }
    #        if output["won"]:
    #            break
    #    output["time"] = time.time()
    #    return output


def play(wordle_number=None, solution=None, wordle_data_file=None):
    game = WordleGame(
        wordle_number=wordle_number, solution=solution, wordle_data_file=wordle_data_file
    )

    if game.wordle_number is not None:
        print(
            f"\nPlaying Wordle {game.wordle_number} - Game date: {game.wordle_date.strftime('%a, %b %d, %Y')}\n"
        )

    guess_num = 1
    while not game.won and len(game.guesses) < 6:
        guess = input(f"Guess {guess_num}: ")
        hints, won, _ = game.guess(guess)
        color_line = game.render_hints(hints)
        print(color_line)
        guess_num += 1

        if won:
            print("\nYou won!\n")
            print("\n")
            print(game.get_color_grid())
            break
