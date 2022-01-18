from typing import  Union, List, Tuple
from classes.ansi import ANSI
from classes.exprs import Exprs

class NPC ():
    ## NPC
    def __init__ (self, npc : dict, dialog : dict, game) -> None:
        self.name : str = npc["name"]
        self.dialogs : List[dict] = dialog["dialog"]
        self.linedata : List[dict] = dialog["linedata"]
        self.active : int = -1
        self.pos : int = 0
        self.cid : str = dialog["cid"]
        self._activate(game)
    def _activate (self, game) -> None:
        for i in range(len(self.dialogs)):
            item : dict = self.dialogs[i]
            trig : dict = item["trigger"]
            if (game.trigresult(self.cid, trig)):
                self.active = item["link"]
                break
    def _goto (self, g : str) -> int:
        for i in range(self.pos+1, len(self.linedata[self.active])):
            x : dict = self.linedata[self.active][i]
            if (x["etype"] == "3" and x["lname"] == g):
                return i
    def next (self, op : Union[None, str] = None) -> Union[bool, str, Tuple[str, list]]:
        if (self.pos >= len(self.linedata[self.active])):
            return False
        dat : dict = self.linedata[self.active][self.pos]
        t : int = int(dat["etype"])
        if (t == 0):
            self.pos += 1
            return Exprs.rep_colors(dat["text"], 1)
        elif (t == 1):
            if (op != None):
                if (op in dat["opts"].keys() and dat != "name"):
                    self.pos = self._goto(dat["opts"][op])
                    return self.next()
            else:
                return dat["text"], list(dat["opts"].keys())[1:]
        elif (t == 2):
            self.pos = self._goto(dat["goto"])
            return self.next()
        elif (t == 3):
            self.pos += 1
            return self.next()
        elif (t == 4):
            self.pos += 1
            return {"et":4, "id":dat["qid"]}
        elif (t == 5):
            self.pos += 1
            return {"et":5, "cid":self.cid, "ref":dat["ref"], "val":dat["val"]}
    def done (self) -> bool:
        return self.pos >= len(self.linedata[self.active])