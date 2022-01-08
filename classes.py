_beta = True

from re import S
import sys

if (len(sys.argv) > 1):
    _beta = True
else:
    _beta = False

from datatables import itemmaxs, itemnamesets, itemmins, bodyslotnames, enemymins, enemymaxs
from random import choice, randrange
from numpy import ceil, floor
from time import sleep

def _game_print (*args, sep : str= " ", end : str = "\n", flush : bool = False) -> None:
    print("\x1b[2K", end="")
    print(*args, sep=sep, end=end, flush=flush)

# stores level up reward data
class LevelRewards ():
    ## LevelRewards
    def __init__ (self):
        self.health = 10
        self.mana = 5
        self.stamina = 5
        self.defense = 1
        self.attack = 1
        self.mods = 1.5
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
    def __init__ (self, it : int, name : str, stats : dict, level : int = 0, xp : int = 0, reqxp : int = 5, levelmod : float = 1.2):
        self.type = it
        self.name = name
        self.stats = stats
        self.level = level
        self.xp = xp
        self.reqxp = reqxp
        self.levelmod = levelmod
        self.lr = LevelRewards()
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
    def recieve_xp (self, amount : int) -> None:
        self.xp += amount
        if (self.xp >= self.reqxp):
            self._levelup()
    def calc_stat (self, stat : str) -> None:
        return self.stats[stat]

# handles complex item tasks
class ItemManager ():
    ## ItemManager
    def __init__ (self):
        self.namesets = itemnamesets
        self.slotnames = bodyslotnames
        self.mins = itemmins
        self.maxs = itemmaxs
    def _target (self, value, index : int, iterable : list) -> list:
        final = []
        for item in iterable:
            if (item[index] == value):
                final.append(item)
        return final
    def gri__get_names (self, x : int, level : int) -> tuple:
        lst = self._target(x, 1, self.namesets[level])
        ind = randrange(0, len(lst))
        return lst[ind], ind
    def gri__gen_stats (self, typeid : int, level : int, slotid : int, ind : int) -> dict:
        mins = self.mins[level][typeid][ind][slotid]
        maxs = self.maxs[level][typeid][ind][slotid]
        return {"h":randrange(mins["h"],maxs["h"]+1),"a":randrange(mins["a"],maxs["a"]+1),"m":randrange(mins["m"],maxs["m"]+1),"s":randrange(mins["s"],maxs["s"]+1),"d":randrange(mins["d"],maxs["d"]+1)}
    def get_rand_itemset (self, level : int, typeid : int) -> tuple:
        names, ind = self.gri__get_names(typeid, level)
        classi = names[:2]
        names = names[2:]
        return classi[0], [Item(self.slotnames[i], names[i], self.gri__gen_stats(typeid, level, i, ind), reqxp=1, levelmod=1) if names[i] != None else None for i in range(7)]

ItemManager = ItemManager()

# enemy inventory, seperate because the inventory consists only of equipped items and is not normally modified
class EnemyInventory ():
    ## EnemyInventory
    def __init__ (self, level : int, typeid : int, preset=None):
        self.level = level
        self.name = "unset"
        self.classi = typeid
        self.slots = {"head":None, "body":None, "legs":None, "boots":None, "weapon":None, "shield":None, "charm":None}
        if (preset != None):
            self.slots = preset["slots"]
            self.name = preset["name"]
            self.classi = preset["type"]
        else:
            self._gen_slots()
    def _gen_slots (self) -> None:
        self.name, items = ItemManager.get_rand_itemset(self.level, self.classi)
        self.slots = {"head":items[0], "body":items[1], "legs":items[2], "boots":items[3], "weapon":items[4], "shield":items[5], "charm":items[6]}
    def calc_stat (self, stat : str) -> int:
        total = 0
        for key in self.slots.keys():
            if (self.slots[key] == None):
                continue
            total += self.slots[key].calc_stat(stat)
        return total

