_dev = True

import os
import sys
import readline
import atexit
from typing import Dict, List, Tuple, Union, Any
import json
from classes.ansi import ANSI
from classes.items import * 
from classes.inventories import *
from classes.player import Player
from classes.quests import *
from classes.enemy import Enemy
from classes.npc import NPC
from classes.gamemap import GameMap
from classes.exprs import Exprs

try:
    with open("history.txt", "x"):
        pass
except FileExistsError:
    pass

_dev = False
_nosave = False
_mansave = False
_readinitfile = False
_noload = False


if ("-s" in sys.argv):
    _dev = True
if ("-n" in sys.argv):
    _nosave = True
    if ("-ms" in sys.argv):
        _mansave = True
if ("-p" in sys.argv):
    _readinitfile = True
if ("-nl" in sys.argv):
    _noload = True

from helpers.datatables import itemmaxs, itemnamesets, itemmins, bodyslotnames, enemymins, enemymaxs, pitemmins, pitemmaxs, pitemnames
from random import choice, randrange
from math import ceil, floor
from time import sleep
from helpers.parsers import nqs
import json

globalindent = 0

def _game_print (*args, sep : str= " ", end : str = "\n", flush : bool = False) -> None:
    print("\x1b[2K" + ("    " * globalindent), end="")
    print(*args, sep=sep, end=end, flush=flush)

def _run_teach () -> None:
    with open("story/story-outline.txt") as file:
        _game_print(file.read())
    _game_print(f"\ntype {ANSI.help_green}help{ANSI.reset} for command information.")

