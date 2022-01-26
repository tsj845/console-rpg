# beta β
__version = "A-0.4.1"

import classes.window as window
from classes.classes import *
from helpers.parsers import datums as content_data

app = window.widgets.QApplication([])
disp = window.Display(game=game)
disp.show()

terminal = window.Terminal(disp)

disp.write(f"build version {__version}\n\nsubmit feedback at https://github.com/tsj845/console-rpg \nto get syntax highlighting for .amly files follow the steps on https://github.com/tsj845/amlytheme \n")

boot(terminal)

game.load_full(content_data)
game.start()

disp.locked = False
disp.prefix = "> "

sys.exit(app.exec())