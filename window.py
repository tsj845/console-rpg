import PyQt5.QtCore as qt
import PyQt5.QtWidgets as widgets
import PyQt5.QtGui as gui
from PyQt5.Qt import Qt as Qt
import sys
from typing import List

default_mono = gui.QFont("courier")
default_foreground = "#f0f0f0"
default_background = "#222222"
gxoff = 20
gyoff = 20

class Text (widgets.QLabel):
    def __init__ (self, text="", parent=None, rp=None, font=default_mono, y=0, color=default_foreground, background=default_background):
        super().__init__(text, parent)
        self._w = self.width()
        self.setMinimumWidth(self._w)
        self._text = text
        self.setFont(font)
        self.adjustSize()
        self.setStyleSheet(f"* {'{'}background:{background};color:{color}{'}'}")
        self._y = 0
        self._parent = rp
        self.y = y
        self.show()
    @property
    def height (self) -> int:
        return self.geometry().height()
    @property
    def y (self) -> int:
        return self._y
    @y.setter
    def y (self, value : int) -> None:
        self._y = value
        self.update_y()
    def update_y (self) -> None:
        if (self._parent != None):
            yval = (self._parent.height - ((self._y+1) * self.height)) - gyoff
            self.move(gxoff, yval)

class Display (widgets.QWidget):
    def __init__ (self, title="testing - press ESC to quit", game=None) -> None:
        self.booting = True
        super().__init__()
        self.setWindowTitle(title)
        self.setObjectName("top")
        self.resize(800, 600)
        self.setStyleSheet("QWidget#top {background:#222222} QPushButton {color:lime} QLabel, QWidget#top > QWidget {color:white;background:transparent} * {background:transparent}")
        self.game = game
        self.lines : List[Text] = []
        self.booting = False
        self.write("1")
    def redraw_lines (self) -> None:
        if (self.booting):
            return
        for l in self.lines:
            l.update_y()
    @property
    def height (self) -> int:
        return self.geometry().height()
    @property
    def top (self) -> int:
        return self.geometry().top()
    @property
    def bottom (self) -> int:
        return self.geometry().bottom()
    def write (self, text : str) -> None:
        for item in text.split("\n"):
            self.add_line(item)
    def add_line (self, text : str) -> None:
        for l in self.lines:
            l.y += 1
        w = Text(text, self, rp=self, y=0)
        self.lines.append(w)
    def type_char (self, text : str) -> None:
        pass
    def keyPressEvent (self, ev : gui.QKeyEvent) -> None:
        try:
            key, text = ev.key(), ev.text()
            if (key == Qt.Key_Space):
                print("space")
            elif (key in (Qt.Key_Return, Qt.Key_Enter)):
                self.write("new line")
            # escape quits the program
            elif (key == Qt.Key_Escape):
                sys.exit()
            elif (key in (Qt.Key_Backspace, Qt.Key_Delete)):
                print("backspace")
            elif (key == Qt.Key_Shift):
                print("shift")
            elif (key == Qt.Key_Meta):
                print("meta")
            elif (key == Qt.Key_Control):
                print("control")
            elif (key == Qt.Key_Alt):
                print("alt")
            elif (key == Qt.Key_CapsLock):
                pass
            elif (key == Qt.Key_Up):
                print("ArrowUp")
            elif (key == Qt.Key_Down):
                print("ArrowDown")
            elif (key == Qt.Key_Right):
                print("ArrowRight")
            elif (key == Qt.Key_Left):
                print("ArrowLeft")
            else:
                self.type_char(text)
        except AttributeError as e:
            print(e)
    def resizeEvent(self, ev : gui.QResizeEvent) -> None:
        if (self.booting):
            return
        self.redraw_lines()

def start (game) -> None:
    app = widgets.QApplication([])

    display = Display(game=game)
    display.show()
    display.write("XBCS")
    display.write("test 1")
    display.write("cast 1\nNBHS")
    display.write("justly")
    display.write("just y")

    sys.exit(app.exec())

start(None)