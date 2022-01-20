from tkinter import *
import re
from typing import Any, List, Tuple

ansire = re.compile("\x1b(\[?[^A-Za-z]*[A-Za-z]{1})")

def printkey (ev : Event):
    print(ev)

def printscroll (ev):
    print(ev)

class KeyMap ():
    ArrowUp = "\uf700"
    ArrowDown = "\uf701"
    ArrowRight = "\uf703"
    ArrowLeft = "\uf702"
    Enter = "\r"
    BackSpace = "\x7f"
    Escape = "\x1b"
    Break = "\x03"

textfont = ("Courier", "12")
boldfont = ("Courier", "12", "bold")
italicfont = ("Courier", "12", "italic")
bolditalicfont = ("Courier", "12", "bold", "italic")
# textfont = "TKFixedFont"

def get_curr_screen_geometry():
    """
    Workaround to get the size of the current screen in a multi-screen setup.

    Returns:
        geometry (str): The standard Tk geometry string.
            [width]x[height]+[left]+[top]
    """
    root = Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    geometry = root.winfo_geometry()
    root.destroy()
    return geometry

class DisplayManager ():
    def __init__ (self, title="console rpg") -> None:
        self.root = Tk()
        self.root.title(title)
        self.root.configure(background="#222222")
        # self.root.geometry(get_curr_screen_geometry().split("+")[0]+"+0+0")
        self.root.bind("<Key>", self._key_ev)
        self.root.bind("<MouseWheel>", self._scroll_ev)
        self.root.bind("<Configure>", self._resize_ev)
        self.line_disp = Frame(self.root)
        self.line_disp.configure(background="#222222")
        self.line_disp.place(anchor=SW, relx=0, rely=1, relwidth=1, relheight=1, bordermode=INSIDE)
        self.lines : List[Label] = []
        self.locked = True
        self.labys : List[int] = []
        self.history : List[str] = []
        self.lheight = 23
        self.lcwidth = 19
        self.lyoff = 20
        self.lxoff = 20
        self.bottom = self.root.winfo_height()
        self.write("\x1b[38;2;0;255;0mHello, World!\x1b[0m")
        self.write("I'm\nmultiline\n\twith indentation")
        self.write("\x1b[38;2;255;0;0mRED\x1b[38;2;0;50;0m\x1b[48;2;0;255;0mGREEN\x1b[49m\x1b[38;2;0;0;255mBLUE")
        self.write("\x1b[1mI'm bolded\x1b[22m\x1b[3mand I'm italicised\x1b[23m")
        self.cx = 0
        self.ctext : List[str] = []
    def write (self, text : str) -> None:
        text = str(text)
        text = text.split("\n")
        for line in text:
            self.addLine(line)
    def redraw_lines (self) -> None:
        localx = 0
        lv = None
        for i in range(len(self.lines)):
            ind = i
            line = self.lines[ind]
            v = self.labys[ind]
            if (v == lv):
                localx += self.lines[ind-1].winfo_width()
            else:
                localx = 0
                lv = v
            line.place(anchor=SW, x=localx+self.lxoff, y=self.bottom-self.lheight*v-self.lyoff)
    def scroll_up (self, amount : int = 1, usr : bool = False):
        # bottom most label is already on screen
        if (usr and (len(self.labys) == 0 or self.labys[-1] >= 0)):
        # if (usr and (len(self.labys) == 0 or (self.bottom - self.lheight * self.labys[-1] < self.bottom))):
            return
        for i in range(len(self.labys)):
            self.labys[i] = self.labys[i] + amount
    def scroll_down (self, amount : int = 1, usr : bool = False):
        # top most label is already on screen
        if (usr and (len(self.labys) == 0 or (self.bottom - self.lheight * self.labys[0] - self.lheight > 0))):
            return
        for i in range(len(self.labys)):
            self.labys[i] = self.labys[i] - amount
    def run (self) -> None:
        self.root.mainloop()
    def kill (self) -> None:
        self.root.destroy()
    def update_input_line (self) -> None:
        self.lines[-1]["text"] = ''.join(self.ctext)
    @property
    def locked (self) -> bool:
        return self._locked
    @locked.setter
    def locked (self, value : bool) -> None:
        self._locked = value
    def _do_ansi (self, text : str) -> List[Tuple[str, str, str, bool, bool]]:
        # texts = text.split("\x1b")
        texts = re.split(ansire, text)
        ret = []
        # text, foreground, background, brightness, italics
        default = ["", "#f0f0f0", "#222222", False, False]
        cwork = default.copy()
        def color_parse (text : str) -> str:
            if (text == "[39m"):
                return "#f0f0f0"
            if (text == "[49m"):
                return "#222222"
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
                ret = (3, bool(("[22m", "[1m").index(text))) if text in ("[22m", "[1m") else (1, color_parse(text)) if text.split(";")[0] in ("[38", "[39") else (2, color_parse(text)) if text.split(";")[0] in ("[48", "[49") else (4, True) if text == "[3m" else (4, False) if text == "[23m" else (0, cwork[0])
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
    # creates a new line
    def addLine (self, text : str = "") -> None:
        self.scroll_up(1)
        text = self._do_ansi(text)
        for item in text:
            l = Label(self.line_disp, text=item[0], font={(False,False):textfont,(False,True):italicfont,(True,False):boldfont,(True,True):bolditalicfont}[(item[3], item[4])])
            l.configure(background=item[2], foreground=item[1], borderwidth=0)
            self.lines.append(l)
            self.labys.append(0)
        self.redraw_lines()
    # puts a character on the screen
    def typechar (self, char : str) -> None:
        self.ctext.insert(self.cx, char)
        self.cx += 1
        self.update_input_line()
    # handles keyboard input
    def _key_ev (self, ev : Event) -> None:
        key = ev.char
        # some sort of meta key, ignore it
        if (key == ""):
            return
        if (key == KeyMap.Break):
            return
        if (key == KeyMap.Escape):
            self.kill()
            return
        if (self.locked):
            return
        if (key == KeyMap.Enter):
            self.addLine()
            return
        if (key in (KeyMap.ArrowRight, KeyMap.ArrowLeft)):
            if (key == KeyMap.ArrowRight and self.cx < len(self.ctext)):
                self.cx += 1
            if (key == KeyMap.ArrowLeft and self.cx > 0):
                self.cx -= 1
            return
        if (key in (KeyMap.ArrowUp, KeyMap.ArrowDown)):
            return
        if (key == KeyMap.BackSpace):
            if (self.cx > 0):
                self.cx -= 1
                self.ctext.pop(self.cx)
                self.update_input_line()
            return
        self.typechar(key)
    # handles scroll input
    def _scroll_ev (self, ev : Event) -> None:
        delta = ev.delta
        if (delta == 0):
            return
        if (delta < 0):
            self.scroll_up(1, usr=True)
        else:
            self.scroll_down(1, usr=True)
        self.redraw_lines()
    # handles window resizing
    def _resize_ev (self, ev : Event) -> None:
        self.bottom = self.root.winfo_height()
        self.redraw_lines()

dm = DisplayManager("testing - press ESC to quit")
dm.run()