# stores data about an enemy
class Enemy ():
    ## Enemy
    def __init__ (self, typeid : int, level : int, preset=None):
        self.typeid = typeid
        self.level = level
        mins = enemymins[level][typeid]
        maxs = enemymaxs[level][typeid]
        self.inven = EnemyInventory(level, typeid, preset)
        self.name = self.inven.name
        if (preset != None):
            self.health = preset["health"]
            self.defense = preset["defense"]
            self.attack = preset["attack"]
            self.stamina = preset["stamina"]
            self.mana = preset["mana"]
        else:
            self.health = randrange(mins["h"], maxs["h"]+1)
            self.defense = randrange(mins["d"], maxs["d"]+1)
            self.mana = randrange(mins["m"], maxs["m"]+1)
            self.stamina = randrange(mins["s"], maxs["s"]+1)
            self.attack = randrange(mins["a"], maxs["a"]+1)
        self.maxhealth = self.health
        self.maxstamina = self.stamina
        self.maxmana = self.mana
    def calc_stat (self, statid : str) -> int:
        return {"h":self.health,"a":self.attack,"d":self.defense,"s":self.stamina,"m":self.mana}[statid] + self.inven.calc_stat(statid)
    def takedmg (self, amount : int) -> bool:
        amount = max(0, amount - self.calc_stat("d"))
        self.health -= amount
        if (self.health <= 0):
            return True
        else:
            return False

# player inventory
class PlayerInventory ():
    ## PlayerInventory
    def __init__ (self):
        self.slots = []
        self.maxslots = 10
        self.body = {"head":None, "body":None, "legs":None, "boots":None, "weapon":None, "shield":None, "charm":None}
    def add (self, item : Item) -> bool:
        if (len(self.slots) >= self.maxslots):
            return False
        self.slots.append(item)
        return True
    def remove (self, index : int):
        try:
            return self.slots.pop(index)
        except:
            return False
    def equip (self, slot : int, index : int) -> bool:
        if (len(self.slots) <= index or slot not in self.body.keys()):
            return False
        if (self.body[slot] != None):
            self.slots.append(self.body.slot)
            self.body[slot] = None
        self.body[slot] = self.slots.pop(index)
        return True
    def calc_stat (self, stat : str) -> int:
        total = 0
        for key in self.body.keys():
            if (self.body[key] == None):
                continue
            total += self.body[key].calc_stat(stat)
        return total

# stores player data
class Player ():
    ## Player
    def __init__ (self):
        self.shield = 0
        self.maxh = 10
        self.health = 10
        self.attack = 1
        self.defense = 0
        self.maxm = 0
        self.mana = 0
        self.maxs = 5
        self.stamina = 5
        self.xp = 0
        self.level = 0
        self.levelingmod = 1.2
        self.reqxp = 5
        self.levrew = LevelRewards()
        self.inventory = PlayerInventory()
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
        x = None
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
        amount = max(0, amount - self.calc_stat("d"))
        self.health -= amount
        if (self.health <= 0):
            return True
        else:
            return False
    def receive_xp (self, amount : int) -> None:
        self.xp += amount
        if (self.xp >= self.reqxp):
            self._levelup()

