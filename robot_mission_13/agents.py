import mesa
from mesa import Agent, Model
from mesa.space import MultiGrid
import random
from objects import WasteAgent, RadioactivityAgent, WasteDisposalAgent


from enum import Enum

class Action(Enum):
    COLLECT = 0
    FUSION = 1
    MOVE_LEFT = 2
    MOVE_RIGHT = 3
    MOVE_UP = 4
    MOVE_DOWN = 5
    DROP = 6

class Robot(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)
        self.percepts = {}
        self.knowledge = {"Near_waste": {"C": None, "L": None, "R": None, "T": None, "D": None } , "carrying": []}
        self.unique_id = unique_id
        self.action = None
        
    def percept(self):
        pass
    
    def deliberate(self):
        pass   
    
    def step_agent (self): 
        self.knowledge = self.percept()
        self.action = self.deliberate(self.knowledge) 
        self.percepts = self.model.do(self, self.action)


class GreenAgent(Robot):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
    def percept(self):
        pass
    
    def deliberate(self, knowledge):
        # If carrying 1 Yellow Waste go to the right
        if len(knowledge["carrying"]) == 1 and knowledge["carrying"][0]==1:
            if self.pos[0] > 1:
                return Action.MOVE_RIGHT
            else:
                return Action.DROP
        # If carrying 2 Green Wastes, delete them and create 1 Yellow Waste
        elif len(knowledge["carrying"]) == 2:
            return Action.FUSION
        # If there is Green Waste nearby, collect it
        elif knowledge["Near_waste"]["C"] is not None :
            return Action.COLLECT
        # If there is no Green Waste at the center, random move
        else:
            return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])
        
        


class YellowAgent(Robot):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
    def percept(self):
        pass
    
    def deliberate(self, knowledge):
        pass

class RedAgent(Robot):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
    def percept(self):
        pass
    
    def deliberate(self, knowledge):
        pass

