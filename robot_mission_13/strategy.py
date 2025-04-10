import random
from objects import WasteAgent, RadioactivityAgent, WasteDisposalAgent, Colors
from enum import Enum

class AgentMode(Enum):
    SEEKING = 0
    CARRYING = 1
    CARRYING_AND_SEEKING_WASTE_UP = 2
    CARRYING_AND_SEEKING_WASTE_DOWN = 3
    
class Action(Enum):
    COLLECT = 0
    FUSION = 1
    MOVE_LEFT = 2
    MOVE_RIGHT = 3
    MOVE_UP = 4
    MOVE_DOWN = 5
    DROP = 6
    DO_NOTHING = 7

class Strategy:
    def __init__(self, model, agent):
        self.model = model
        self.agent = agent
        self.action = None
        self.mode = AgentMode.SEEKING
        self.percepts = {}

    def check_possible_directions(self):
        possible_moves = [
            Action.MOVE_LEFT,
            Action.MOVE_RIGHT,
            Action.MOVE_UP,
            Action.MOVE_DOWN,
        ]

        # Check if there is no neighbor more to the left
        if not any(
            neighbor.pos[0] < self.agent.pos[0] for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_LEFT)

        # Check if there is no neighbor more to the right
        if not any(
            neighbor.pos[0] > self.agent.pos[0] for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_RIGHT)

        # Check if there is no neighbor more above
        if not any(
            neighbor.pos[1] > self.agent.pos[1] for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_UP)

        # Check if there is no neighbor more below
        if not any(
            neighbor.pos[1] < self.agent.pos[1] for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_DOWN)

        # Check if there is a neighbor with too much radioactivity
        if any(
            isinstance(neighbor, RadioactivityAgent)
            and getattr(neighbor, "radioactivity", 0) > self.agent.max_radioactivity
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_RIGHT)
        
        #If I am a red/Yellow agent, I don't want to go further than one step in the yellow zone
        if (self.agent.color in [ Colors.RED, Colors.YELLOW ]) and any(
            isinstance(neighbor, RadioactivityAgent)
            and neighbor.pos == self.agent.pos
            and neighbor.radioactivity <= self.agent.max_radioactivity - 1/3
            for neighbor in self.agent.knowledge["Neighbors"]
            ):
            possible_moves.remove(Action.MOVE_LEFT)
        return possible_moves

    def deliberate(self):
        pass


class StrategyRandom(Strategy):
    def check_equivalent_waste(self):
        if len(self.agent.knowledge["carrying"]) == 2 or (
            len(self.agent.knowledge["carrying"]) == 1 and self.agent.color == Colors.RED
        ):
            self.mode = AgentMode.CARRYING
            return Action.FUSION
        # First, check if there is a waste in its neighbors
        for neighbor in self.agent.knowledge["Neighbors"]:
            if isinstance(neighbor, WasteAgent) and neighbor.color == self.agent.color:
                # If the waste is at the agent's position, collect it
                if neighbor.pos == self.agent.pos and (self.agent.knowledge["DroppedLast"] is None or neighbor != self.agent.knowledge["DroppedLast"][0]) :
                    return Action.COLLECT
                # Otherwise, move towards the waste
                elif neighbor != self.agent.knowledge["DroppedLast"]is None or neighbor != self.agent.knowledge["DroppedLast"][0]:
                    # Determine direction based on relative position
                    waste_x, waste_y = neighbor.pos
                    agent_x, agent_y = self.agent.pos
                    # Move towards the waste based on relative position
                    if waste_x != agent_x:
                        return (
                            Action.MOVE_LEFT if waste_x < agent_x else Action.MOVE_RIGHT
                        )
                    elif waste_y != agent_y:
                        return Action.MOVE_UP if waste_y > agent_y else Action.MOVE_DOWN
        return None

    def deliberate_seeking(self):
        if len(self.agent.knowledge["carrying"]) == 1 and self.agent.color != Colors.RED and random.random() < 0.05:
            self.agent.knowledge["DroppedLast"] = [self.agent.knowledge["carrying"][0], 10]
            return Action.DROP

        action = self.check_equivalent_waste()
        if action is not None:
            return action

        # If there is no Waste besides, random move if possible :
        # Exclusion of impossible moves :
        possible_moves = self.check_possible_directions()
        if possible_moves:
            return random.choice(possible_moves)
        return Action.DO_NOTHING  # Default action if no possible moves are available

    def DeliberateCarrying(self):
        if self.agent.color == Colors.RED:
            # Check if any of the neighbors are radioactivity agents that exceed the agent's tolerance
            if (
                self.agent.knowledge["LastActionNotWorked"] == Action.MOVE_RIGHT
            ):  # TODO faire gaffe aux frontieres haut bas
                self.mode = AgentMode.CARRYING_AND_SEEKING_WASTE_UP
            return Action.MOVE_RIGHT
        else:
            if any(
                isinstance(neighbor, RadioactivityAgent)
                and neighbor.radioactivity > self.agent.max_radioactivity
                for neighbor in self.agent.knowledge["Neighbors"]
            ):
                self.mode = AgentMode.SEEKING
                return Action.DROP
            else:
                return Action.MOVE_RIGHT

    def DeliberateCarryingAndSeekingWaste(self):
        if self.agent.color == Colors.RED:
            if any(
                (isinstance(neighbor, WasteDisposalAgent) and neighbor.pos == self.agent.pos)
                for neighbor in self.agent.knowledge["Neighbors"]
            ):
                self.mode = AgentMode.SEEKING
                return Action.DROP
            if (
                not self.agent.knowledge["LastActionNotWorked"] == Action.MOVE_UP
                and self.mode != AgentMode.CARRYING_AND_SEEKING_WASTE_DOWN
            ):
                return Action.MOVE_UP
            else:
                self.mode = AgentMode.CARRYING_AND_SEEKING_WASTE_DOWN
                return Action.MOVE_DOWN

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
                return random.choice(
                    [
                        Action.MOVE_LEFT,
                        Action.MOVE_RIGHT,
                        Action.MOVE_UP,
                        Action.MOVE_DOWN,
                    ]
                )
