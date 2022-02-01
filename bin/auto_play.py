#!/usr/bin/env python

import json
import multiprocessing as mp
import os
import time

import fire
from libwordle.data import load_data
from libwordle.game import WordleGame
from libwordle.player import WordlePlayer
from libwordle.visualization import save_results, save_stats
from tqdm import tqdm

MY_DIR = os.path.dirname(os.path.realpath(__file__))


def play_game(wordle_number, word_freqs, solutions, valid_words):
    game = WordleGame(
        wordle_number=wordle_number,
        solutions=solutions,
        valid_words=valid_words,
        word_freqs=word_freqs,
    )
    player = WordlePlayer(word_freqs=word_freqs)

    while not game.is_finished:
        word = player.best_guess()
        if word is None:
            break
        hints = game.guess(word)
        player.add_hints(word, hints)

    color_grid = []
    for hints in game.all_hints:
        color_line = [{"B": 1, "G": 3, "Y": 2}[h] for h in hints]
        color_grid.append(color_line)
    output = {
        "won": game.won,
        "guesses": len(game.guesses),
        "color_grid": color_grid,
        "wordle_number": wordle_number,
        "time": time.time(),
    }

    return output


def main(
    num_games=None,
    num_threads=None,
    output_file="wordle_grids.png",
    stats_file="wordle_stats.png",
    max_vocab_size=100_000,
    debug=False,
    mobile_friendly=False,
    save_grids=False,
):

    solutions, valid_words, word_freqs = load_data(max_vocab_size=max_vocab_size)

    num_games = num_games or len(solutions)

    if debug:
        with open(os.path.join(MY_DIR, "results.json")) as f:
            results = json.load(f)
    else:
        with mp.Pool(num_threads) as p:
            r = [
                p.apply_async(play_game, (i, word_freqs, solutions, valid_words))
                for i in range(num_games)
            ]
            finished = 0
            with tqdm(total=num_games, unit="game(s)") as pb:
                while finished < num_games:
                    new_finished = len([1 for x in r if x.ready()])
                    # progress_tracker.append((time.time() - t0, new_finished))
                    pb.update(new_finished - finished)
                    finished = new_finished
            results = [x.get() for x in r]
            results = [r for r in results if r is not None]
            with open(os.path.join(MY_DIR, "results.json"), "w") as f:
                json.dump(results, f)
            # with open(os.path.join(MY_DIR, "progress_tracker.json"), "w") as f:
            #    json.dump(progress_tracker, f)

    save_stats(results, stats_file)
    if save_grids:
        save_results(results, output_file, mobile_friendly=mobile_friendly)


if __name__ == "__main__":
    fire.Fire(main)
