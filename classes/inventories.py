from typing import Dict, List, Tuple, Union, Any
from classes.items import *

class EnemyInventory ():
    ## EnemyInventory
    def __init__ (self, level : int, typeid : int, preset : Union[None, dict] = None) -> None:
        self.level : int = level
        self.classi : int = typeid
        self.name : str = "unset"
        self.slots : Dict[str, Union[None, Item]] = {"head":None, "body":None, "legs":None, "boots":None, "weapon":None, "shield":None, "charm":None}
        # if preset was given do that
        if (preset != None):
            self.slots = preset["slots"]
            self.classi = preset["type"]
            self.name = preset["name"]
        else:
            self._gen_slots()
    def _gen_slots (self) -> None:
        # gets a random name and item set
        self.name, items = ItemManager.get_rand_itemset(self.level, self.classi)
        # sets slots
        self.slots = {"head":items[0], "body":items[1], "legs":items[2], "boots":items[3], "weapon":items[4], "shield":items[5], "charm":items[6]}
    def setstat (self, statid : str, value : int) -> None:
        for key in bodyslotnames:
            if (self.slots[key] != None):
                self.slots[key].setstat(statid, value)
    # calculates a stat
    def calc_stat (self, stat : str) -> int:
        total : int = 0
        for key in self.slots.keys():
            if (self.slots[key] == None):
                continue
            total += self.slots[key].calc_stat(stat)
        return total

class PlayerInventory ():
    ## PlayerInventory
    def __init__ (self) -> None:
        self.slots : List[Item] = []
        self.maxslots : int = 10
        self.body : Dict[str, Union[None, Item]] = {"head":None, "body":None, "legs":None, "boots":None, "weapon":None, "shield":None, "charm":None}
    def add (self, item : Item) -> bool:
        if (len(self.slots) >= self.maxslots):
            return False
        self.slots.append(item)
        return True
    def remove (self, index : int) -> Union[Item, bool]:
        try:
            return self.slots.pop(index)
        except:
            return False
    def equip (self, slot : str, index : int) -> bool:
        if (len(self.slots) <= index or slot not in self.body.keys()):
            return False
        if (self.body[slot] != None):
            self.slots.append(self.body.slot)
            self.body[slot] = None
        self.body[slot] = self.slots.pop(index)
        return True
    def calc_stat (self, stat : str) -> int:
        total : int = 0
        for key in self.body.keys():
            if (self.body[key] == None):
                continue
            total += self.body[key].calc_stat(stat)
        return total