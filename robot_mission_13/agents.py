import mesa
from mesa import Agent, Model
from mesa.space import MultiGrid
import random
from objects import WasteAgent, RadioactivityAgent, WasteDisposalAgent, Colors
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
    def __init__(self, model, unique_id):
        super().__init__(model)
        self.percepts = {}
        self.knowledge = {"Near_waste": {"C": [], "L": [], "R": [], "T": [], "D": []} , "carrying": []}
        self.unique_id = unique_id
        self.action = None
        
    def percept(self):
        pass
    
    def deliberate(self):
        pass   
    
    def step_agent(self): 
        #self.knowledge = self.percept()
        self.action = self.deliberate(self.knowledge) 
        self.percepts = self.model.do(self, self.action)
    
    def step(self):
        self.step_agent()


class GreenAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id)
        self.max_radioactivity = 1/3
        
    def percept(self):
        pass
    
    def deliberate_i(self, knowledge):
        # If carrying 1 Yellow Waste
        if len(knowledge["carrying"]) == 1 and knowledge["carrying"][0] == Colors.YELLOW:
            # If the agent is not at east of green zone, move right
            if self.pos[0] > 1: #TODO change this to the actual position of the green zone
                return Action.MOVE_LEFT
            else:
            # Drop the Yellow Waste
                return Action.DROP
        # If carrying 2 Green Wastes, delete them and create 1 Yellow Waste
        elif len(knowledge["carrying"]) == 2:
            return Action.FUSION
        # If there is Green Waste nearby, collect it
        elif Colors.GREEN in knowledge["Near_waste"]["C"]:
            return Action.COLLECT
        # If there is no Green Waste at the center, random move
        else:
            return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])
        
    def deliberate(self, knowledge):
        return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])


class YellowAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id)
        self.max_radioactivity = 2/3
        
    def percept(self):
        pass
    
    def deliberate_i(self, knowledge):
        # If carrying 1 Red waste
        if len(knowledge["carrying"]) == 1 and knowledge["carrying"][0] == Colors.RED:
            # If the agent is not at the east of yellow zone, move right
            if self.pos[0] > 1: #TODO change this to the correct position
                return Action.MOVE_LEFT
            else:
            # Drop the Red Waste
                return Action.DROP
        # If carrying 2 Yellow Wastes, delete them and create 1 Yellow Waste
        elif len(knowledge["carrying"]) == 2:
            return Action.FUSION
        # If there is Green Waste nearby, collect it
        elif Colors.YELLOW in knowledge["Near_waste"]["C"]:
            return Action.COLLECT
        # If there is no Green Waste at the center, random move
        else:
            return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])
        
    def deliberate(self, knowledge):
        return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])

class RedAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id)
        self.max_radioactivity = 1
    def percept(self):
        pass
    def deliberate_i(self, knowledge):
        # If carrying 1 Red waste
        if len(knowledge["carrying"]) == 1 and knowledge["carrying"][0] == Colors.RED:
            # If the agent is not at the east of yellow zone, move right
            if not isinstance(WasteDisposalAgent , knowledge["Near_Waste"]["C"])  : #TODO change this to the correct position
                return Action.MOVE_LEFT
            else:
            # Drop the Red Waste in the dustbin
                return Action.DROP
        # If there is Red Waste nearby, collect it
        elif Colors.RED in knowledge["Near_waste"]["C"]:
            return Action.COLLECT
        # If there is no Green Waste at the center, random move
        else:
            return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])
        
    def deliberate(self, knowledge):
        return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])
