#!/usr/bin/env python

import datetime

import fire

from wordle_player import WordlePlayer, load_data_files

# Use load_datafiles to load the data
# and create a WordlePlayer object
# to play the game.


def play(wordle_number=None):
    word_freqs, solutions, all_playable_words = load_data_files()
    wp = WordlePlayer(solutions, word_freqs, wordle_number=wordle_number)
    while not wp.won_game:
        print(f"I suggest guessing:  {wp.next_word().upper()}")
        guess = ""
        while guess not in all_playable_words:
            guess = input("What word did you choose? ").strip().lower()
        wp.guess(guess)
        wp._update()
    print(f"You won! It took you {wp.num_guesses} guesses.")


if __name__ == "__main__":
    fire.Fire(play)
