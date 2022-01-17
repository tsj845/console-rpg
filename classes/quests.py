from typing import List
from classes.gamemap import GameMap
game = GameMap()

class Task ():
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
            if (t["type"] == "COUNT"):
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
        game.queue("task", (self.text, self.rewards, self.comptext))

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
        game.queue("quest", (self.name, self.rewards, self.comptext))

# manages quests
class QuestManager ():
    ## QuestManager
    def __init__ (self) -> None:
        self.quests : List[Quest] = []
        self.torem : List[str] = []
        self.completed : List[Quest] = []
        self.cqids : List[str] = []
    def remdone (self) -> None:
        ol = len(self.quests)
        for i in range(ol):
            i = ol - i - 1
            quest : Quest = self.quests[i]
            if (quest.qid in self.torem):
                quest.complete()
                self.cqids.append(quest.qid)
                self.completed.append(self.quests.pop(i))
        self.torem.clear()
    def event (self, kind : str, specific : str, *data) -> None:
        for quest in self.quests:
            if (quest.event(kind, specific, *data)):
                self.torem.append(quest.qid)
        self.remdone()
    def add_quest (self, quest : Quest) -> None:
        self.quests.append(quest)