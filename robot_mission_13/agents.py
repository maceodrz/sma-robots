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
        self.knowledge = {"Neighbors": [] , "carrying": [], "LastActionWorked": True}
        self.unique_id = unique_id
        self.action = None
        self.model = model
        
    def percept(self):
        self.knowledge["Neighbors"] = list(self.model.grid.get_neighbors(self.pos, moore=True, include_center=True, radius=1))
        return self.knowledge
            
            
            
    
    def deliberate(self):
        pass   
    
    def step_agent(self): 
        self.knowledge = self.percept()
        self.action = self.deliberate(self.knowledge) 
        self.percepts = self.model.do(self, self.action)
    
    def step(self):
        self.step_agent()


class GreenAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id)
        self.max_radioactivity = 1/3
        self.color = Colors.GREEN
        self.model = model
        
    
    def deliberate(self, knowledge):
        # If carrying 1 Yellow Waste
        if len(knowledge["carrying"]) == 1 and knowledge["carrying"][0] == Colors.YELLOW:
            # If the agent is not at east of green zone, move right
            if any( isinstance( RadioactivityAgent, neighbor ) for neighbor in knowledge["Neighbors"] ) : #TODO change this to the actual position of the green zone
                return Action.MOVE_LEFT
            else:
            # Drop the Yellow Waste
                return Action.DROP
        # If carrying 2 Green Wastes, delete them and create 1 Yellow Waste
        elif len(knowledge["carrying"]) == 2:
            return Action.FUSION
        
        else:
            for neighbor in knowledge["Neighbors"]:
                if isinstance(neighbor, WasteAgent) and neighbor.color == Colors.GREEN:
                    # If the waste is at the agent's position, collect it
                    if neighbor.pos == self.pos:
                        return Action.COLLECT
                    # Otherwise, move towards the waste
                    else:
                        # Determine direction based on relative position
                        waste_x, waste_y = neighbor.pos
                        agent_x, agent_y = self.pos
                        
                        # Move horizontally first
                        if waste_x < agent_x:
                            return Action.MOVE_LEFT
                        elif waste_x > agent_x:
                            return Action.MOVE_RIGHT
                        # Then move vertically
                        elif waste_y < agent_y:
                            return Action.MOVE_UP
                        elif waste_y > agent_y:
                            return Action.MOVE_DOWN
            # If there is no Green Waste at the center, random move
            return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])
        
    #def deliberate(self, knowledge):
    #    return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])


class YellowAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id)
        self.max_radioactivity = 2/3
        self.color = Colors.YELLOW
        
    def deliberate(self, knowledge):
        # If carrying 1 Red waste
        if len(knowledge["carrying"]) == 1 and knowledge["carrying"][0] == Colors.RED:
            # If the agent is not at the east of yellow zone, move right
            if self.pos[0] > 1: #TODO change this to the correct position
                return Action.MOVE_RIGHT
            else:
            # Drop the Red Waste
                return Action.DROP
        # If carrying 2 Yellow Wastes, delete them and create 1 Yellow Waste
        elif len(knowledge["carrying"]) == 2:
            return Action.FUSION
        # If there is Green Waste nearby, collect it
        # If there is no Green Waste at the center, random move
        else:
            for neighbor in knowledge["Neighbors"]:
                if isinstance(neighbor, WasteAgent) and neighbor.color == Colors.YELLOW:
                    # If the waste is at the agent's position, collect it
                    if neighbor.pos == self.pos:
                        return Action.COLLECT
                    # Otherwise, move towards the waste
                    else:
                        # Determine direction based on relative position
                        waste_x, waste_y = neighbor.pos
                        agent_x, agent_y = self.pos
                        
                        # Move horizontally first
                        if waste_x < agent_x:
                            return Action.MOVE_LEFT
                        elif waste_x > agent_x:
                            return Action.MOVE_RIGHT
                        # Then move vertically
                        elif waste_y < agent_y:
                            return Action.MOVE_UP
                        elif waste_y > agent_y:
                            return Action.MOVE_DOWN
            # If there is no Green Waste at the center, random move
            return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])
    #def deliberate(self, knowledge):
    #    return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])

class RedAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id)
        self.max_radioactivity = 1
        self.color = Colors.RED
        self.MODE = "Random" #TODO faut faire des modes en gros, en mode automate ou bieeeeeen là
    
    def deliberate(self, knowledge):
        # If carrying 1 Red waste
        if len(knowledge["carrying"]) == 1 and knowledge["carrying"][0].color == Colors.RED:
            # If the agent is not at the east of yellow zone, move right
            if not any(isinstance(neighbor, WasteDisposalAgent) and neighbor.pos == self.pos for neighbor in knowledge["Neighbors"]) and knowledge["LastActionWorked"] :
                return Action.MOVE_RIGHT
            elif not any(isinstance(neighbor, WasteDisposalAgent) and neighbor.pos == self.pos for neighbor in knowledge["Neighbors"]):
                if not knowledge["LastActionWorked"]:
                    self.TopFlag = False
                else:
                    return Action.MOVE_UP
            elif not any(isinstance(neighbor, WasteDisposalAgent) and neighbor.pos == self.pos for neighbor in knowledge["Neighbors"]):
                return Action.MOVE_DOWN
            else:
            # Drop the Red Waste in the dustbin
                return Action.DROP        
        # If there is no Green Waste at the center, random move
        else:
            for neighbor in knowledge["Neighbors"]:
                if isinstance(neighbor, WasteAgent) and neighbor.color == Colors.RED:
                    # If the waste is at the agent's position, collect it
                    if neighbor.pos == self.pos:
                        return Action.COLLECT
                    # Otherwise, move towards the waste
                    else:
                        # Determine direction based on relative position
                        waste_x, waste_y = neighbor.pos
                        agent_x, agent_y = self.pos
                        
                        # Move horizontally first
                        if waste_x < agent_x:
                            return Action.MOVE_LEFT
                        elif waste_x > agent_x:
                            return Action.MOVE_RIGHT
                        # Then move vertically
                        elif waste_y < agent_y:
                            return Action.MOVE_UP
                        elif waste_y > agent_y:
                            return Action.MOVE_DOWN
            # If there is no Green Waste at the center, random move
            return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])
        
    #def deliberate(self, knowledge):
    #    return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])
