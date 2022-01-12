_dev = True

import sys
import readline
from typing import Dict, List, Tuple, Union, Any

try:
    with open("history.txt", "x"):
        pass
except FileExistsError:
    pass

if ("-s" in sys.argv):
    _dev = True
else:
    _dev = False

from datatables import itemmaxs, itemnamesets, itemmins, bodyslotnames, enemymins, enemymaxs, pitemmins, pitemmaxs, pitemnames
from random import choice, randrange
from numpy import ceil, floor
from time import sleep

def _game_print (*args, sep : str= " ", end : str = "\n", flush : bool = False) -> None:
    print("\x1b[2K", end="")
    print(*args, sep=sep, end=end, flush=flush)

def _run_teach () -> None:
    _game_print("base commands:\n\tquit\n\tinven\n\twalk [destination]\n\tlist [options?]\n\tpeek [target]\ncombat commands:\n\tlist\n\tstatus\n\tattack [target]\n\trest\ninventory commands:\n\tback\n\tlist [target]")

# stores level up reward data
class LevelRewards ():
    ## LevelRewards
    def __init__ (self) -> None:
        self.health : int = 10
        self.mana : int = 5
        self.stamina : int = 5
        self.defense : int = 1
        self.attack : int = 1
        self.mods : float = 1.5
    def level (self) -> None:
        self.health = floor(self.health * self.mods)
        self.mana = floor(self.mana * self.mods)
        self.stamina = floor(self.stamina * self.mods)
        self.defense = floor(self.defense * self.mods)
        self.attack = floor(self.attack * self.mods)
    def setall (self, h : int = 10, m : int = 5, s : int = 5, d : int = 1, a : int = 1, mo : float = 1.5) -> None:
        self.health = h
        self.mana = m
        self.stamina = s
        self.defense = d
        self.attack = a
        self.mods = mo

# holds item data
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

# handles complex item tasks
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

# enemy inventory, seperate because the inventory consists only of equipped items and is not normally modified
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

# stores data about an enemy
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

# player inventory
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

# stores player data
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

# stores npc data
class NPC ():
    ## NPC
    def __init__ (self, npc : dict, dialog : dict) -> None:
        self.name : str = npc["name"]
        self.dialogs : List[dict] = dialog["dialog"]
        self.linedata : List[dict] = dialog["linedata"]
        self.active : int = -1
        self.pos : int = 0
        self._activate()
    def _activate (self) -> None:
        for i in range(len(self.dialogs)):
            item : dict = self.dialogs[i]
            trig : dict = item["trigger"]
            if (game.trigresult(trig)):
                self.active = item["link"]
                break
    def _goto (self, g : str) -> int:
        for i in range(self.pos+1, len(self.linedata[self.active])):
            x : dict = self.linedata[self.active][i]
            if (x["type"] == "3" and x["lname"] == g):
                return i
    def next (self, op : Union[None, str] = None) -> Union[bool, str, Tuple[str, list]]:
        if (self.pos >= len(self.linedata[self.active])):
            return False
        dat : dict = self.linedata[self.active][self.pos]
        t : int = int(dat["type"])
        if (t == 0):
            self.pos += 1
            return dat["text"]
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
            return {"id":dat["qid"]}
    def done (self) -> bool:
        return self.pos >= len(self.linedata[self.active])

