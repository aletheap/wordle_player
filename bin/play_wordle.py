#!/usr/bin/env python


import fire
from libwordle.game import WordleGame


def main(wordle_number: int = None, wordle_data_file: str = None, random_word: bool = False):
    game = WordleGame(
        wordle_number=wordle_number, wordle_data_file=wordle_data_file, random_word=random_word
    )
    game.play()


if __name__ == "__main__":
    fire.Fire(main)
