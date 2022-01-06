from datatables import itemmaxs, itemnamesets, itemmins, bodyslotnames, enemymins, enemymaxs
from random import choice, randrange
from numpy import floor

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
    def level (self):
        self.health = floor(self.health * self.mods)
        self.mana = floor(self.mana * self.mods)
        self.stamina = floor(self.stamina * self.mods)
        self.defense = floor(self.defense * self.mods)
        self.attack = floor(self.attack * self.mods)
    def setall (self, h=10, m=5, s=5, d=1, a=1, mo=1.5):
        self.health = h
        self.mana = m
        self.stamina = s
        self.defense = d
        self.attack = a
        self.mods = mo

# holds item data
class Item ():
    ## Item
    def __init__ (self, it, name, stats, level=0, xp=0, reqxp=5, levelmod=1.2):
        self.type = it
        self.name = name
        self.stats = stats
        self.level = level
        self.xp = xp
        self.reqxp = reqxp
        self.levelmod = levelmod
        self.lr = LevelRewards()
        self.lr.setall(*stats["upgrades"] if "upgrades" in stats.keys() else [0, 0, 0, 0, 0])
    def _levelup (self):
        self.xp -= self.reqxp
        self.reqxp = floor(self.reqxp * self.levelmod)
        self.level += 1
        self.stats["h"] = self.stats["h"] + self.lr.health
        self.stats["a"] = self.stats["a"] + self.lr.attack
        self.stats["m"] = self.stats["m"] + self.lr.mana
        self.stats["s"] = self.stats["s"] + self.lr.stamina
        self.stats["d"] = self.stats["d"] + self.lr.defense
        self.lr.level()
    def recieve_xp (self, amount : int):
        self.xp += amount
        if (self.xp >= self.reqxp):
            self._levelup()
    def calc_stat (self, stat):
        return self.stats[stat]

# handles complex item tasks
class ItemManager ():
    ## ItemManager
    def __init__ (self):
        self.namesets = itemnamesets
        self.slotnames = bodyslotnames
        self.mins = itemmins
        self.maxs = itemmaxs
    def _target (self, value, index, iterable):
        final = []
        for item in iterable:
            if (item[index] == value):
                final.append(item)
        return final
    def gri__get_names (self, x, level):
        return choice(self._target(x, 1, self.namesets[level]))
    def gri__gen_stats (self, typeid, level, slotid):
        mins = self.mins[level][typeid][slotid]
        maxs = self.maxs[level][typeid][slotid]
        return {"h":randrange(mins["h"],maxs["h"]+1),"a":randrange(mins["a"],maxs["a"]+1),"m":randrange(mins["m"],maxs["m"]+1),"s":randrange(mins["s"],maxs["s"]+1),"d":randrange(mins["d"],maxs["d"]+1)}
    def get_rand_itemset (self, level, typeid):
        names = self.gri__get_names(typeid, level)
        classi = names[:2]
        names = names[2:]
        return [Item(self.slotnames[i], names[i], self.gri__gen_stats(typeid, level, i, classi), reqxp=1, levelmod=1) if names[i] != None else None for i in range(7)]

ItemManager = ItemManager()

# enemy inventory, seperate because the inventory consists only of equipped items and is not normally modified
class EnemyInventory ():
    ## EnemyInventory
    def __init__ (self, level, typeid, preset=None):
        self.level = level
        self.name = "unset"
        self.classi = typeid
        self.slots = {"head":None, "body":None, "legs":None, "boots":None, "weapon":None, "shield":None, "charm":None}
        if (preset != None):
            self.slots = preset["slots"]
            self.name = preset["name"]
            self.classi = preset["classi"]
        else:
            self.slots = self._gen_slots()
    def _gen_slots (self):
        self.name, self.classi, items = ItemManager.get_rand_itemset(self.level, self.typeid)
        self.slots = {"head":items[0], "body":items[1], "legs":items[2], "boots":items[3], "weapon":items[4], "shield":items[5], "charm":items[6]}