Ansi = ANSI()
ItemManager = ItemManager()

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
        self.map = {}
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
        self.dflags = {}
        self.reg_dflags = []
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
        self._queue : List[Tuple[str, list]] = []
        self.__initfile = False
    ## reward
    def reward (self, reward : dict, indent : int = 0) -> None:
        global globalindent
        globalindent = indent
        n = reward["type"]
        if (n == "XP"):
            a = int(reward["amount"])
            _game_print(f"you got {a} xp")
            self.player.receive_xp(a)
        elif (n == "ITEM"):
            self._forcegenitem(" ".join([reward["slot"], reward["iname"], reward["h"], reward["a"], reward["d"], reward["s"], reward["m"], reward["lvl"], reward["xp"], reward["xpr"], reward["xpm"]]))
        elif (n == "UPG"):
            t = reward["target"]
            if (t == "inv-slots"):
                a = int(reward["amount"])
                self.player.inventory.maxslots += a
                _game_print(f"you inventory capacity was increased by {a}, raising total capacity to {self.player.inventory.maxslots}")
        globalindent = 0
    ## quests
    def get_quest (self, qid : str) -> dict:
        quests = self.full_data["quests"]
        for q in quests:
            if (q["qid"] == qid):
                return q
    def queue (self, itype : str, data : Tuple[str, list]) -> None:
        self._queue.append((itype, data))
    def _empty_queue (self) -> None:
        for i in range(len(self._queue)):
            item = self._queue.pop(0)
            itype = item[0]
            data = item[1]
            if (itype in ("task", "quest")):
                _game_print(f"{itype} \"{data[0]}\" completed")
                for r in data[1]:
                    self.reward(r, indent=1)
                _game_print(f"{ANSI.violet}{ANSI.italic}{data[2]}{ANSI.unitalic}{ANSI.default_text}")
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
            if (ent["type"] == typename):
                return True
        return False
    def _ge_all (self, typename : str) -> list:
        ents = []
        for ent in self.room_data["list"]:
            if (ent["type"] == typename):
                ents.append(ent)
        return ents
    ## triggers
    def trigresult (self, cid : str, trig : str) -> bool:
        if (trig["etype"] == "lit"):
            if (trig["con"] == "always"):
                return True
            elif (trig["con"] == "never"):
                return False
        elif (trig["etype"] == "flag"):
            if (self.dflags[cid+trig["ref"]] == trig["con"]):
                return True
            else:
                return False
        elif (trig["etype"] == "quest"):
            return trig["qid"] in self.questmanager.cqids
        return False
    def check_qt_trigger (self, trig : dict):
        if (trig["type"] == "EVENT"):
            return self.evflags[trig["kind"]+"-"+trig["specific"]]
        elif (trig["type"] == "COUNT"):
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
            d = {"name":dat["name"], "type":int(dat["etype"]), "health":int(dat["baseh"]), "attack":int(dat["basea"]), "defense":int(dat["based"]), "stamina":int(dat["bases"]), "mana":int(dat["basem"]), "slots":{}}
            for slot in bodyslotnames:
                if (slot in dat):
                    it = dat["items"][slot]
                    d["slots"][slot] = Item(bodyslotnames.index(slot), it["name"], {"h":int(it["hmod"]), "a":int(it["amod"]), "d":int(it["dmod"]), "s":int(it["smod"]), "m":int(it["mmod"])}, int(it["level"]), 0, int(it["xpr"]), float(it["xpm"]))
                else:
                    d["slots"][slot] = None
            return d
        if ("eid" in data):
            dat = geten(data["eid"])
            return int(dat["etype"]), int(dat["level"]), getpreset(dat)
        else:
            return int(data["etype"]), int(data["level"])
    def _upenunid (self) -> None:
        c = 0
        for ent in self.room_data["list"]:
            if (ent["type"] == "ENEMY"):
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
        _game_print(f"{ANSI.red}ENTERING COMBAT{ANSI.reset}")
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
        _game_print(f"Enemy {text} took {max(0, self.player.calc_stat('a') - en.calc_stat('d'))} damage")
        if (en.takedmg(self.player.calc_stat("a"))):
            _game_print(f"Enemy {text} was defeated!")
            self.netq.pop(self.netq.index(en))
            ind = self.enemies.index(en)
            self.enemies.pop(ind)
            lst = self.room_data["list"]
            for i in range(len(lst)):
                ent = lst[i]
                if (ent["type"] == "ENEMY" and ent["unid"] == ind):
                    lst.pop(i)
                    self.trigger_event("combat", "enemy-death")
                    self.counts["kills"] += 1
                    break
            self._upenunid()
            if (len(self.enemies) == 0):
                self.incombat = False
                self.player.reset_values()
                _game_print(f"{ANSI.help_green}You won!{ANSI.reset}")
                self.trigger_event("combat", "win")
        if (len(self.enemies) > 0):
            self._enemy_atk()
    def _upltunid (self) -> None:
        c = 0
        for ent in self.room_data["list"]:
            if (ent["type"] == "CHEST"):
                ent["unid"] = c
                c += 1
    def _upnpunid (self) -> None:
        c = 0
        for ent in self.room_data["list"]:
            if (ent["type"] == "NPC"):
                ent["unid"] = c
                c += 1
    ## loading
    def load_area (self, data : dict) -> None:
        self.area_data = data
        self.area_data["visited"] = None
        for room in self.area_data["rooms"]:
            self._do_prob(room)
        self.load_room(self.area_data["rooms"][int(self.area_data["startroom"])] if self.area_data["startroom"].isdigit() else self._grabroom(self.area_data["startroom"]))
        self.trigger_event("load", "area", self.area_data)
    def _do_prob (self, data : dict) -> None:
        l = data["list"]
        ol = len(l)
        for i in range(ol):
            i = ol - i - 1
            if ("spawn-chance" in l[i]):
                if (randrange(0, 100) >= int(l[i]["spawn-chance"])):
                    l.pop(i)
    def load_room (self, data : dict) -> None:
        self.room_data = data
        self.room_data["visit"] = None
        self._upltunid()
        self.trigger_event("load", "room", data)
        self._check_combat()
    def load_full (self, data : list) -> None:
        for i in range(len(data)):
            x = data[i]
            if (int(x["did"]) == 5):
                self.map = x
                continue
            self.full_data[["dungeons","npcs","quests","enemies","dialogs","misc"][int(x["did"])]].append(x)
        self.load_area(self.full_data["dungeons"][0])
    def _grabroom (self, uid : str) -> dict:
        for room in self.area_data["rooms"]:
            if (room["uid"] == uid):
                return room
    def _getroomcons (self, room : dict, flat : bool = False) -> list:
        cons = []
        for ent in room["list"]:
            if (ent["type"] == "CON"):
                cons.append(ent)
        if (flat):
            for i in range(len(cons)):
                cons[i] = cons[i]["target"]
        return cons
    ## map display
    def _disp_map (self):
        def gd (tid : str) -> dict:
            for d in self.full_data["dungeons"]:
                if (d["tid"] == tid):
                    return d
        m = GameMap()
        c = 0
        i = 0
        for layer in self.map["layers"]:
            i += 1
            locs = layer["list"]
            for loc in locs:
                if (loc["type"] == "EMPTY"):
                    m.add(0)
                elif (loc["type"] == "CORNER"):
                    m.add(3, direc=int(loc["dir"]))
                elif (loc["type"] == "DUN"):
                    vin = "visited" in gd(loc["tid"])
                    if (vin or _dev):
                        cons = loc["connect"]
                        m.add(1, c, cons)
                    else:
                        m.add(2, c)
                    c += 1
            if (i < len(self.map["layers"])):
                m.newline()
        m.render()
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
            if (ent["type"] == "ENEMY"):
                ents.append(f"<ENEMY type={etc[ent['etype']]} level={ent['level']}>" if "etype" in ent else f"<PREDEF name={ent['eid']}>")
            elif (ent["type"] == "NPC"):
                ents.append(f"<NPC name={getnpc(ent['nid'])['name']}>")
            elif (ent["type"] == "CHEST"):
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
    def _dflag_init (self, data : dict) -> None:
        if (data["cid"] in self.reg_dflags):
            return
        self.reg_dflags.append(data["cid"])
        flags = data["flags"]
        for flag in flags:
            self.dflags[data["cid"]+flag["ref"]] = flag["value"]
    ## dialog entry
    def _start_dialog (self, text : str) -> None:
        def gn (n : dict) -> dict:
            n = n["nid"]
            for np in self.full_data["npcs"]:
                if (np["nid"] == n):
                    return np
        if (not text.isdigit()):
            npcs = self._ge_all("NPC")
            for i in range(len(npcs)):
                n = gn(npcs[i])
                if (n == None):
                    continue
                if (n["name"] == text):
                    text = str(i+1)
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
        self._dflag_init(dia)
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
            if (not self.__initfile):
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
                _game_print(r, end=("\n\n" if self.__initfile else "\n"))
            elif (type(r) == dict):
                if (r["et"] == 4):
                    q = Quest(self.get_quest(r["id"]))
                    self.questmanager.add_quest(q)
                    _game_print(f"\x1b[2K{self.active_npc.name} has given you the {ANSI.violet}quest{ANSI.default_text} \"{q.name}\"")
                    self.trigger_event("quest", "accept", q)
                elif (r["et"] == 5):
                    self.dflags[r["cid"]+r["ref"]] = r["val"]
                    self._parse_dialog("", True)
            else:
                _game_print(f"{r[0]}: {', '.join(r[1])}")
        else:
            _game_print(self.active_npc.next(text))
        self.trigger_event("dialog", "continue")
        if (self.active_npc.done()):
            self._parse_dialog("leave")
    ## FGI
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
        i = Item(slotid, name, {"h":h,"a":a,"d":d,"s":s,"m":m}, level, xp, xpr, xpm)
        self.player.inventory.slots.append(i)
        _game_print(f"you recieved:\n\t{i}")
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
            if (ent["type"] == "CHEST" and ent["unid"] == text):
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
        elif (text == "update"):
            _game_print("updating quests")
            self.questmanager.event("any", "null")
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
            current_health = ANSI.heart * self.player.health
            total_health = ANSI.empty_heart * (self.player.maxh - self.player.health)
            health_color = ANSI.default_text
            percentage = self.player.health / self.player.maxh
            if percentage <= 1.0 and percentage > .75:
                health_color = ANSI.health_high
            elif percentage <= .75 and percentage > .25:
                health_color = ANSI.health_medium
            elif percentage <= .25:
                health_color = ANSI.health_low
            _game_print(f"health: {health_color}{current_health}{total_health}{ANSI.default_text}\nattack: {self.player.calc_stat('a')}\ndefense: {self.player.calc_stat('d')}\nstamina: {self.player.calc_stat('s')}\nmana: {self.player.calc_stat('m')}")
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
    def __readfile (self) -> None:
        lines = None
        with open("insts.txt", "r") as f:
            lines = f.read().split("\n")
        if (lines == None):
            print("attempted to read insts.txt for instructions, could not find file")
            return
        self.__initfile = True
        for line in lines:
            self.parse_input(line)
        self.__initfile = False
    ## main start
    def start (self) -> None:
        global _nosave
        try:
            if ((not _noload and SaveLoader.load()) and not _dev):
                _run_teach()
            if (_dev and _readinitfile):
                self.__readfile()
        except:
            _nosave = True
            raise
        while True:
            inp = input("\x1b[2K> ")
            if (inp.startswith("help")):
                with open("help_text.json") as file:
                    help_text = json.loads(file.read())

                t = inp.split(" ")
                length = len(t)
                def f (s : str) -> str:
                    return Exprs.rep_colors(s)
                if length == 1:
                    _game_print(f(f"{ANSI.help_green}type help [category] for the list of all its commands{ANSI.reset}\n{help_text['help']}"))
                
                elif t[1] in help_text.keys():
                    help_t = help_text[t[1]]
                    if length == 3:
                        if t[2] in help_t["cmds"].keys():
                            _game_print(f(help_t["cmds"][t[2]]))
                        else:
                            _game_print(f(f"{ANSI.help_red}'{t[2]}' does not exist or is not implemented{ANSI.reset}"))
                    else:
                        _game_print(f(f"{ANSI.help_green}for more info on a command type help {t[1]} [command]{ANSI.reset}\n{help_t['list']}"))
                
                else:
                    _game_print(f(f"{ANSI.help_red}'{t[1]}' is not a category{ANSI.reset}"))

            elif (inp == "save"):
                if (_mansave):
                    _nosave = False
                SaveLoader.save()
                if (_mansave):
                    _nosave = True
            elif (inp == "load"):
                if (_dev):
                    SaveLoader.load()
            elif (inp == "quit"):
                if (_dev):
                    break
                if (input("type \"yes\" to confirm: ") != "yes"):
                    continue
                SaveLoader.save()
                break
            elif (inp == "inspect" and _dev):
                self._inspect()
            else:
                self.parse_input(inp)
            self._empty_queue()
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
        self.checks = {
            "-- states" : ["event", "counts", "evflags"],
            "-- player" : ["health", "attack", "defense", "stamina", "mana", "lvl", "xp", "xpr", "xpm"],
            "-- inventory" : ["capacity"],
            "-- equipped" : bodyslotnames,
            "-- location" : ["data", "room"],
            "-- quests" : [],
            "-- dflags" : ["dflags", "regflags"]
        }
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
        if (_nosave):
            return
        def fitem (item : Item) -> str:
            return f"<{bodyslotnames[item.type].upper()} name=\"{item.name}\" h={item.stats['h']} a={item.stats['a']} d={item.stats['d']} s={item.stats['s']} m={item.stats['m']} lvl={item.level} xp={item.xp} xpr={item.reqxp} xpm={item.levelmod}>"
        lines = []
        ### build the states block
        lines.append("{")
        lines.append("\t-- states")
        # gets current event id
        ev = 1 if game.incombat else (2 if game.indialog else (3 if game.ininvent else (4 if game.inquestm else (5 if game.inshopin else 0))))
        lines.append(f"\tevent = {ev}")
        # counts
        lines.append(f"\tcounts = {json.dumps(game.counts)}")
        # event flags
        lines.append(f"\tevflags = {json.dumps(game.evflags)}")
        lines.append("}")
        ### build the player block
        lines.append("{")
        lines.append("\t-- player")
        lines.append(f"\thealth = {game.player.health}/{game.player.maxh}")
        lines.append(f"\tattack = {game.player.attack}")
        lines.append(f"\tdefense = {game.player.defense}")
        lines.append(f"\tstamina = {game.player.stamina}/{game.player.maxs}")
        lines.append(f"\tmana = {game.player.mana}/{game.player.maxm}")
        lines.append(f"\tlvl = {game.player.level}")
        lines.append(f"\txp = {game.player.xp}")
        lines.append(f"\txpr = {game.player.reqxp}")
        lines.append(f"\txpm = {game.player.levelingmod}")
        lines.append("}")
        ### build the inventory block
        lines.append("{")
        lines.append("\t-- inventory")
        lines.append(f"\tcapacity = {game.player.inventory.maxslots}")
        for item in game.player.inventory.slots:
            lines.append(f"\t{fitem(item)}")
        lines.append("}")
        ### build the equipped block
        lines.append("{")
        lines.append("\t-- equipped")
        for n in bodyslotnames:
            lines.append(f"\t{n} = {'EMPTY' if game.player.inventory.body[n] == None else fitem(game.player.inventory.body[n])}")
        lines.append("}")
        ### build the location block
        lines.append("{")
        lines.append("\t-- location")
        lines.append(f"\tdata = {json.dumps(game.area_data)}")
        lines.append(f"\troom = \"{game.room_data['uid']}\"")
        lines.append("}")
        ### build the quests block
        lines.append("{")
        lines.append("\t-- quests")
        for q in game.questmanager.quests:
            lines.append(f"\t<QUEST qid={q.qid} prog={q.prog} completed=false>")
        for q in game.questmanager.completed:
            lines.append(f"\t<QUEST qid={q.qid} prog={q.prog} completed=true>")
        lines.append("}")
        ### build the dialog flags block
        lines.append("{")
        lines.append("\t-- dflags")
        lines.append(f"\tdflags = {json.dumps(game.dflags)}")
        lines.append(f"\tregflags = {json.dumps(game.reg_dflags)}")
        lines.append("}")
        self._fileman(True, "\x1c".join(lines).replace("\n","\\n").replace("\x1c","\n"))
    def _bfind (self, block : List[str], search : str) -> int:
        for i in range(len(block)):
            if (block[i].startswith(search)):
                return i
        return -1
    def _checkblock (self, searches : List[str], block : List[str]) -> bool:
        for search in searches:
            if (self._bfind(block, search) < 0):
                return True
        return False
    def _dstrut (self, l : str) -> dict:
        d = {}
        l = nqs(l[1:-1], " ")
        d["type"] = l.pop(0)
        for x in l:
            x = x.split("=")
            d[x[0]] = x[1][1:-1] if "\"" in x[1] else ({"true":True, "false":False}[x[1]] if x[1] in ("true", "false") else (float(x[1]) if "." in x[1] else int(x[1])))
        return d
    def _parseblock (self, block : List[str]) -> None:
        # block header
        bid = None
        # get block header
        for i in range(len(block)):
            l = block[i]
            if (l.startswith("-- ")):
                bid = block.pop(i)
                break
        # ensure that block has a header
        if (bid == None):
            return
        # ensure that all properties exist in block
        if (self._checkblock(self.checks[bid], block)):
            return
        ### parse states block
        if (bid == "-- states"):
            # event
            l = int(block.pop(self._bfind(block, "event")).split(" ")[2])
            game.incombat = True if l == 1 else False
            game.indialog = True if l == 2 else False
            game.ininvent = True if l == 3 else False
            game.inquestm = True if l == 4 else False
            game.inshopin = True if l == 5 else False
            # counts
            game.counts = json.loads(block.pop(self._bfind(block, "counts")).split(" ", 2)[2])
            # ev flags
            game.evflags = json.loads(block.pop(self._bfind(block, "evflags")).split(" ", 2)[2])
        ### parse player block
        elif (bid == "-- player"):
            p = game.player
            l = block.pop(self._bfind(block, "health")).split(" ")[2].split("/")
            p.health = int(l[0])
            p.maxh = int(l[1])
            p.attack = int(block.pop(self._bfind(block, "attack")).split(" ")[2])
            p.defense = int(block.pop(self._bfind(block, "defense")).split(" ")[2])
            l = block.pop(self._bfind(block, "stamina")).split(" ")[2].split("/")
            p.stamina = int(l[0])
            p.maxs = int(l[1])
            l = block.pop(self._bfind(block, "mana")).split(" ")[2].split("/")
            p.mana = int(l[0])
            p.maxm = int(l[1])
            p.level = int(block.pop(self._bfind(block, "lvl")).split(" ")[2])
            p.xp = int(block.pop(self._bfind(block, "xp")).split(" ")[2])
            p.reqxp = int(block.pop(self._bfind(block, "xpr")).split(" ")[2])
            p.levelingmod = float(block.pop(self._bfind(block, "xpm")).split(" ")[2])
        ### parse inventory block
        elif (bid == "-- inventory"):
            inv = game.player.inventory
            inv.maxslots = int(block.pop(self._bfind(block, "capacity")).split(" ")[2])
            for i in range(len(block)):
                l = block.pop(i)
                it = self._dstrut(l)
                inv.slots.append(Item(bodyslotnames.index(it["type"].lower()), it["name"], {"h":int(it["h"]),"a":int(it["a"]),"d":int(it["d"]),"s":int(it["s"]),"m":int(it["m"])}, int(it["lvl"]), int(it["xp"]), int(it["xpr"]), float(it["xpm"])))
        ### parse equipped block
        elif (bid == "-- equipped"):
            inv = game.player.inventory
            for i in range(len(bodyslotnames)):
                sn = bodyslotnames[i]
                l = block.pop(self._bfind(block, sn)).split(" ", 2)[2]
                if l == "EMPTY":
                    inv.body[sn] = None
                else:
                    it = self._dstrut(l)
                    inv.body[sn] = Item(i, it["name"], {"h":int(it["h"]),"a":int(it["a"]),"d":int(it["d"]),"s":int(it["s"]),"m":int(it["m"])}, int(it["lvl"]), int(it["xp"]), int(it["xpr"]), float(it["xpm"]))
        ### parse location block
        elif (bid == "-- location"):
            l = block.pop(self._bfind(block, "data")).split(" ", 2)[2]
            game.area_data = json.loads(l)
            r = block.pop(self._bfind(block, "room")).split(" ", 2)[2][1:-1]
            game.load_room(game._grabroom(r))
        ### parse quests block
        elif (bid == "-- quests"):
            for i in range(len(block)):
                l = block.pop(0)
                qu = self._dstrut(l)
                q = game.get_quest(str(qu["qid"]))
                q["prog"] = qu["prog"]
                q = Quest(q)
                if (qu["completed"]):
                    q.done = True
                    q.rag = True
                    game.questmanager.completed.append(q)
                else:
                    game.questmanager.add_quest(q)
        ### parse dialog flags block
        elif (bid == "-- dflags"):
            l = block.pop(self._bfind(block, "dflags")).split(" ", 2)[2]
            game.dflags = json.loads(l)
            l = block.pop(self._bfind(block, "regflags")).split(" ", 2)[2]
            game.reg_dflags = json.loads(l)
    ## load
    def load (self) -> None:
        lines = self._fileman()
        if (len(lines) < 10):
            return True
        lines = lines.split("\n")
        blocks = []
        # break lines into blocks
        cblock = []
        for i in range(len(lines)):
            line = lines[i]
            if (line == "}"):
                blocks.append(cblock)
                cblock = []
                continue
            if (line == "{"):
                continue
            cblock.append(line.lstrip())
        for block in blocks:
            self._parseblock(block)
        return False


SaveLoader = SaveLoader()

atexit.register(SaveLoader.save)