# manages tasks
class Task ():
    ### NEEDS FIXING
    ## Task
    def __init__ (self, data : dict) -> None:
        self.text : str = data["text"]
        self.instructions : str = data["instructions"]
        self.comptext : str = data["comptext"]
        self.trigger : dict = data["trigger"]
        self.triggers : List[dict] = []
        if ("triggers" in data):
            self.triggers = data["triggers"]
        else:
            self.triggers = [data["trigger"]]
            self.trigger = {"name":"COMPOUND", "req":"all"}
        self.rewards : List[dict] = data["rewards"] if "rewards" in data else []
    # activates the task
    def activate (self) -> None:
        for t in self.triggers:
            if (t["name"] == "COUNT"):
                if ("o" in t):
                    t["c"] = game.counts[t["a"]] + int(t["o"])
                else:
                    t["c"] = int(t["c"])
    # runs checks to see if the task is complete
    def check (self) -> bool:
        state : int = {"all":0,"any":1}[self.trigger["req"]]
        for trigger in self.triggers:
            r : bool = game.check_qt_trigger(trigger)
            if (state == 0 and not r):
                return False
            elif (state == 1 and r):
                return True
        if (state == 0):
            return True
        elif (state == 1):
            return False
    def event (self, kind : str, specific : str, *data) -> bool:
        return self.check()
    def complete (self) -> None:
        for r in self.rewards:
            game.reward(r)

# handles quest stuff
class Quest ():
    ## Quest
    def __init__ (self, qo : dict):
        self.qid : str = qo["qid"]
        self.name : str = qo["name"]
        self.comptext : str = qo["comptext"]
        self.retreq : bool = qo["return"] == "yes"
        self.tasks : List[Task] = [Task(qo["tasks"][i]) for i in range(len(qo["tasks"]))]
        self.rewards : List[dict] = qo["rewards"]
        self.prog : int = qo["prog"]
        self.tasks[self.prog].activate()
        self.done : bool = False
        self.rag : bool = False
    def _next_task (self) -> bool:
        self.tasks[self.prog].complete()
        self.prog += 1
        if (self.prog >= len(self.tasks)):
            self.done = True
            return False
        self.tasks[self.prog].activate()
        return True
    def event (self, kind : str, specific : str, *data) -> bool:
        if (self.done):
            return True
        if (self.tasks[self.prog].event(kind, specific, data)):
            return not self._next_task()
        return False
    def complete (self) -> None:
        if (not self.done or self.rag):
            return
        self.rag = True
        for r in self.rewards:
            game.reward(r)

# manages quests
class QuestManager ():
    ## QuestManager
    def __init__ (self) -> None:
        self.quests : List[Quest] = []
        self.torem : List[str] = []
        self.completed : List[Quest] = []
    def remdone (self) -> None:
        ol = len(self.quests)
        for i in range(ol):
            i = ol - i - 1
            quest : Quest = self.quests[i]
            if (quest.qid in self.torem):
                quest.complete()
                self.completed.append(self.quests.pop(i))
        self.torem.clear()
    def event (self, kind : str, specific : str, *data) -> None:
        for quest in self.quests:
            if (quest.event(kind, specific, *data)):
                self.torem.append(quest.qid)
        self.remdone()
    def add_quest (self, quest : Quest) -> None:
        self.quests.append(quest)

