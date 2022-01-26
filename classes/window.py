from math import floor
import PyQt5.QtCore as qt
import PyQt5.QtWidgets as widgets
import PyQt5.QtGui as gui
from PyQt5.Qt import Qt as Qt
import sys
from typing import List, Any, Tuple
import re

ansire = re.compile("\x1b(\[?[\d;]+[A-Za-z]{1})")

boldings = {0:50, 1:87, 2:0}

default_mono = gui.QFont("courier")
default_foreground = "#f0f0f0"
default_background = "#222222"
default_cursor = "rgba(204, 204, 204, 0.5)"
gxoff = 20
gyoff = 20

# label with extra functionality
class Text (widgets.QLabel):
    def __init__ (self, text : str= "", parent=None, rp=None, font : gui.QFont = default_mono, y : int = 0, x : int = 0, color : str = default_foreground, background : str = default_background, bold : int = 0, italic : bool = False):
        font = gui.QFont(font.family(), weight=boldings[bold], italic=italic)
        super().__init__(text, parent)
        self.show()
        self._w = len(text) * rp.fwidth
        self.setMinimumWidth(self._w)
        self.setMaximumWidth(self._w)
        self._textv = text
        self.setFont(font)
        self.adjustSize()
        self.setStyleSheet(f"* {'{'}background:{background};color:{color}{'}'}")
        self._y = 0
        self._x = x
        self._xval = 0
        self._yval = 0
        self._parent = rp
        self.y = y+1
    @property
    def _text (self) -> str:
        return self._textv
    @_text.setter
    def _text (self, value : str) -> None:
        self._textv = value
        self._w = len(value) * self._parent.fwidth
        self.setMinimumWidth(self._w)
        self.setMaximumWidth(self._w)
        self.setText(value)
        self.move(self._xval, self._yval)
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
            self._yval = (self._parent.height - ((self._y+1) * self.height)) - gyoff
            self._xval = gxoff + (self._parent.fwidth * self._x)
            self.move(self._xval, self._yval)

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
        self._linebuf : List[str] = []
        self._cp = 0
        self._locked = True
        self.fwidth = 0
        self.fheight = 0
        self.calc_fwidth()
        self.input_line : Text = Text("HELLOW?", self, self, y=-1)
        self.cursor : Text = Text(" ", self, self, y=-1, x=2, background=default_cursor)
        self._prefix = ""
        self._histind = 0
        self._hist : List[str] = []
        self.booting = False
    def terminate (self) -> None:
        sys.exit()
    def hist (self, dir : int = 0) -> None:
        if (dir > 0):
            if (self._histind >= len(self._hist)):
                return
        elif (dir < 0):
            if (self._histind < 1):
                return
        self._histind += dir
        self._linebuf = list(self._hist[self._histind])
        self._cp = len(self._linebuf)
        self.update_input_line()
    @property
    def cp (self) -> int:
        return self._cp
    @cp.setter
    def cp (self, value : int) -> None:
        self._cp = value
        self.cursor._x = self._cp + len(self.prefix)
        self.cursor.update_y()
    def calc_fwidth (self) -> None:
        t = widgets.QLabel("x", self)
        t.setFont(default_mono)
        t.show()
        self.fwidth = t.frameGeometry().width()
        self.fheight = t.frameGeometry().height()
        t.setParent(None)
    def redraw_lines (self) -> None:
        if (self.booting):
            return
        for l in self.lines:
            l.update_y()
    @property
    def prefix (self) -> str:
        return self._prefix
    @prefix.setter
    def prefix (self, value : str) -> None:
        self._prefix = value
        self.update_input_line()
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
            x = re.findall("\[[\d;]+[A-Za-z]{1}", text)
            # if it's an ansi code
            if (len(x) == 1):
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
        return ret
    # adds a line
    def add_line (self, text : str) -> None:
        for l in self.lines:
            l.y += 1
        text = self._do_ansi(text)
        lx = 0
        for item in text:
            w = Text(item[0], self, rp=self, y=0, color=item[1], background=item[2], bold=item[3], italic=item[4], x=lx)
            lx += len(item[0])
            self.lines.append(w)
        self.redraw_lines()
    # updates the input line
    def update_input_line (self) -> None:
        self.calc_fwidth()
        v = self._prefix + "".join(self._linebuf)
        self.input_line._text = v
    # adds a character to input
    def type_char (self, char : str) -> None:
        self._linebuf.insert(self.cp, char)
        self.cp += 1
        self.update_input_line()
    # deletes a character from input
    def del_char (self) -> None:
        if (self.cp > 0):
            self.cp -= 1
            self._linebuf.pop(self.cp)
            self.update_input_line()
    # moves the cursor one to the right
    def move_right (self) -> None:
        if (self.cp < len(self._linebuf)):
            self.cp += 1
    # moves the cursor one to the left
    def move_left (self) -> None:
        if (self.cp > 0):
            self.cp -= 1
    def send_input (self) -> None:
        if (not self._locked):
            lin = "".join(self._linebuf)
            self._hist.append(lin)
            self._histind = len(self._hist)
            self.write(self._prefix + lin)
            self._linebuf = []
            self.cp = 0
            self.update_input_line()
            self.game.main_input(lin)
    # handles key presses
    def keyPressEvent (self, ev : gui.QKeyEvent) -> None:
        key, text = ev.key(), ev.text()
        if (key == Qt.Key_Space):
            self.type_char(" ")
        elif (key in (Qt.Key_Return, Qt.Key_Enter)):
            self.send_input()
        # escape quits the program
        elif (key == Qt.Key_Escape):
            sys.exit()
        elif (key in (Qt.Key_Backspace, Qt.Key_Delete)):
            self.del_char()
        elif (key == Qt.Key_Shift):
            pass
        elif (key == Qt.Key_Meta):
            pass
        elif (key == Qt.Key_Control):
            pass
        elif (key == Qt.Key_Alt):
            pass
        elif (key == Qt.Key_CapsLock):
            pass
        elif (key == Qt.Key_Up):
            self.hist(-1)
        elif (key == Qt.Key_Down):
            self.hist(1)
        elif (key == Qt.Key_Right):
            self.move_right()
        elif (key == Qt.Key_Left):
            self.move_left()
        else:
            self.type_char(text)
    # handles resizing
    def resizeEvent(self, ev : gui.QResizeEvent) -> None:
        if (self.booting):
            return
        self.calc_fwidth()
        self.redraw_lines()

