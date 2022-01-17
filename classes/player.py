from classes.level_rewards import LevelRewards
from classes.inventories import PlayerInventory
from math import floor
from typing import Union

globalindent = 0

def _game_print (*args, sep : str= " ", end : str = "\n", flush : bool = False) -> None:
    print("\x1b[2K" + ("    " * globalindent), end="")
    print(*args, sep=sep, end=end, flush=flush)

class Player ():
    ## Player
    def __init__ (self) -> None:
        self.shield : int = 0
        self.maxh : int = 10
        self.health : int = 10
        self.attack : int = 1
        self.defense : int = 0
        self.maxm : int = 0
        self.mana : int = 0
        self.maxs : int = 5
        self.stamina : int = 5
        self.xp : int = 0
        self.level : int = 0
        self.levelingmod : float = 1.2
        self.reqxp : int = 5
        self.levrew : LevelRewards = LevelRewards()
        self.inventory : PlayerInventory = PlayerInventory()
    def _levelup (self) -> None:
        self.xp -= self.reqxp
        self.level += 1
        self.reqxp = floor(self.reqxp * self.levelingmod)
        self.maxh += self.levrew.health
        self.maxm += self.levrew.mana
        self.maxs += self.levrew.stamina
        self.attack += self.levrew.attack
        self.defense += self.levrew.defense
        self.levrew.level()
        self.inventory.maxslots += 5
    def reset_values (self, dohealth : bool = False, domana : bool = False) -> None:
        self.stamina = self.maxs
        if (dohealth):
            self.health = self.maxh
        if (domana):
            self.mana = self.maxm
    def calc_stat (self, statid : str) -> int:
        return {"h":self.health,"a":self.attack,"d":self.defense,"s":self.stamina,"m":self.mana}[statid] + self.inventory.calc_stat(statid)
    def setstat (self, statid : str, value : int) -> None:
        x : Union[None, str] = None
        if (statid == "h"):
            self.health = value
            x = "health"
        elif (statid == "a"):
            self.attack = value
            x = "attack"
        elif (statid == "d"):
            self.defense = value
            x = "defense"
        elif (statid == "s"):
            self.stamina = value
            x = "stamina"
        elif (statid == "m"):
            self.mana = value
            x = "mana"
        elif (statid == "maxh"):
            self.maxh = value
        _game_print(f"player stat {x} set to {value}" if x != None else f"failed to set player stat {statid}")
    def takedmg (self, amount : int) -> bool:
        amount : int = max(0, amount - self.calc_stat("d"))
        self.health -= amount
        if (self.health <= 0):
            return True
        else:
            return False
    def receive_xp (self, amount : int) -> None:
        self.xp += amount
        if (self.xp >= self.reqxp):
            self._levelup()