from classes.ansi import ANSI

Ansi = ANSI()

class GameMap ():
    def __init__ (self):
        self.intern = []
        self.y = -1
        self.x = -1
        self.newline()
    def render (self) -> None:
        for i in range(self.y+1):
            for l in range(2):
                for j in range(len(self.intern[i])):
                    if (l == 0):
                        print(f"{self.intern[i][j][3]}", end="")
                        print(f"{self.intern[i][j][0]}", end="")
                        print(f"{self.intern[i][j][4]}", end="")
                    elif (l == 1):
                        print(f" {self.intern[i][j][2]}  ", end="")
                print("")

    def add (self, code : int, unid : int = None, cons : str = None, direc : int = None) -> None:
        l = self.intern[self.y][self.x]
        a = False
        # spacing
        if (code == 0):
            a = True
            l[3] = "  "
        # discovered location
        elif (code == 1):
            a = True
            l[0] = f"{unid}"
            l[1] = ANSI.vertical_light if "u" in cons else " "
            l[2] = ANSI.vertical_light if "d" in cons else " "
            l[3] = (ANSI.horizontal_light*2) if "l" in cons else " "
            l[4] = ANSI.horizontal_light if "r" in cons else "  "
        # undiscovered location
        elif (code == 2):
            a = True
            l[0] = "?"
        elif (code == 3):
            a = True
            l[0] = [Ansi["c-tr"], Ansi["c-rd,l-hl"], Ansi["l-hl,c-dl"], Ansi["l-hl,c-lt"], Ansi["l-hl,t-lur"], " "+Ansi["t-urd"], Ansi["l-hl,t-rdl"], Ansi["l-hl,t-dlu"], Ansi["l-hl,cross-l"]][direc]
            pa = [(1, 4), (4, 2), (2, 3), (3, 1), (3, 4, 1), (1, 4, 2), (3, 4, 2), (2, 3, 1), (3, 4, 1, 2)][direc]
            l[2] = ANSI.vertical_light if 2 in pa else " "
            l[3] = ANSI.horizontal_light if 3 in pa else " "
            l[4] = ANSI.horizontal_light if 4 in pa else " "
        if (a):
            self._incx()
    def _incx (self) -> None:
        self.x += 1
        self.intern[self.y].append([" " for i in range(5)])
    def newline (self) -> None:
        self.y += 1
        self.x = -1
        self.intern.append([])
        self._incx()