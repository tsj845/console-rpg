from classes.inventories import EnemyInventory
from random import randrange
from typing import Union, Dict
from helpers.datatables import enemymins, enemymaxs

class Enemy ():
    ## Enemy
    def __init__ (self, typeid : int, level : int, preset : Union[None, dict] = None) -> None:
        self.typeid : int = typeid
        self.level : int = level
        mins : Dict[str, int] = enemymins[level][typeid]
        maxs : Dict[str, int] = enemymaxs[level][typeid]
        self.inven : EnemyInventory = EnemyInventory(level, typeid, preset)
        self.name : str = self.inven.name
        if (preset != None):
            self.health : int = preset["health"]
            self.defense : int = preset["defense"]
            self.attack : int = preset["attack"]
            self.stamina : int = preset["stamina"]
            self.mana : int = preset["mana"]
        else:
            self.health : int = randrange(mins["h"], maxs["h"]+1)
            self.defense : int = randrange(mins["d"], maxs["d"]+1)
            self.mana : int = randrange(mins["m"], maxs["m"]+1)
            self.stamina : int = randrange(mins["s"], maxs["s"]+1)
            self.attack : int = randrange(mins["a"], maxs["a"]+1)
        self.maxhealth : int = self.health
        self.maxstamina : int = self.stamina
        self.maxmana : int = self.mana
    def calc_stat (self, statid : str) -> int:
        return {"h":self.health,"a":self.attack,"d":self.defense,"s":self.stamina,"m":self.mana}[statid] + self.inven.calc_stat(statid)
    def setstat (self, statid : str, value : int) -> None:
        if (statid == "h"):
            self.health = value
        elif (statid == "a"):
            self.attack = value
        elif (statid == "d"):
            self.defense = value
        elif (statid == "s"):
            self.stamina = value
        elif (statid == "m"):
            self.mana = value
        self.inven.setstat(statid, value)
    def takedmg (self, amount : int) -> bool:
        amount : int = max(0, amount - self.calc_stat("d"))
        self.health -= amount
        if (self.health <= 0):
            return True
        else:
            return False