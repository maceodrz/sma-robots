from mesa import Agent
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
    DO_NOTHING = 7
    
    
    
class AgentMode(Enum):
    SEEKING = 0
    CARRYING = 1
    CARRYING_AND_SEEKING_WASTE_UP = 2
    CARRYING_AND_SEEKING_WASTE_DOWN = 3


class Robot(Agent):
    def __init__(self, model, unique_id, color = None, max_radioactivity = None ):
        super().__init__(model)
        self.percepts = {}
        
        self.knowledge = {"Neighbors": [], "carrying": [], "LastActionWorked": True}
        self.unique_id = unique_id
        self.action = None
        self.color = color
        self.max_radioactivity = max_radioactivity
        self.model = model
        self.color = None
        self.mode = AgentMode.SEEKING

    def percept(self):
        self.knowledge["Neighbors"] = list(
            self.model.grid.get_neighbors(
                self.pos, moore=True, include_center=True, radius=1
            )
        )
        return self.knowledge
    
    def check_possible_directions(self):
        possible_moves = [Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN]

        # Check if there is no neighbor more to the left
        if not any(neighbor.pos[0] < self.pos[0] for neighbor in self.knowledge["Neighbors"]):
            possible_moves.remove(Action.MOVE_LEFT)

        # Check if there is no neighbor more to the right
        if not any(neighbor.pos[0] > self.pos[0] for neighbor in self.knowledge["Neighbors"]):
            possible_moves.remove(Action.MOVE_RIGHT)

        # Check if there is no neighbor more above
        if not any(neighbor.pos[1] < self.pos[1] for neighbor in self.knowledge["Neighbors"]):
            possible_moves.remove(Action.MOVE_UP)

        # Check if there is no neighbor more below
        if not any(neighbor.pos[1] > self.pos[1] for neighbor in self.knowledge["Neighbors"]):
            possible_moves.remove(Action.MOVE_DOWN)
        
        # Check if there is a neighbor with too much radioactivity
        if any(isinstance(neighbor, RadioactivityAgent) and getattr(neighbor, 'radioactivity', 0) > self.max_radioactivity for neighbor in self.knowledge["Neighbors"]):
            possible_moves.remove(Action.MOVE_RIGHT)
        return possible_moves
    
    def check_equivalent_waste(self):
        if len(self.knowledge["carrying"]) == 2 or len(self.knowledge["carrying"]) == 1 and self.color == Colors.RED :
            self.mode = AgentMode.CARRYING
            return Action.FUSION
        # First, check if there is a waste in its neighbors
        for neighbor in self.knowledge["Neighbors"]:
            if isinstance(neighbor, WasteAgent) and neighbor.color == self.color:
                # If the waste is at the agent's position, collect it
                if neighbor.pos == self.pos:
                    return Action.COLLECT
                # Otherwise, move towards the waste
                else:
                    # Determine direction based on relative position
                    waste_x, waste_y = neighbor.pos
                    agent_x, agent_y = self.pos
                    # Move towards the waste based on relative position
                    if waste_x != agent_x:
                        return Action.MOVE_LEFT if waste_x < agent_x else Action.MOVE_RIGHT
                    elif waste_y != agent_y:
                        return Action.MOVE_UP if waste_y < agent_y else Action.MOVE_DOWN
        return None

    def deliberate_seeking(self):
        action =  self.check_equivalent_waste()
        if action is not None:
            return action

        # If there is no Waste besides, random move if possible :
        # Exclusion of impossible moves : 
        possible_moves = self.check_possible_directions()
        if possible_moves:
            return random.choice(possible_moves)
        return Action.Do_NOTHING # Default action if no possible moves are available
        
            
    
    def DeliberateCarrying(self):
        if any( isinstance(RadioactivityAgent, neighbor) and neighbor.radioactivity > self.max_radioactivity for neighbor in self.knowledge["Neighbors"]):
            self.mode = AgentMode.SEEKING
            return Action.DROP
        else:
            return Action.MOVE_RIGHT
    
    def DeliberateCarryingAndSeekingWaste(self):
        pass
    
    def deliberate(self):
        match self.mode:
            case AgentMode.SEEKING:
                return self.deliberate_seeking()
            case AgentMode.CARRYING:
                return self.DeliberateCarrying()
            case AgentMode.CARRYING_AND_SEEKING_WASTE_UP:
                return self.DeliberateCarryingAndSeekingWaste()
            case AgentMode.CARRYING_AND_SEEKING_WASTE_DOWN:
                return self.DeliberateCarryingAndSeekingWaste()
            case _:
            # Default case if none of the above match
                return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])

    def step_agent(self):
        self.knowledge = self.percept()
        self.action = self.deliberate()
        self.percepts = self.model.do(self, self.action)

    def step(self):
        self.step_agent()


class GreenAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id, color=Colors.GREEN, max_radioactivity = 1/3)
        self.model = model

    # def deliberate(self, knowledge):
    #    return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])


class YellowAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id)
        self.max_radioactivity = 2 / 3
        self.color = Colors.YELLOW


    # def deliberate(self, knowledge):
    #    return random.choice([Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN])


class RedAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id)
        self.max_radioactivity = 1
        self.color = Colors.RED
        


    def DeliberateCarrying(self):
        # Check if any of the neighbors are radioactivity agents that exceed the agent's tolerance
        radioactivity_neighbors = [neighbor for neighbor in self.knowledge["Neighbors"] if isinstance(neighbor, RadioactivityAgent)]
        if len(radioactivity_neighbors) <= 6:
            self.mode = AgentMode.CARRYING_AND_SEEKING_WASTE_UP
        return Action.MOVE_RIGHT
    
    def DeliberateCarryingAndSeekingWaste(self):
        if any( (isinstance(neighbor, WasteDisposalAgent) and neighbor.pos == self.pos) for neighbor in self.knowledge["Neighbors"] ) :
            self.mode = AgentMode.SEEKING
            return Action.DROP
        radioactivity_neighbors = [neighbor for neighbor in self.knowledge["Neighbors"] if isinstance(neighbor, RadioactivityAgent)]
        if self.mode == AgentMode.CARRYING_AND_SEEKING_WASTE_UP and len(radioactivity_neighbors) > 4:
            return Action.MOVE_UP
        else:
            self.mode = AgentMode.CARRYING_AND_SEEKING_WASTE_DOWN
            return Action.MOVE_DOWN

    