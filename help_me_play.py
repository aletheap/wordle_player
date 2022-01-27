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
    print(
        f"\nPlaying Wordle {wp.wordle_number} - Game date: {wp.wordle_date.strftime('%a, %b %d, %Y')}\n"
    )
    while not wp.won_game:
        print(f"\nI suggest guessing:\n\n{wp.next_word().upper()}\n")
        guess = ""
        while guess not in all_playable_words:
            guess = input("\nWhat word did you choose? ").strip().lower()
        wp.guess(guess)
        wp._update()
    if wp.num_guesses == 1:
        print(f"\nCorrect! You got it in 1 guess!!!")
    else:
        print(f"\nCorrect! You got it in {wp.num_guesses} guesses.")


if __name__ == "__main__":
    fire.Fire(play)
