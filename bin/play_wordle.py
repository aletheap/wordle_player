#!/usr/bin/env python

import sys

import fire
from libwordle.game import play

if __name__ == "__main__":
    fire.Fire(play)