# handles top level game logic
class Runner ():
    ## Runner
    def __init__ (self):
        # offloading
        self.player = Player()
        self.questmanager = QuestManager()
        # collections of rooms
        self.area_data = {}
        # a single room
        self.room_data = {}
        # all the data in the game
        self.full_data = {"dungeons":[], "npcs":[], "quests":[], "enemies":[], "dialogs":[], "misc":[]}
        # active enemies/entities
        self.enemies = []
        self.entities = []
        self.netq = []
        self.active_npc = None
        # game state flags
        self.incombat = False
        self.gameover = False
        self.indialog = False
        self.ininvent = False
        self.inshopin = False
        self.inquestm = False
        # events
        self.listeners = {"any":{"null":[]}, "input":{"null":[]}, "output":{"null":[]}, "load":{"null":[],"area":[],"room":[]}, "combat":{"null":[],"start":[],"win":[],"lose":[],"attack":[],"enemy-death":[]}, "quest":{"null":[],"accept":[],"complete":[]}, "reward":{"null":[],"combat":[],"quest":[]}, "dialog":{"null":[],"start":[],"leave":[],"continue":[]}, "shop":{"null":[],"enter":[],"leave":[]}, "inven":{"null":[], "equip":[]}, "loot":{"null":[], "chest":[]}, "pl-move":{"null":[], "walk":[]}}
        self.evflags = {}
        for broad in self.listeners.keys():
            scope = self.listeners[broad]
            self.evflags[broad] = False
            for key in scope.keys():
                self.evflags[broad+"-"+key] = False
        self.counts = {
            "kills" : 0,
            "b-won" : 0,
            "c-opened" : 0,
            "i-looted" : 0,
        }
        self.listen(self.questmanager.event)
    ## reward
    def reward (self, reward : dict) -> None:
        n = reward["name"]
        if (n == "XP"):
            self.player.receive_xp(int(reward["amount"]))
        elif (n == "ITEM"):
            self._forcegenitem(" ".join([reward["slot"], reward["iname"], reward["h"], reward["a"], reward["d"], reward["s"], reward["m"], reward["lvl"], reward["xp"], reward["xpr"], reward["xpm"]]))
        elif (n == "UPG"):
            t = reward["target"]
            if (t == "inv-slots"):
                self.player.inventory.maxslots += int(reward["amount"])
    ## quests
    def get_quest (self, qid : str) -> dict:
        quests = self.full_data["quests"]
        for q in quests:
            if (q["qid"] == qid):
                return q
    ## events
    def listen (self, listener, kind : str = "any", specific : str = "null") -> None:
        self.listeners[kind][specific].append(listener)
    def _trigger_any (self, kind : str = "any", spec : str = "null", *data) -> None:
        self.evflags["any"] = True
        self.evflags["any-null"] = True
        for l in self.listeners["any"]["null"]:
            l(kind, spec, *data)
    def trigger_event (self, kind : str, specific : str, *data) -> None:
        self.evflags[kind] = True
        self.evflags[kind+"-"+specific] = True
        self._trigger_any(kind, specific, *data)
        for l in self.listeners[kind][specific]:
            l(kind, specific, *data)
    def _room_has (self, typename : str) -> bool:
        for ent in self.room_data["list"]:
            if (ent["name"] == typename):
                return True
        return False
    def _ge_all (self, typename : str) -> list:
        ents = []
        for ent in self.room_data["list"]:
            if (ent["name"] == typename):
                ents.append(ent)
        return ents
    ## triggers
    def trigresult (self, trig : str) -> bool:
        if (trig["type"] == "lit"):
            if (trig["con"] == "always"):
                return True
            elif (trig["con"] == "never"):
                return False
        return False
    def check_qt_trigger (self, trig : dict):
        if (trig["name"] == "EVENT"):
            return self.evflags[trig["kind"]+"-"+trig["specific"]]
        elif (trig["name"] == "COUNT"):
            return self.counts[trig["a"]] >= trig["c"]
        return False
    ## combat
    def _form_endat (self, data : dict) -> Union[Tuple[int, int], Tuple[int, int, dict]]:
        def geten (eid : str) -> dict:
            for i in range(len(self.full_data["enemies"])):
                en = self.full_data["enemies"][i]
                if (en["eid"] == eid):
                    return en
        def getpreset (dat : dict) -> dict:
            d = {"name":dat["name"], "type":int(dat["type"]), "health":int(dat["baseh"]), "attack":int(dat["basea"]), "defense":int(dat["based"]), "stamina":int(dat["bases"]), "mana":int(dat["basem"]), "slots":{}}
            for slot in bodyslotnames:
                if (slot in dat):
                    it = dat["items"][slot]
                    d["slots"][slot] = Item(bodyslotnames.index(slot), it["name"], {"h":int(it["hmod"]), "a":int(it["amod"]), "d":int(it["dmod"]), "s":int(it["smod"]), "m":int(it["mmod"])}, int(it["level"]), 0, int(it["xpr"]), float(it["xpm"]))
                else:
                    d["slots"][slot] = None
            return d
        if ("eid" in data):
            dat = geten(data["eid"])
            return int(dat["type"]), int(dat["level"]), getpreset(dat)
        else:
            return int(data["type"]), int(data["level"])
    def _upenunid (self) -> None:
        c = 0
        for ent in self.room_data["list"]:
            if (ent["name"] == "ENEMY"):
                ent["unid"] = c
                c += 1
    def _check_combat (self) -> None:
        enemies = self._ge_all("ENEMY")
        self._upenunid()
        if (not len(enemies)):
            return
        self.enemies = []
        for en in enemies:
            ene = Enemy(*self._form_endat(en))
            for c in "hadsm":
                if (c+"abs" in en):
                    ene.setstat(c, int(en[c+"abs"]))
            self.enemies.append(ene)
            self.netq.append(ene)
        self.incombat = True
        _game_print("entering combat...")
        self.trigger_event("combat", "start")
    def _enemy_atk (self) -> None:
        en = self.netq.pop(0)
        self.netq.append(en)
        def gi (en : Enemy):
            return self.enemies.index(en)
        e = gi(en)
        if (en.stamina == 0):
            _game_print(f"enemy {e} reseted to regain strength")
            en.stamina = en.maxstamina
            en.mana = en.maxmana
            return
        en.stamina -= 1
        _game_print(f"enemy {e} attacked dealing {max(0, en.calc_stat('a') - self.player.calc_stat('d'))} damage")
        if (self.player.takedmg(en.calc_stat("a"))):
            _game_print(f"enemy {e} killed you")
            self.gameover = True
            self.trigger_event("combat", "lose")
    def _attack (self, text : str) -> None:
        if (self.player.stamina == 0):
            _game_print("you don't have the strength left to do that")
            return
        if (len(text) < 7):
            return
        text = text[7:]
        if (not text.isdigit()):
            return
        text = int(text) - 1
        if (text >= len(self.enemies)):
            return
        self.player.stamina -= 1
        en = self.enemies[text]
        _game_print(f"enemy {text} took {max(0, self.player.calc_stat('a') - en.calc_stat('d'))} damage")
        if (en.takedmg(self.player.calc_stat("a"))):
            _game_print(f"enemy {text} was defeated")
            self.netq.pop(self.netq.index(en))
            ind = self.enemies.index(en)
            self.enemies.pop(ind)
            lst = self.room_data["list"]
            for i in range(len(lst)):
                ent = lst[i]
                if (ent["name"] == "ENEMY" and ent["unid"] == ind):
                    lst.pop(i)
                    self.trigger_event("combat", "enemy-death")
                    self.counts["kills"] += 1
                    break
            self._upenunid()
            if (len(self.enemies) == 0):
                self.incombat = False
                self.player.reset_values()
                _game_print("exiting combat...")
                self.trigger_event("combat", "win")
        if (len(self.enemies) > 0):
            self._enemy_atk()
    def _upltunid (self) -> None:
        c = 0
        for ent in self.room_data["list"]:
            if (ent["name"] == "CHEST"):
                ent["unid"] = c
                c += 1
    def _upnpunid (self) -> None:
        c = 0
        for ent in self.room_data["list"]:
            if (ent["name"] == "NPC"):
                ent["unid"] = c
                c += 1
    ## loading
    def load_area (self, data : dict) -> None:
        self.area_data = data.copy()
        self.load_room(self.area_data["rooms"][int(self.area_data["startroom"])] if self.area_data["startroom"].isdigit() else self._grabroom(self.area_data["startroom"]))
        self.trigger_event("load", "area", self.area_data)
    def load_room (self, data : dict) -> None:
        self.room_data = data
        self.room_data["visit"] = None
        self._upltunid()
        self.trigger_event("load", "room", data)
        self._check_combat()
    def load_full (self, data : list) -> None:
        for i in range(len(data)):
            x = data[i]
            self.full_data[["dungeons","npcs","quests","enemies","dialogs","misc"][int(x["did"])]].append(x)
        self.load_area(self.full_data["dungeons"][0])
    def _grabroom (self, uid : str) -> dict:
        for room in self.area_data["rooms"]:
            if (room["uid"] == uid):
                return room
    def _getroomcons (self, room : dict, flat : bool = False) -> list:
        cons = []
        for ent in room["list"]:
            if (ent["name"] == "CON"):
                cons.append(ent)
        if (flat):
            for i in range(len(cons)):
                cons[i] = cons[i]["target"]
        return cons
    ## map display
    def _disp_map (self):
        pass
    ## listing
    def _list_rooms (self) -> None:
        cons = self._getroomcons(self.room_data, True)
        for room in self.area_data["rooms"]:
            if ("visit" in room or room['uid'] in cons or _dev):
                _game_print(room['uid'] + (" (current)" if room['uid'] == self.room_data['uid'] else "") + (" (unvisited)" if "visit" not in room else ""))
    def _list_room_connections (self) -> None:
        for ent in self._getroomcons(self.room_data):
            _game_print(f"door to: {ent['target']}")
    def _list_room (self, search : str, room : dict) -> None:
        if (search == "list rooms"):
            self._list_rooms()
            return
        elif (search == "list doors"):
            self._list_room_connections()
            return
        ents = []
        etc = {"0":"melee", "1":"mage"}
        def getnpc (nid : str) -> dict:
            for i in range(len(self.full_data["npcs"])):
                npc = self.full_data["npcs"][i]
                if (npc["nid"] == nid):
                    return npc
            return {"name":"not found"}
        for i in range(len(room["list"])):
            ent = room["list"][i]
            if (ent["name"] == "ENEMY"):
                ents.append(f"<ENEMY type={etc[ent['type']]} level={ent['level']}>" if "type" in ent else f"<PREDEF name={ent['eid']}>")
            elif (ent["name"] == "NPC"):
                ents.append(f"<NPC name={getnpc(ent['nid'])['name']}>")
            elif (ent["name"] == "CHEST"):
                ents.append(f"<CHEST level={ent['level']}>")
        if (len(search) > 4):
            search = search[5:]
            length = 0
            check = ""
            if (search == "enemies"):
                length = 5
                check = "ENEMY"
            elif (search == "npcs"):
                length = 3
                check = "NPC"
            elif (search == "chests"):
                length = 5
                check = "CHEST"
            ol = len(ents)
            for i in range(ol):
                i = ol - i - 1
                if (ents[i][1:length+1] != check):
                    ents.pop(i)
        _game_print(*ents, sep="\n")
    def _peek (self, text : str) -> None:
        if (len(text) < 5):
            return
        text = text[5:]
        cons = self._getroomcons(self.room_data, True)
        if (text in cons):
            self._list_room("list", self._grabroom(text))
        elif (text == self.room_data["uid"]):
            _game_print("you're already in that room")
        else:
            _game_print("that room isn't adjacent")
    ## walking
    def _walk_to (self, text : str) -> None:
        if (len(text) < 6):
            return
        text = text[5:]
        cons = self._getroomcons(self.room_data, True)
        if (text not in cons):
            _game_print("that room isn't adjacent")
        else:
            _game_print(f"walking to {text}...")
            sleep(0.25)
            self.load_room(self._grabroom(text))
            self.trigger_event("pl-move", "walk")
    ## combat input
    def _parse_combin (self, text : str) -> None:
        if (text == "list"):
            for en in self.enemies:
                _game_print(f"<ENEMY type={en.typeid} level={en.level} h={en.calc_stat('h')} a={en.calc_stat('a')} d={en.calc_stat('d')} s={en.calc_stat('s')} m={en.calc_stat('m')}>")
        elif (text.startswith("attack")):
            self._attack(text)
        elif (text == "rest"):
            self._enemy_atk()
    ## inven input
    def _parse_invent (self, text : str) -> None:
        if (text == "back"):
            self.ininvent = False
            _game_print("leaving inventory...")
            sleep(0.25)
            _game_print("", end="")
            return
        elif (text.startswith("list")):
            if (len(text) < 6):
                return
            text = text[5:]
            if (text in ("inven", "items")):
                if (len(self.player.inventory.slots) == 0):
                    _game_print("you have nothing in your inventory")
                for i in range(len(self.player.inventory.slots)):
                    _game_print(self.player.inventory.slots[i])
            elif (text == "body"):
                for key in bodyslotnames:
                    x = self.player.inventory.body[key]
                    _game_print(f"{key} : {x if x != None else 'empty'}")
        elif (text.startswith("equip")):
            text = text.split(" ")
            if (len(text) < 3 or text[1] not in bodyslotnames or not text[2].isdigit()):
                _game_print("invalid equip command")
                return
            ind = int(text[2])-1
            if (ind < 0 or ind >= len(self.player.inventory.slots)):
                _game_print("invalid index")
                return
            if (self.player.inventory.equip(text[1], ind)):
                _game_print("item equipped")
                self.trigger_event("inven", "equip", self.player.inventory.body[text[1]])
            else:
                _game_print("failed to equip item")
        elif (text.startswith("drop")):
            if (len(text.split(" ")) < 2 or not text.split(" ")[1].isdigit()):
                _game_print("invalid drop command")
                return
            ind = int(text.split(" ")[1])-1
            if (ind < 0 or ind >= len(self.player.inventory.slots)):
                _game_print("invalid item index")
                return
            self.player.inventory.remove(ind)
            _game_print(f"dropped item from slot {ind+1}")
        elif (text == "fill status"):
            _game_print(f"currently using {len(self.player.inventory.slots)} of {self.player.inventory.maxslots} slots")
    ## dialog entry
    def _start_dialog (self, text : str) -> None:
        if (not text or not text.isdigit()):
            _game_print("invalid input")
            return
        text = int(text)-1
        npcs = self._ge_all("NPC")
        if (text < 0 or text >= len(npcs)):
            _game_print("invalid index")
            return
        self._save_hist_scope()
        def grabnpc (nd : dict) -> dict:
            for n in self.full_data["npcs"]:
                if (n["nid"] == nd["nid"]):
                    return n
        npc = grabnpc(npcs[text])
        dia = {}
        for di in self.full_data["dialogs"]:
            if (di["cid"] == npc["cid"]):
                dia = di
                break
        self.active_npc = NPC(npc, dia)
        self.indialog = True
        flavor = ("you strike a conversation with", "you start talking to", "you initiate data transfer protocols with")
        _game_print(f"{choice(flavor)} {self.active_npc.name}")
        self._parse_dialog("", True)
        self.trigger_event("dialog", "start")
    ## dialog input
    def _parse_dialog (self, text : str, k : bool = False) -> None:
        if (text == "leave"):
            self.indialog = False
            self.active_npc = None
            _game_print("leaving dialog...")
            sleep(0.25)
            self._load_hist_scope()
            self.trigger_event("dialog", "leave")
            return
        if (text == ""):
            if (not k):
                print("\x1b[2K\x1b[1A\x1b[2K", end="")
            r = self.active_npc.next()
            if (r == False):
                self._parse_dialog("leave")
                return
            if (type(r) == str):
                _game_print(r)
            elif (type(r) == dict):
                q = Quest(self.get_quest(r["id"]))
                self.questmanager.add_quest(q)
                _game_print(f"\x1b[2K{self.active_npc.name} has given you the quest {q.name}")
                self.trigger_event("quest", "accept", q)
            else:
                _game_print(f"{r[0]}: {', '.join(r[1])}")
        else:
            _game_print(self.active_npc.next(text))
        self.trigger_event("dialog", "continue")
        if (self.active_npc.done()):
            self._parse_dialog("leave")
    def _forcegenitem (self, text : str) -> None:
        text = text.split(" ")
        slotid = int(text[0])
        name = text[1].replace("-", " ")
        h = int(text[2])
        a = int(text[3])
        d = int(text[4])
        s = int(text[5])
        m = int(text[6])
        level = int(text[7]) if len(text) > 7 else 0
        xp = int(text[8]) if len(text) > 8 else 0
        xpr = int(text[9]) if len(text) > 9 else 0
        xpm = float(text[10]) if len(text) > 10 else 0
        self.player.inventory.slots.append(Item(slotid, name, {"h":h,"a":a,"d":d,"s":s,"m":m}, level, xp, xpr, xpm))
    def _lootroom (self, text : str) -> None:
        if (len(self.player.inventory.slots) >= self.player.inventory.maxslots):
            _game_print("you don't have room in your inventory")
            return
        if (not text.isdigit()):
            _game_print("invalid uid")
            return
        text = int(text) - 1
        for i in range(len(self.room_data["list"])):
            ent = self.room_data["list"][i]
            if (ent["name"] == "CHEST" and ent["unid"] == text):
                self.room_data["list"].pop(i)
                self._upltunid()
                item = ItemManager.genitem(int(ent["level"]))
                self.player.inventory.add(item)
                _game_print(f"you got: lvl {int(ent['level'])} {item.name}")
                break
        self.trigger_event("loot", "chest")
    ## quest input
    def _parse_quest (self, text : str) -> None:
        if (text == "back"):
            _game_print("leaving quest manager...")
            sleep(0.25)
            self.inquestm = False
            return
        elif (text.startswith("list")):
            if (len(text) > 4):
                if (text == "list complete"):
                    if (len(self.questmanager.quests) == 0):
                        _game_print("you have no completed quests")
                        return
                    for q in self.questmanager.quests:
                        _game_print(f"<QUEST progress={q.prog} name={q.name}>")
                return
            if (len(self.questmanager.quests) == 0):
                _game_print("you have no active quests")
                return
            for q in self.questmanager.quests:
                _game_print(f"<QUEST progress={q.prog} name={q.name}>")
        elif (text.startswith("task")):
            text = text[5:]
            if (not text.isdigit()):
                _game_print("invalid uid")
                return
            text = int(text)-1
            if (text < 0 or text >= len(self.questmanager.quests)):
                _game_print("nonexistant uid")
                return
            q = self.questmanager.quests[text]
            t : Task = q.tasks[q.prog]
            _game_print(f"current task:\n\tname: {t.text}\n\tinstuctions: {t.instructions}")
    ## input
    def parse_input (self, text : str) -> None:
        if (_dev):
            try:
                if (text.startswith("sps")):
                    text = text.split(" ")
                    self.player.setstat(text[1], int(text[2]))
                    return
                elif (text.startswith("ses")):
                    text = text.split(" ")
                    self.enemies[int(text[1])].setstat(text[2], int(text[3]))
                    return
                elif (text.startswith("genitem")):
                    text = text[8:]
                    self._forcegenitem(text)
            except IndexError:
                _game_print("something went wrong")
        # do inventory stuff
        if (self.ininvent):
            self._parse_invent(text)
            return
        # do dialog stuff
        if (self.indialog):
            self._parse_dialog(text)
            return
        # do quest stuff
        if (self.inquestm):
            self._parse_quest(text)
            return
        # map of area
        if (text == "map"):
            self._disp_map()
        # list interactions
        elif (text.startswith("list")):
            if (not self.incombat):
                self._list_room(text, self.room_data)
        # move
        elif (text.startswith("walk")):
            if (not self.incombat):
                self._walk_to(text)
        # fight neutral entity
        elif (text.startswith("fight")):
            if (not self.incombat):
                pass
        # talk to npc
        elif (text.startswith("talk")):
            if (not self.incombat):
                self._start_dialog(text[5:])
        # inventory
        elif (text == "inven"):
            self.ininvent = True
            _game_print("entering inventory")
            sleep(0.25)
            _game_print("", end="")
        # manage quests
        elif (text == "quests"):
            self.inquestm = True
            _game_print("entering quest manager...")
            sleep(0.25)
            _game_print("", end="")
        # loot the room
        elif (text.startswith("loot")):
            if (not self.incombat):
                self._lootroom(text[5:])
        # peek into another room
        elif (text.startswith("peek")):
            if (not self.incombat):
                self._peek(text)
        # check player status
        elif (text == "status"):
            current_health = "\u2665"*self.player.health
            total_health = "\u2661"* (self.player.maxh - self.player.health)
            health_color = "\x1b[0m"
            percentage = self.player.health / self.player.maxh
            if percentage <= 1.0 and percentage > .75:
                health_color = "\x1b[38;2;0;200;0m"
            elif percentage <= .75 and percentage > .25:
                health_color = "\x1b[38;2;245;245;0m"
            elif percentage <= .25:
                health_color = "\x1b[38;2;245;0;0m"
            _game_print(f"health: {health_color}{current_health}{total_health}\x1b[0m\nattack: {self.player.calc_stat('a')}\ndefense: {self.player.calc_stat('d')}\nstamina: {self.player.calc_stat('s')}\nmana: {self.player.calc_stat('m')}")
        # regain strength
        elif (text == "rest"):
            self.player.stamina = self.player.maxs
            self.player.mana += ceil((self.player.maxm - self.player.mana) / 2)
            _game_print("you rest to regain your strength")
        if (self.incombat):
            self._parse_combin(text)
        self.trigger_event("input", "null", text)
    ## game lost
    def lostgame (self) -> None:
        _game_print("game over")
    ## inspect
    def _inspect (self) -> None:
        shorts = {}
        def handleshort (inp : str) -> None:
            x = int(inp[3])
            inp = inp[5:]
            if (x == 0):
                inp = inp.split("::")
                shorts[inp[0]] = inp[1]
            elif (x == 1):
                shorts.pop(inp)
            elif (x == 2):
                print(shorts.keys())
            elif (x == 3):
                shorts.clear()
        def doshorts (inp : str) -> str:
            for key in shorts.keys():
                inp = inp.replace(f"^{key}", shorts[key])
            return inp
        while True:
            inp = input("> ")
            if (inp == "exit"):
                break
            inp = doshorts(inp)
            if (inp.startswith("S:/")):
                handleshort(inp)
            else:
                try:
                    print(eval(inp))
                except:
                    print("something went wrong")
    ## history
    def _save_hist_scope (self, clear : bool = True) -> None:
        readline.write_history_file("history.txt")
        if (clear):
            readline.clear_history()
    def _load_hist_scope (self) -> None:
        readline.read_history_file("history.txt")
    ## main start
    def start (self) -> None:
        if (not _dev):
            _run_teach()
        while True:
            inp = input("\x1b[2K> ")
            if (inp == "save"):
                SaveLoader.save()
            elif (inp == "load"):
                SaveLoader.load()
            elif (inp == "quit"):
                if (_dev):
                    break
                if (input("type \"yes\" to confirm: ") != "yes"):
                    continue
                break
            elif (inp == "inspect" and _dev):
                self._inspect()
            else:
                self.parse_input(inp)
            if (self.gameover):
                self.lostgame()
                break

game = Runner()

## saveloader
class SaveLoader ():
    def __init__ (self) -> None:
        self._sf_name : str = "save"
        self._sf_ext : str = "tssvf"
        try:
            with open(f"{self._sf_name}.{self._sf_ext}", "x"):
                pass
        except FileExistsError:
            pass
    def _fileman (self, rw : bool = False, data : str = ""):
        with open(f"{self._sf_name}.{self._sf_ext}", ("w" if rw else "r")) as f:
            if (rw):
                f.write(data)
            else:
                lines = f.read()
        if (not rw):
            return lines
    ## save
    def save (self) -> None:
        pass
    ## load
    def load (self) -> None:
        pass

SaveLoader = SaveLoader()