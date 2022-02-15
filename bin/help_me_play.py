#!/usr/bin/env python

import fire
from libwordle.game import WordleGame
from libwordle.player import WordlePlayer

# Use load_datafiles to load the data
# and create a WordlePlayer object
# to play the game.


def play(wordle_number=None):
    p = WordlePlayer()
    g = WordleGame(wordle_number=wordle_number)
    print(
        f"\nPlaying Wordle {g.wordle_number} - Game date: {g.wordle_date.strftime('%a, %b %d, %Y')}\n"
    )
    while not g.won and len(g.guesses) < g.max_guesses:
        next_best_guess = p.best_guess().upper()
        print(f"\nI suggest guessing:\n\n{next_best_guess}\n")
        guess = ""
        while guess not in g.valid_words:
            guess = input(f"\nWhat word did you choose? ").strip().lower()
        hints = g.guess(guess)
        p.add_hints(guess, hints)
    if len(g.guesses) == 1:
        print(f"\nCorrect! You got it in 1 guess!!!")
    else:
        print(f"\nCorrect! You got it in {len(g.guesses)} guesses.")


if __name__ == "__main__":
    fire.Fire(play)
