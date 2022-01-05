from classes import *
from parsers import datums as content_data

game = Runner()
game.load_full(content_data)
game.start()