# stores data about an enemy
class Enemy ():
    ## Enemy
    def __init__ (self, typeid, level, preset=None):
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
            self.stamina = randrange(mins["m"], maxs["m"]+1)
            self.attack = randrange(mins["a"], maxs["a"]+1)

# player inventory
class PlayerInventory ():
    ## PlayerInventory
    def __init__ (self):
        self.slots = []
        self.maxslots = 10
        self.body = {"head":None, "body":None, "legs":None, "boots":None, "weapon":None, "shield":None, "charm":None}
    def add (self, item):
        if (len(self.slots) >= self.maxslots):
            return False
        self.slots.append(item)
        return True
    def remove (self, index):
        try:
            return self.slots.pop(index)
        except:
            return False
    def equip (self, slot, index):
        if (len(self.slots) <= index or slot not in self.body.keys()):
            return False
        if (self.body[slot] != None):
            self.slots.append(self.body.slot)
            self.body[slot] = None
        self.body[slot] = self.slots.pop(index)
        return True
    def calc_stat (self, stat):
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
    def _levelup (self):
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
    def receive_xp (self, amount : int):
        self.xp += amount
        if (self.xp >= self.reqxp):
            self._levelup()

# handles top level game logic
class Runner ():
    ## Runner
    def __init__ (self):
        self.player = Player()
        self.area_data = {}
        self.room_data = {}
        self.full_data = []
        self.active_quests = []
        self.enemies = []
        self.entities = []
        # events
        self.listeners = {"any":{"null":[]}, "input":{"null":[]}, "output":{"null":[]}, "load":{"null":[],"area":[],"room":[]}, "combat":{"null":[],"start":[],"win":[],"lose":[],"attack":[],"enemy-death":[]}, "quest":{"null":[],"accept":[],"complete":[]}, "reward":{"null":[],"combat":[],"quest":[]}, "dialog":{"null":[],"start":[],"leave":[],"continue":[]}, "shop":{"null":[],"enter":[],"leave":[]}}
    ## events
    def listen (self, listener, kind="any", specific="null"):
        self.listeners[kind][specific].append(listener)
    def _trigger_any (self, kind="any", spec="null"):
        for l in self.listeners["any"]["null"]:
            l((kind, spec))
    def trigger_event (self, kind, specific, *data):
        self._trigger_any(kind, specific)
        for l in self.listeners[kind][specific]:
            l((kind, specific), *data)
    ## loading
    def load_area (self, data):
        self.trigger_event("load", "area", data)
    def load_room (self, data):
        self.trigger_event("load", "room", data)
    def load_full (self, data):
        self.full_data = data
    ## input
    def parse_input (self, text):
        self.trigger_event("input", "null", text)
    ## quests
    def _parse_qes (self, quest):
        focus = quest["tasks"]["0"]["trigger"]
        return focus["kind"], focus["specific"]
    def _reward (self, rewards):
        for r in rewards["list"]:
            if (r["name"] == "XP"):
                self.player.receive_xp(int(r["amount"]))
            elif (r["name"] == "ITEM"):
                pass
        self.trigger_event("reward", "quest", rewards)
    def _compquest (self, qid):
        quest = None
        for i in range(len(self.active_quests)):
            if (self.active_quests[i]["qid"] == qid):
                quest
                quest = self.active_quests[i]
                break
        self.trigger_event("quest", "complete", quest)
        self._reward(quest["rewards"])
    def _progquest (self, qid):
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
    def _questing (self, quest):
        def f (*a):
            self._progquest(quest["qid"])
        return f
    def activate_quest (self, quest):
        self.active_quests.append(quest)
        self.listen(self._questing(quest), *self._parse_qes(quest))
    ## main start
    def start (self):
        while True:
            inp = input("> ")
            if (inp == "save"):
                pass
            elif (inp == "load"):
                pass
            elif (inp == "quit"):
                if (input("type \"yes\" to confirm: ") != "yes"):
                    continue
                break
            else:
                self.parse_input(inp)