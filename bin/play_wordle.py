#!/usr/bin/env python


import random
from typing import Optional

import fire
from libwordle.game import WordleGame


def main(wordle_number: Optional[int] = None, random_word: bool = False):
    game = WordleGame(wordle_number=wordle_number, random_word=random_word)
    game.play()


if __name__ == "__main__":
    fire.Fire(main)
