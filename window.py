import PyQt5.QtCore as qt
import PyQt5.QtWidgets as widgets
import PyQt5.QtGui as gui
from PyQt5.Qt import Qt as Qt
import sys
from typing import List

class DisplayO (widgets.QWidget):
    def __init__ (self, title="testing - press ESC to quit", game=None) -> None:
        super().__init__()
        self.setWindowTitle(title)
        self.setObjectName("top")
        self.setStyleSheet("QWidget#top {background:#222222} QPushButton {color:lime} QLabel, QWidget#top > QWidget {color:white;background:transparent}")
        self.game = game
        self.text_font = gui.QFont("courier")
        self.lines = widgets.QWidget(self)
        self.line_man = widgets.QVBoxLayout(self.lines)
        # self.write("XBCS")
        # self.write("test 1")
        # self.write("cast 1\nNBHS")
        print(self.geometry())
    def write (self, text : str) -> None:
        for item in text.split("\n"):
            self.add_line(item)
    def add_line (self, text : str) -> None:
        w = widgets.QLabel(text)
        w.setFont(self.text_font)
        self.line_man.addWidget(w, 0, qt.Qt.AlignBottom)
    def type_char (text : str) -> None:
        pass
    def keyPressEvent (self, ev : gui.QKeyEvent) -> None:
        try:
            key, text = ev.key(), ev.text()
            if (key == Qt.Key_Space):
                print("space")
            elif (key in (Qt.Key_Return, Qt.Key_Enter)):
                print("enter")
            # escape quits the program
            elif (key == Qt.Key_Escape):
                # print("esc")
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
                # print(key, text)
        except AttributeError as e:
            print(e)

default_mono = gui.QFont("courier")
default_foreground = "#f0f0f0"
default_background = "#222222"
gxoff = 20

class Text (widgets.QLabel):
    def __init__ (self, text="", parent=None, font=default_mono, y=0, color=default_foreground, background=default_background):
        super().__init__(text, parent)
        self.setFont(font)
        self.setStyleSheet(f"* {'{'}background:{background};color:{color}{'}'}")
        self._y = 0
        self._parent = parent
        self.height = self.geometry().height()
        self.y = y
    @property
    def y (self) -> int:
        return self._y
    @y.setter
    def y (self, value : int) -> None:
        self._y = value
        self.update_y()
    def update_y (self) -> None:
        if (self._parent != None):
            self.move(0, 0)
            print(self._parent.bottom - (self.y+1) * self.height, self.y, self._parent.bottom)
            self.move(gxoff, self._parent.bottom - ((self._y+1) * self.height - self.height))

class Display (widgets.QWidget):
    def __init__ (self, title="testing - press ESC to quit", game=None) -> None:
        super().__init__()
        self.setWindowTitle(title)
        self.setObjectName("top")
        self.setStyleSheet("QWidget#top {background:#222222} QPushButton {color:lime} QLabel, QWidget#top > QWidget {color:white;background:transparent}")
        self.game = game
        self.lines : List[Text] = []
        self.write("XBCS")
        self.write("test 1")
        self.write("cast 1\nNBHS")
        # print(self.geometry())
    def redraw_lines (self) -> None:
        for l in self.lines:
            # l.move(0, 0)
            # l.y = l.y
            l.update_y()
    @property
    def bottom (self) -> int:
        return self.geometry().bottom()
    def write (self, text : str) -> None:
        for item in text.split("\n"):
            self.add_line(item)
    def add_line (self, text : str) -> None:
        for l in self.lines:
            l.y += 1
        w = Text(text, self, y=0)
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
                # print("enter")
            # escape quits the program
            elif (key == Qt.Key_Escape):
                # print("esc")
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
                # print(key, text)
        except AttributeError as e:
            print(e)
    def resizeEvent(self, a0: gui.QResizeEvent) -> None:
        self.redraw_lines()

def start (game) -> None:
    app = widgets.QApplication([])
    # print(dir(gui.QFontDatabase()))

    display = Display(game=game)
    display.resize(800, 600)
    display.show()
    # print(display.geometry())

    sys.exit(app.exec())

start(None)