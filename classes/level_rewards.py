from numpy import floor

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