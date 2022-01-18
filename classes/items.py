from typing import Dict, List, Tuple, Union, Any
from helpers.datatables import itemmaxs, itemnamesets, itemmins, bodyslotnames, pitemmins, pitemmaxs, pitemnames
from random import choice, randrange
from math import floor
from classes.level_rewards import LevelRewards

class Item ():
    ## Item
    def __init__ (self, it : int, name : str, stats : Dict[str, int], level : int = 0, xp : int = 0, reqxp : int = 5, levelmod : float = 1.2) -> None:
        self.type : int = it
        self.name : str = name
        self.stats : Dict[str, int] = stats
        self.level : int = level
        self.xp : int = xp
        self.reqxp : int = reqxp
        self.levelmod : float = levelmod
        self.lr : LevelRewards = LevelRewards()
        self.lr.setall(*stats["upgrades"] if "upgrades" in stats.keys() else [0, 0, 0, 0, 0])
    def _levelup (self) -> None:
        self.xp -= self.reqxp
        self.reqxp = floor(self.reqxp * self.levelmod)
        self.level += 1
        self.stats["h"] = self.stats["h"] + self.lr.health
        self.stats["a"] = self.stats["a"] + self.lr.attack
        self.stats["m"] = self.stats["m"] + self.lr.mana
        self.stats["s"] = self.stats["s"] + self.lr.stamina
        self.stats["d"] = self.stats["d"] + self.lr.defense
        self.lr.level()
    def setstat (self, statid : str, value : int) -> None:
        self.stats[statid] = value
    def recieve_xp (self, amount : int) -> None:
        self.xp += amount
        if (self.xp >= self.reqxp):
            self._levelup()
    def calc_stat (self, stat : str) -> None:
        return self.stats[stat]
    def __str__ (self) -> str:
        return f"<{bodyslotnames[self.type].upper()} \"{self.name}\" h={self.stats['h']} a={self.stats['a']} d={self.stats['d']} s={self.stats['s']} m={self.stats['m']}>"
    def __repr__ (self) -> str:
        return self.__str__()

class ItemManager ():
    ## ItemManager
    def __init__ (self) -> None:
        self.namesets : tuple = itemnamesets
        self.slotnames : Tuple[str] = bodyslotnames
        self.mins : tuple = itemmins
        self.maxs : tuple = itemmaxs
    def _target (self, value : Any, index : int, iterable : list) -> list:
        final : List[Any] = []
        for item in iterable:
            if (item[index] == value):
                final.append(item)
        return final
    def gri__get_names (self, x : int, level : int) -> tuple:
        lst : Tuple[str, int, Union[None, Dict[str, int]]] = self._target(x, 1, self.namesets[level])
        ind : int = randrange(0, len(lst))
        return lst[ind], ind
    def gri__gen_stats (self, typeid : int, level : int, slotid : int, ind : int) -> Dict[str, int]:
        mins : Dict[str, int] = self.mins[level][typeid][ind][slotid]
        maxs : Dict[str, int] = self.maxs[level][typeid][ind][slotid]
        return {"h":randrange(mins["h"],maxs["h"]+1),"a":randrange(mins["a"],maxs["a"]+1),"m":randrange(mins["m"],maxs["m"]+1),"s":randrange(mins["s"],maxs["s"]+1),"d":randrange(mins["d"],maxs["d"]+1)}
    def get_rand_itemset (self, level : int, typeid : int) -> tuple:
        names, ind = self.gri__get_names(typeid, level)
        classi : List[Union[str, int]] = names[:2]
        names : List[Dict[str, int]] = names[2:]
        return classi[0], [Item(self.slotnames[i], names[i], self.gri__gen_stats(typeid, level, i, ind), reqxp=1, levelmod=1) if names[i] != None else None for i in range(7)]
    def genitem (self, level : int = 0) -> Item:
        slot : int = randrange(0, len(bodyslotnames))
        mins : Dict[str, int] = pitemmins[level][slot]
        maxs : Dict[str, int] = pitemmaxs[level][slot]
        stats = {"h":randrange(mins["h"],maxs["h"]+1),"a":randrange(mins["a"],maxs["a"]+1),"m":randrange(mins["m"],maxs["m"]+1),"s":randrange(mins["s"],maxs["s"]+1),"d":randrange(mins["d"],maxs["d"]+1)}
        name : str = choice(pitemnames[level][slot])
        return Item(slot, name, stats, levelmod=1)

ItemManager = ItemManager()