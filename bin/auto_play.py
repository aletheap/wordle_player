#!/usr/bin/env python

import fire

from libwordle.player import AutomatedTeam


def main(
    output_dir=".",
    save_grids=False,  # if True, save grids to output_dir
    num_threads=None,  # defaults to all available cores
    max_games=3000,  # max number of games to play
    wordle_number=None,  # play a single wordle game
):
    AutomatedTeam.parallel_play(
        output_dir=output_dir,
        save_grids=save_grids,
        num_threads=num_threads,
        max_games=max_games,
        wordle_number=wordle_number,
    )


if __name__ == "__main__":
    fire.Fire(main)
