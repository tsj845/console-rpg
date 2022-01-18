# beta β
__version = "A-0.4"
print(f"build version {__version}\n\nsubmit feedback at https://github.com/tsj845/console-rpg \nto get syntax highlighting for .amly files follow the steps on https://github.com/tsj845/amlytheme \n")

from classes.classes import *
from helpers.parsers import datums as content_data

game.load_full(content_data)
game.start()