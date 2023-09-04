#!/usr/bin/env python


from typing import Optional

import fire
from libwordle.game import InteractiveWordleGame


def main(wordle_number: Optional[int] = None, random_word: bool = False):
    game = InteractiveWordleGame(wordle_number=wordle_number, random_word=random_word)
    game.play()


if __name__ == "__main__":
    fire.Fire(main)
