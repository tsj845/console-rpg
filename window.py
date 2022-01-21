import PyQt5.QtCore as qt
import PyQt5.QtWidgets as widgets
import PyQt5.QtGui as gui
from PyQt5.Qt import Qt as Qt
import sys
from typing import List, Any, Tuple
import re

ansire = re.compile("\x1b(\[?[^A-Za-z]*[A-Za-z]{1})")

boldings = {0:50, 1:87, 2:0}

default_mono = gui.QFont("courier")
default_foreground = "#f0f0f0"
default_background = "#222222"
gxoff = 20
gyoff = 20

# label with extra functionality
class Text (widgets.QLabel):
    def __init__ (self, text : str= "", parent=None, rp=None, font : gui.QFont = default_mono, y : int = 0, x : int = 0, color : str = default_foreground, background : str = default_background, bold : int = 0, italic : bool = False):
        font = gui.QFont(font.family(), weight=boldings[bold], italic=italic)
        super().__init__(text, parent)
        self.show()
        # self._w = self.frameGeometry().width()
        self._w = len(text) * rp.fwidth
        self.setMinimumWidth(self._w)
        self.setMaximumWidth(self._w)
        self._text = text
        self.setFont(font)
        self.adjustSize()
        self.setStyleSheet(f"* {'{'}background:{background};color:{color}{'}'}")
        self._y = 0
        self._x = x
        self._parent = rp
        self.y = y
        # self.x = x
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
    # @property
    # def x (self) -> int:
    #     return self._x
    # @x.setter
    # def x (self, value : int) -> None:
    #     self._x = value
    #     self.update_x()
    def update_y (self) -> None:
        if (self._parent != None):
            yval = (self._parent.height - ((self._y+1) * self.height)) - gyoff
            xval = gxoff + (self._parent.fwidth * self._x)
            print(xval, gxoff, self._x, self._parent.fwidth, self._text)
            self.move(xval, yval)

# display manager
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
        self._locked = True
        self.fwidth = 0
        self.calc_fwidth()
        self.booting = False
    def calc_fwidth (self) -> None:
        t = widgets.QLabel("x", self)
        t.setFont(default_mono)
        t.show()
        self.fwidth = t.frameGeometry().width()
        t.setParent(None)
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
    @property
    def locked (self) -> bool:
        return self._locked
    @locked.setter
    def locked (self, value : bool) -> None:
        self._locked = value
    # writes one or more lines to output
    def write (self, text : str) -> None:
        for item in text.split("\n"):
            self.add_line(item)
    def _do_ansi (self, text : str) -> List[Tuple[str, str, str, int, bool]]:
        # texts = text.split("\x1b")
        texts = re.split(ansire, text)
        ret = []
        # text, foreground, background, brightness, italics
        default = ["", default_foreground, default_background, 0, False]
        cwork = default.copy()
        def color_parse (text : str) -> str:
            if (text == "[39m"):
                return default_foreground
            if (text == "[49m"):
                return default_background
            text = text[1:-1].split(";")
            if (text[1] == "2"):
                rc = str(hex(int(text[2])))[2:]
                gc = str(hex(int(text[3])))[2:]
                bc = str(hex(int(text[4])))[2:]
                rc = ("0" if len(rc) == 1 else "") + rc
                gc = ("0" if len(gc) == 1 else "") + gc
                bc = ("0" if len(bc) == 1 else "") + bc
                return f"#{rc}{gc}{bc}"
        def parse_ansi (text : str) -> Tuple[int, Any]:
            # graphics
            if (text[-1] == "m"):
                bolds = ("[22m", "[1m", "[2m")
                ret = (3, bolds.index(text)) if text in bolds else (1, color_parse(text)) if text.split(";")[0] in ("[38", "[39") else (2, color_parse(text)) if text.split(";")[0] in ("[48", "[49") else (4, True) if text == "[3m" else (4, False) if text == "[23m" else (0, cwork[0])
                return ret
        for i in range(len(texts)):
            text = texts[i]
            # don't care about empty text
            if (text == ""):
                continue
            # if it's an ansi code
            if (len(re.findall("[A-Za-z]{1}", text)) == 1):
                # cwork isn't empty so add it to ret
                if (cwork[0] != ""):
                    ret.append(tuple(cwork.copy()))
                    cwork = default.copy()
                # reset code
                if (text == "[0m"):
                    cwork = default.copy()
                else:
                    pos, val = parse_ansi(text)
                    cwork[pos] = val
            # otherwise add the text to cwork
            else:
                cwork[0] = cwork[0] + text
        if (cwork[0] != ""):
            ret.append(tuple(cwork))
        # print(ret)
        return ret
    # adds a line
    def add_line (self, text : str) -> None:
        # self.scroll_up(1)
        for l in self.lines:
            l.y += 1
        text = self._do_ansi(text)
        print(text)
        lx = 0
        for item in text:
            w = Text(item[0], self, rp=self, y=0, color=item[1], background=item[2], bold=item[3], italic=item[4], x=lx)
            lx += len(item[0])
            self.lines.append(w)
        self.redraw_lines()
    # adds a character to input
    def type_char (self, text : str) -> None:
        pass
    # deletes a character from input
    def del_char (self) -> None:
        pass
    # handles key presses
    def keyPressEvent (self, ev : gui.QKeyEvent) -> None:
        key, text = ev.key(), ev.text()
        if (key == Qt.Key_Space):
            print("space")
        elif (key in (Qt.Key_Return, Qt.Key_Enter)):
            self.write("new line")
        # escape quits the program
        elif (key == Qt.Key_Escape):
            sys.exit()
        elif (key in (Qt.Key_Backspace, Qt.Key_Delete)):
            self.del_char()
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
    # handles resizing
    def resizeEvent(self, ev : gui.QResizeEvent) -> None:
        if (self.booting):
            return
        self.calc_fwidth()
        self.redraw_lines()

# starts the output
def start (game) -> None:
    app = widgets.QApplication([])

    display = Display(game=game)
    display.show()
    # display.write("XBCS")
    # display.write("test 1")
    # display.write("cast 1\nNBHS")
    # display.write("justly")
    # display.write("just y")
    display.write("\x1b[38;2;0;50;0m\x1b[48;2;0;255;0mGREN\x1b[0mnormie text")
    display.write("\x1b[2mfaint \x1b[1mbold \x1b[22m\x1b[3mnormal italics\x1b[0m")

    sys.exit(app.exec())

start(None)