class Char ():
    def __init__ (self, char : str, fg : str, bg : str, bold : int, italic : bool):
        pass

# manages everything
class Terminal ():
    def __init__ (self, out : Display) -> None:
        self.out : Display = out
        self.lines : List[List[str]] = []
        self.x = 0
        self.y = 0
        self.mwidth = 0
        self.mheight = 0
        self.recalc()
    def recalc (self) -> None:
        self.mwidth = floor(self.out.geometry().width() / self.out.fwidth)
        self.mheight = floor(self.out.geometry().height() / self.out.fheight)
    def wchar (self, char : Char) -> None:
        pass
    def write (self, text : str) -> None:
        self.out.write(text)
    def grab (self, count : int) -> List[str]:
        lst : List[str] = []
        return lst

terminal = None

# starts the output
def start (game) -> None:
    global terminal
    app = widgets.QApplication([])

    display = Display(game=game)
    display.show()
    # display.write("XBCS")
    # display.write("test 1")
    # display.write("cast 1\nNBHS")
    # display.write("justly")
    # display.write("just y")
    # display.write("\x1b[38;2;0;50;0m\x1b[48;2;0;255;0mGREN\x1b[0mnormie text")
    # display.write("\x1b[2mfaint \x1b[1mbold \x1b[22m\x1b[3mnormal italics\x1b[0m")
    display.locked = False
    display.prefix = "> "

    terminal = Terminal(display)

    sys.exit(app.exec())