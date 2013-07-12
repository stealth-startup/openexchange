#!/usr/bin/python

__author__ = 'Rex'

import os


def start():
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    os.chdir(SCRIPT_DIR)
    while True:
        if os.system('python manage.py processblock') == 2:
            break


if __name__ == "__main__":
    start()
