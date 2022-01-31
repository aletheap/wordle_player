#!/usr/bin/env python

import fire
from libwordle.game import WordleGame
from libwordle.player import WordlePlayer

# Use load_datafiles to load the data
# and create a WordlePlayer object
# to play the game.


def play():
    p = WordlePlayer()
    n_guesses = 0
    while not p.won:
        next_best_guess = p.best_guess().upper()
        print(f"\nI suggest guessing:\n\n{next_best_guess}\n")

        guess = input(f"\nWhat word did you choose? ").strip().lower()

        hints = ""
        while not p.valid_hints(hints):
            hints = input(f"\nWhat hints did you get? (e.g. gbbyg) ").strip().upper()

        p.add_hints(guess, hints)
        n_guesses += 1

    if n_guesses == 1:
        print(f"\nCongrats! You got it in 1 guess!!!")
    else:
        print(f"\nCongrats! You got it in {n_guesses} guesses.")


if __name__ == "__main__":
    fire.Fire(play)