# handles top level game logic
class Runner ():
    ## Runner
    def __init__ (self):
        self.player = Player()
        # collections of rooms
        self.area_data = {}
        # a single room
        self.room_data = {}
        # all the data in the game
        self.full_data = {"dungeons":[], "npcs":[], "quests":[], "enemies":[], "misc":[]}
        self.active_quests = []
        # active enemies/entities
        self.enemies = []
        self.entities = []
        self.netq = []
        # game state flags
        self.incombat = False
        self.gameover = False
        # events
        self.listeners = {"any":{"null":[]}, "input":{"null":[]}, "output":{"null":[]}, "load":{"null":[],"area":[],"room":[]}, "combat":{"null":[],"start":[],"win":[],"lose":[],"attack":[],"enemy-death":[]}, "quest":{"null":[],"accept":[],"complete":[]}, "reward":{"null":[],"combat":[],"quest":[]}, "dialog":{"null":[],"start":[],"leave":[],"continue":[]}, "shop":{"null":[],"enter":[],"leave":[]}}
    ## events
    def listen (self, listener, kind : str = "any", specific : str = "null") -> None:
        self.listeners[kind][specific].append(listener)
    def _trigger_any (self, kind : str = "any", spec : str = "null") -> None:
        for l in self.listeners["any"]["null"]:
            l((kind, spec))
    def trigger_event (self, kind : str, specific : str, *data) -> None:
        self._trigger_any(kind, specific)
        for l in self.listeners[kind][specific]:
            l((kind, specific), *data)
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
    ## combat
    def _form_endat (self, data : dict):
        if ("eid" in data):
            pass
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
            self.enemies.append(ene)
            self.netq.append(ene)
        self.incombat = True
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
                if (ent["unid"] == ind):
                    lst.pop(i)
                    break
            self._upenunid()
            if (len(self.enemies) == 0):
                self.incombat = False
                self.player.reset_values()
        if (len(self.enemies) > 0):
            self._enemy_atk()
    ## loading
    def load_area (self, data : dict) -> None:
        self.area_data = data.copy()
        self.load_room(self.area_data["rooms"][int(self.area_data["startroom"])] if self.area_data["startroom"].isdigit() else self._grabroom(self.area_data["startroom"]))
        self.trigger_event("load", "area", self.area_data)
    def load_room (self, data : dict) -> None:
        self.room_data = data
        self.room_data["visit"] = None
        self.trigger_event("load", "room", data)
        self._check_combat()
    def load_full (self, data : list) -> None:
        for i in range(len(data)):
            x = data[i]
            self.full_data[["dungeons","npcs","quests","enemies","misc"][int(x["did"])]].append(x)
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
            if ("visit" in room or room['uid'] in cons or _beta):
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
    ## combat input
    def _parse_combin (self, text : str) -> None:
        if (text == "list"):
            for en in self.enemies:
                _game_print(f"<ENEMY type={en.typeid} level={en.level} h={en.calc_stat('h')} a={en.calc_stat('a')} d={en.calc_stat('d')} s={en.calc_stat('s')} m={en.calc_stat('m')}>")
        elif (text == "status"):
            _game_print(f"h={self.player.health}/{self.player.maxh} a={self.player.attack} d={self.player.defense} s={self.player.stamina} m={self.player.mana}")
        elif (text.startswith("attack")):
            self._attack(text)
        elif (text == "rest"):
            self.player.stamina = self.player.maxs
            self.player.mana += ceil((self.player.maxm - self.player.mana) / 2)
            _game_print("you reset to regain your strength")
            self._enemy_atk()
    ## input
    def parse_input (self, text : str) -> None:
        if (_beta):
            if (text.startswith("sps")):
                text = text.split(" ")
                self.player.setstat(text[1], int(text[2]))
                return
        if (self.incombat):
            self._parse_combin(text)
            return
        # map of area
        if (text == "map"):
            self._disp_map()
        # list interactions
        elif (text.startswith("list")):
            self._list_room(text, self.room_data)
        # move
        elif (text.startswith("walk")):
            self._walk_to(text)
        # fight neutral entity
        elif (text.startswith("fight")):
            pass
        # talk to npc
        elif (text.startswith("talk")):
            pass
        # inventory
        elif (text == "inven"):
            pass
        # loot the room
        elif (text == "loot"):
            pass
        # peek into another room
        elif (text.startswith("peek")):
            self._peek(text)
        self.trigger_event("input", "null", text)
    ## quests
    def _parse_qes (self, quest : dict) -> tuple:
        focus = quest["tasks"]["0"]["trigger"]
        return focus["kind"], focus["specific"]
    def _reward (self, rewards : dict) -> None:
        for r in rewards["list"]:
            if (r["name"] == "XP"):
                self.player.receive_xp(int(r["amount"]))
            elif (r["name"] == "ITEM"):
                pass
        self.trigger_event("reward", "quest", rewards)
    def _compquest (self, qid : str) -> None:
        quest = None
        for i in range(len(self.active_quests)):
            if (self.active_quests[i]["qid"] == qid):
                quest
                quest = self.active_quests[i]
                break
        self.trigger_event("quest", "complete", quest)
        self._reward(quest["rewards"])
    def _progquest (self, qid : str) -> None:
        quest = None
        for i in range(len(self.active_quests)):
            if (self.active_quests[i]["qid"] == qid):
                quest
                quest = self.active_quests[i]
                break
        quest["prog"] = quest["prog"] + 1
        if (quest["prog"] == len(quest["tasks"].keys())-1):
            self._compquest(qid)
        else:
            self.trigger_event("quest", "progress", quest)
    def _questing (self, quest : dict):
        def f (*a):
            self._progquest(quest["qid"])
        return f
    def activate_quest (self, quest : dict) -> None:
        self.active_quests.append(quest)
        self.listen(self._questing(quest), *self._parse_qes(quest))
    ## game lost
    def lostgame (self) -> None:
        _game_print("game over")
    ## main start
    def start (self) -> None:
        while True:
            inp = input("\x1b[2K> ")
            if (inp == "save"):
                SaveLoader.save()
            elif (inp == "load"):
                SaveLoader.load()
            elif (inp == "quit"):
                if (_beta):
                    break
                if (input("type \"yes\" to confirm: ") != "yes"):
                    continue
                break
            else:
                self.parse_input(inp)
            if (self.gameover):
                self.lostgame()
                break

game = Runner()

## saveloader
class SaveLoader ():
    def __init__ (self):
        self._sf_name = "save"
        self._sf_ext = "tssvf"
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