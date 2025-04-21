# Strategy.py contains various strategies for waste collection agents

import random
from objects import WasteAgent, RadioactivityAgent, WasteDisposalAgent, Colors
from enum import Enum
from communication.message.MessagePerformative import MessagePerformative
from communication.message.Message import Message


# Enum representing different modes for the RandomStrategy agent
class AgentModeRandom(Enum):
    SEEKING = 0        # Looking for waste
    CARRYING = 1       # Carrying waste and moving to disposal
    CARRYING_AND_SEEKING_WASTE_UP = 2    # Carrying waste and moving up to find disposal
    CARRYING_AND_SEEKING_WASTE_DOWN = 3  # Carrying waste and moving down to find disposal


# Enum representing different modes for the FusionAndResearch strategy agent
class AgentModeFusionAndResearch(Enum):
    FUSION = 0         # Fusing waste
    CARRYING = 1       # Carrying waste
    RESEARCHING_TOP = 2    # Exploring the top area
    RESEARCHING_DOWN = 3   # Exploring the bottom area
    PLACING_FUSION = 4     # Positioning for fusion
    PLACING_TOP = 5        # Positioning at the top
    PLACING_DOWN = 6       # Positioning at the bottom
    REDSEEKING = 7         # Red agent seeking waste


# Enum representing possible actions an agent can take
class Action(Enum):
    COLLECT = 0        # Collect waste
    FUSION = 1         # Fuse collected waste
    MOVE_LEFT = 2      # Move left
    MOVE_RIGHT = 3     # Move right
    MOVE_UP = 4        # Move up
    MOVE_DOWN = 5      # Move down
    DROP = 6           # Drop carried waste
    DO_NOTHING = 7     # Do nothing


# Base Strategy class that other strategies inherit from
class Strategy:
    def __init__(self, model, agent):
        self.model = model
        self.agent = agent
        self.action = None
        self.mode = None
        self.percepts = {}

    # Determines which directions the agent can move in based on its surroundings
    def check_possible_directions(self):
        possible_moves = [
            Action.MOVE_LEFT,
            Action.MOVE_RIGHT,
            Action.MOVE_UP,
            Action.MOVE_DOWN,
        ]

        # Remove directions if there's no neighbor in that direction
        if not any(
            neighbor.pos[0] < self.agent.pos[0]
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_LEFT)

        if not any(
            neighbor.pos[0] > self.agent.pos[0]
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_RIGHT)

        if not any(
            neighbor.pos[1] > self.agent.pos[1]
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_UP)

        if not any(
            neighbor.pos[1] < self.agent.pos[1]
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_DOWN)

        # Don't move right if there's too much radioactivity
        if any(
            isinstance(neighbor, RadioactivityAgent)
            and getattr(neighbor, "radioactivity", 0) > self.agent.max_radioactivity
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_RIGHT)

        # Red/Yellow agents shouldn't go deep into the yellow zone
        if (self.agent.color in [Colors.RED, Colors.YELLOW]) and any(
            isinstance(neighbor, RadioactivityAgent)
            and neighbor.pos == self.agent.pos
            and neighbor.radioactivity <= self.agent.max_radioactivity - 1 / 3
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            if Action.MOVE_LEFT in possible_moves:
                possible_moves.remove(Action.MOVE_LEFT)
        return possible_moves

    # Abstract method to be implemented by subclasses
    def deliberate(self):
        pass


# A strategy that makes random decisions
class StrategyRandom(Strategy):
    def __init__(self, model, agent):
        super().__init__(model, agent)
        self.mode = AgentModeRandom.SEEKING

    # Checks for equivalent waste nearby to collect or move towards
    def check_equivalent_waste(self):
        # Check if agent has enough waste to fuse
        if len(self.agent.knowledge["carrying"]) == 2 or (
            len(self.agent.knowledge["carrying"]) == 1
            and self.agent.color == Colors.RED
        ):
            self.mode = AgentModeRandom.CARRYING
            return Action.FUSION
            
        # Look for waste in neighboring cells
        for neighbor in self.agent.knowledge["Neighbors"]:
            if isinstance(neighbor, WasteAgent) and neighbor.color == self.agent.color:
                # Collect waste at the agent's position if not recently dropped
                if neighbor.pos == self.agent.pos and (
                    self.agent.knowledge["DroppedLast"] is None
                    or neighbor != self.agent.knowledge["DroppedLast"][0]
                ):
                    return Action.COLLECT
                # Move towards waste otherwise
                elif (
                    neighbor != self.agent.knowledge["DroppedLast"] is None
                    or neighbor != self.agent.knowledge["DroppedLast"][0]
                ):
                    waste_x, waste_y = neighbor.pos
                    agent_x, agent_y = self.agent.pos
                    if waste_x != agent_x:
                        return (
                            Action.MOVE_LEFT if waste_x < agent_x else Action.MOVE_RIGHT
                        )
                    elif waste_y != agent_y:
                        return Action.MOVE_UP if waste_y > agent_y else Action.MOVE_DOWN
        return None

    # Decision making when in seeking mode
    def deliberate_seeking(self):
        # Sometimes drop carried waste if not a red agent
        if (
            len(self.agent.knowledge["carrying"]) == 1
            and self.agent.color != Colors.RED
            and random.random() < 0.05
        ):
            self.agent.knowledge["DroppedLast"] = [
                self.agent.knowledge["carrying"][0],
                10,
            ]
            return Action.DROP

        # Check for waste to collect
        action = self.check_equivalent_waste()
        if action is not None:
            return action

        # Move randomly if no waste found
        possible_moves = self.check_possible_directions()
        if possible_moves:
            return random.choice(possible_moves)
        return Action.DO_NOTHING

    # Decision making when carrying waste
    def DeliberateCarrying(self):
        # Switch to seeking if not carrying anything
        if len(self.agent.knowledge["carrying"]) == 0:
            self.mode = AgentModeRandom.SEEKING
            return Action.DO_NOTHING
            
        if self.agent.color == Colors.RED:
            # If right movement failed, switch to seeking waste up
            if (self.agent.knowledge["LastActionNotWorked"] == Action.MOVE_RIGHT):
                self.mode = AgentModeRandom.CARRYING_AND_SEEKING_WASTE_UP
            return Action.MOVE_RIGHT
        else:
            # Drop waste if radioactivity is too high
            if any(
                isinstance(neighbor, RadioactivityAgent)
                and neighbor.radioactivity > self.agent.max_radioactivity
                for neighbor in self.agent.knowledge["Neighbors"]
            ):
                self.mode = AgentModeRandom.SEEKING
                return Action.DROP
            else:
                return Action.MOVE_RIGHT

    # Decision making when carrying waste and seeking waste disposal
    def DeliberateCarryingAndSeekingWaste(self):
        if self.agent.color == Colors.RED:
            # Drop waste if at disposal point
            if any(
                (
                    isinstance(neighbor, WasteDisposalAgent)
                    and neighbor.pos == self.agent.pos
                )
                for neighbor in self.agent.knowledge["Neighbors"]
            ):
                self.mode = AgentModeRandom.SEEKING
                return Action.DROP
                
            # Navigate up or down to find waste disposal
            if (
                not self.agent.knowledge["LastActionNotWorked"] == Action.MOVE_UP
                and self.mode != AgentModeRandom.CARRYING_AND_SEEKING_WASTE_DOWN
            ):
                return Action.MOVE_UP
            else:
                self.mode = AgentModeRandom.CARRYING_AND_SEEKING_WASTE_DOWN
                return Action.MOVE_DOWN

    # Main deliberation method that delegates to appropriate sub-method
    def deliberate(self):
        match self.mode:
            case AgentModeRandom.SEEKING:
                return self.deliberate_seeking()
            case AgentModeRandom.CARRYING:
                return self.DeliberateCarrying()
            case AgentModeRandom.CARRYING_AND_SEEKING_WASTE_UP:
                return self.DeliberateCarryingAndSeekingWaste()
            case AgentModeRandom.CARRYING_AND_SEEKING_WASTE_DOWN:
                return self.DeliberateCarryingAndSeekingWaste()
            case _:
                # Default random movement
                return random.choice(
                    [
                        Action.MOVE_LEFT,
                        Action.MOVE_RIGHT,
                        Action.MOVE_UP,
                        Action.MOVE_DOWN,
                    ]
                )


# Strategy that focuses on fusion and exploration
class FusionAndResearch(Strategy):
    def __init__(self, model, agent):
        super().__init__(model, agent)

        # Assign agent role based on whether it's first of its color
        if not model.first_of_color[agent.color]:
            model.first_of_color[agent.color] = True
            self.agent_type = AgentModeFusionAndResearch.PLACING_FUSION
        else:
            # Alternate between top and bottom explorers
            self.agent_type = (
                AgentModeFusionAndResearch.PLACING_TOP
                if agent.unique_id % 2 == 0
                else AgentModeFusionAndResearch.PLACING_DOWN
            )
        self.mode = self.agent_type
        self.finished_fusion = False

    def deliberate_fusion(self):
        if len(self.agent.knowledge["carrying"]) == 2 and not self.agent.color == Colors.RED:
            return Action.FUSION
        elif (
            len(self.agent.knowledge["carrying"]) == 1
            and self.agent.color + 1 == self.agent.knowledge["carrying"][0].color
        ):
            return Action.DROP
        
        # Special handling for red agents at disposal sites
        elif self.agent.color == Colors.RED and len(self.agent.knowledge["carrying"]) > 0 and any(
                (
                    isinstance(neighbor, WasteDisposalAgent)
                    and neighbor.pos == self.agent.pos
                )
                for neighbor in self.agent.knowledge["Neighbors"]
            ):
            return Action.DROP
        
        # Collect waste of matching color
        elif len(self.agent.knowledge["carrying"]) <= 1 and any(
            isinstance(others, WasteAgent)
            and others.color == self.agent.color
            and others.pos == self.agent.pos
            and others not in self.agent.knowledge["carrying"]
            for others in self.agent.knowledge["Neighbors"]
        ):
            return Action.COLLECT
        
        # Navigation with position tracking
        possible_directions = self.check_possible_directions()
        if Action.MOVE_DOWN not in possible_directions:
            if self.agent.knowledge["y"] is None:
                self.agent.knowledge["y"] = 1
            return Action.MOVE_UP

        elif Action.MOVE_UP not in possible_directions:
            if self.agent.knowledge["y"] is None:
                self.agent.knowledge["y"] = -1
            elif self.agent.knowledge["height"] is None:
                # Calculate map height when reaching the top
                if self.agent.knowledge["y"] > 0:
                    self.agent.knowledge["height"] = self.agent.knowledge["y"] - 1
                    self.agent.knowledge["y"] = 0
                else:
                    self.agent.knowledge["height"] = self.agent.knowledge["y"] + 1
                    self.agent.knowledge["y"] = self.agent.knowledge["height"]

            return Action.MOVE_DOWN

        else:
            for action in reversed(self.agent.knowledge["LastAction"]):
                if action not in [Action.COLLECT, Action.FUSION, Action.DROP]:
                    return action


    # Decision making when carrying waste
    def deliberate_carrying(self):
        # Return to placing mode if not carrying waste
        if (
            len(self.agent.knowledge["carrying"]) == 0
            and self.agent_type == AgentModeFusionAndResearch.PLACING_FUSION
        ):
            self.mode = AgentModeFusionAndResearch.PLACING_FUSION
            return Action.DO_NOTHING

        # Collect additional waste if possible
        if (
            self.agent.knowledge["carrying"][0].color == self.agent.color
            and any(
                isinstance(neighbor, WasteAgent)
                and neighbor.color == self.agent.color
                and neighbor.pos == self.agent.pos
                for neighbor in self.agent.knowledge["Neighbors"]
            )
            and self.agent.color != Colors.RED
        ):
            return Action.COLLECT
        # Fuse if carrying two pieces of waste
        elif len(self.agent.knowledge["carrying"]) == 2 and not self.agent.color == Colors.RED:
            return Action.FUSION
        # Drop waste if radioactivity is too high
        possible_directions = self.check_possible_directions()
        if Action.MOVE_RIGHT not in possible_directions:
            match self.agent_type:
                case AgentModeFusionAndResearch.PLACING_TOP:
                    self.mode = AgentModeFusionAndResearch.RESEARCHING_TOP
                case AgentModeFusionAndResearch.PLACING_DOWN:
                    self.mode = AgentModeFusionAndResearch.RESEARCHING_DOWN
            return Action.DROP

        # Move right by default
        return Action.MOVE_RIGHT

    # Decision making for exploration mode
    def deliberate_research(self, top_or_down):
        # Move left after dropping waste
        if self.agent.knowledge["LastAction"][-1] == Action.DROP:
            return Action.MOVE_LEFT
        # Switch to carrying mode if waste collected
        elif len(self.agent.knowledge["carrying"]) > 0:
            self.mode = AgentModeFusionAndResearch.CARRYING
            return Action.MOVE_RIGHT
        # Collect waste if found
        elif any(
            isinstance(neighbor, WasteAgent)
            and neighbor.color == self.agent.color
            and neighbor.pos == self.agent.pos
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            self.mode = AgentModeFusionAndResearch.CARRYING
            return Action.COLLECT
            
        possible_moves = self.check_possible_directions()

        # Movement logic during exploration
        if self.agent.knowledge["LastAction"][-1] == top_or_down["Top or Down"]:
            if Action.MOVE_LEFT in possible_moves:
                return Action.MOVE_LEFT
            else:
                return Action.MOVE_RIGHT
        # Switch exploration direction if blocked
        elif top_or_down["Top or Down"] not in possible_moves and (
            Action.MOVE_LEFT not in possible_moves
            or Action.MOVE_RIGHT not in possible_moves
        ):
            self.mode = top_or_down["Change Mode"]
            return top_or_down["Down or Top"]
        # Continue in current direction if partly blocked
        elif (
            Action.MOVE_LEFT not in possible_moves
            or Action.MOVE_RIGHT not in possible_moves
        ):
            return top_or_down["Top or Down"]
        else:
            return self.agent.knowledge["LastAction"][-1]

    # Decision making for red agents seeking waste
    def deliberate_red_seeking(self):
        if len(self.agent.knowledge["carrying"]) > 0:
            self.mode = AgentModeFusionAndResearch.CARRYING
            return Action.MOVE_RIGHT
        if any(
            isinstance(neighbor, WasteAgent)
            and neighbor.color == self.agent.color
            and neighbor.pos == self.agent.pos
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            self.mode = AgentModeFusionAndResearch.CARRYING
            return Action.COLLECT
            
        possible_moves = self.check_possible_directions()
        # Prioritize moving left
        if Action.MOVE_LEFT in possible_moves:
            return Action.MOVE_LEFT
        # Change direction if blocked
        elif self.agent.knowledge["LastAction"][-1] == Action.MOVE_LEFT:
            return random.choice([Action.MOVE_UP, Action.MOVE_DOWN])
        # Navigation when certain directions are blocked
        elif Action.MOVE_DOWN not in possible_moves:
            return Action.MOVE_UP
        elif Action.MOVE_UP not in possible_moves:
            return Action.MOVE_DOWN
        else:
            return self.agent.knowledge["LastAction"][-1]

    # Decision making for placing agents in position
    def deliberate_placing(self, action):
        # Collect waste if available
        if len(self.agent.knowledge["carrying"]) <= 1 and any(
            isinstance(neighbor, WasteAgent)
            and neighbor.color == self.agent.color
            and neighbor.pos == self.agent.pos
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            return Action.COLLECT
            
        possible_moves = self.check_possible_directions()
        # Continue in desired direction if possible
        if action in possible_moves:
            return action
        else:
            # Switch modes if blocked
            match action:
                case Action.MOVE_RIGHT:
                    self.mode = AgentModeFusionAndResearch.FUSION
                    return Action.MOVE_UP
                case Action.MOVE_UP:
                    self.mode = AgentModeFusionAndResearch.RESEARCHING_TOP
                    return Action.MOVE_LEFT
                case Action.MOVE_DOWN:
                    self.mode = AgentModeFusionAndResearch.RESEARCHING_DOWN
                    return Action.MOVE_LEFT
                case Action.MOVE_LEFT:
                    self.mode = AgentModeFusionAndResearch.FUSION
                    return Action.MOVE_UP

    # Main deliberation method that delegates to appropriate sub-method
    def deliberate(self):
        match self.mode:
            case AgentModeFusionAndResearch.FUSION:
                if self.finished_fusion:
                    return self.deliberate_red_seeking()
                return self.deliberate_fusion()
            case AgentModeFusionAndResearch.CARRYING:
                return self.deliberate_carrying()
            case AgentModeFusionAndResearch.RESEARCHING_TOP:
                return self.deliberate_research(
                    {
                        "Top or Down": Action.MOVE_DOWN,
                        "Down or Top": Action.MOVE_UP,
                        "Change Mode": AgentModeFusionAndResearch.RESEARCHING_DOWN,
                    }
                )
            case AgentModeFusionAndResearch.RESEARCHING_DOWN:
                return self.deliberate_research(
                    {
                        "Top or Down": Action.MOVE_UP,
                        "Down or Top": Action.MOVE_DOWN,
                        "Change Mode": AgentModeFusionAndResearch.RESEARCHING_TOP,
                    }
                )
            case AgentModeFusionAndResearch.PLACING_FUSION:
                return self.deliberate_placing(Action.MOVE_RIGHT)
            case AgentModeFusionAndResearch.PLACING_TOP:
                return self.deliberate_placing(Action.MOVE_UP)
            case AgentModeFusionAndResearch.PLACING_DOWN:
                return self.deliberate_placing(Action.MOVE_DOWN)
            case _:
                # Default random movement
                return random.choice(
                    [
                        Action.MOVE_LEFT,
                        Action.MOVE_RIGHT,
                        Action.MOVE_UP,
                        Action.MOVE_DOWN,
                    ]
                )


# Enhanced strategy that adds communication between agents
class FusionAndResearchWithCommunication(FusionAndResearch):
    # Handle communication between agents
    def communicate(self):
        # Send identification messages to agents in same row
        for others in self.agent.knowledge["Neighbors"]:
            if isinstance(others, type(self.agent)) and others != self.agent and self.agent_type != AgentModeFusionAndResearch.PLACING_FUSION and self.mode not in [AgentModeFusionAndResearch.PLACING_TOP, AgentModeFusionAndResearch.PLACING_DOWN] and others.pos[1] == self.agent.pos[1] and not self.finished_fusion:
                self.agent.send_message(
                    Message(
                        self.agent.get_name(),
                        others.get_name(),
                        MessagePerformative.QUERY_REF,
                        {"Message Type": "Identification",
                        "Agent Type": self.agent_type,
                        "Color": self.agent.color},
                    )
                )
                
        list_messages = self.agent.get_new_messages()

        for message in list_messages:
            # Handle identification queries
            if message.get_performative() == MessagePerformative.QUERY_REF:
                if ( 
                    message.get_content()["Message Type"] == "Identification"
                    and self.agent_type != AgentModeFusionAndResearch.PLACING_FUSION 
                    and message.get_content()["Color"] == self.agent.color
                    and message.get_content()["Agent Type"] != self.agent_type
                ):
                    # Notify other agent that exploration is complete
                    for others in self.model.agents:
                        if (
                            isinstance(others, type(self.agent))
                            and self.agent.color == others.color
                        ):
                            self.agent.send_message(
                                Message(
                                    self.agent.get_name(),
                                    message.get_exp(),
                                    MessagePerformative.INFORM_REF,
                                    "Fin d'exploration",
                                )
                            )
            # Handle end of exploration notifications
            if message.get_performative() == MessagePerformative.INFORM_REF:
                if message.get_content() == "Fin d'exploration" and self.agent_type != AgentModeFusionAndResearch.PLACING_FUSION:
                    self.mode = AgentModeFusionAndResearch.FUSION
                    self.finished_fusion = True

    # Enhanced version of placing deliberation
    def deliberate_placing(self, action):
        if len(self.agent.knowledge["carrying"]) <= 1 and any(
            isinstance(neighbor, WasteAgent)
            and neighbor.color == self.agent.color
            and neighbor.pos == self.agent.pos
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            return Action.COLLECT
        possible_moves = self.check_possible_directions()
        if action in possible_moves:
            return action
        else:
            # Handle transitions between modes with tracking of position
            match action:
                case Action.MOVE_RIGHT:
                    self.mode = AgentModeFusionAndResearch.FUSION
                    return Action.MOVE_UP
                case Action.MOVE_UP:
                    self.agent.knowledge["y"] = -1  # Track y position
                    self.mode = AgentModeFusionAndResearch.RESEARCHING_TOP
                    return Action.MOVE_RIGHT
                case Action.MOVE_DOWN:
                    self.agent.knowledge["y"] = 1   # Track y position
                    self.mode = AgentModeFusionAndResearch.RESEARCHING_DOWN
                    return Action.MOVE_RIGHT
                case Action.MOVE_LEFT:
                    self.mode = AgentModeFusionAndResearch.FUSION
                    return Action.MOVE_UP

    # Enhanced research deliberation with position tracking
    def deliberate_research(self, top_or_down):
        if self.agent.knowledge["LastAction"][-1] == Action.DROP:
            return Action.MOVE_LEFT

        elif len(self.agent.knowledge["carrying"]) > 0:
            self.mode = AgentModeFusionAndResearch.CARRYING
            return Action.MOVE_RIGHT

        elif any(
            isinstance(neighbor, WasteAgent)
            and neighbor.color == self.agent.color
            and neighbor.pos == self.agent.pos
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            self.mode = AgentModeFusionAndResearch.CARRYING
            return Action.COLLECT
            
        possible_moves = self.check_possible_directions()

        # Track x position when reaching edge
        if (
            self.agent.knowledge["x"] is None
            and Action.MOVE_RIGHT not in possible_moves
        ):
            self.agent.knowledge["x"] = 0
            return Action.MOVE_LEFT

        # Navigation logic with position tracking
        if self.agent.knowledge["LastAction"][-1] == top_or_down["Top or Down"]:
            if Action.MOVE_LEFT in possible_moves:
                return Action.MOVE_LEFT
            else:
                return Action.MOVE_RIGHT

        elif top_or_down["Top or Down"] not in possible_moves and (
            Action.MOVE_LEFT not in possible_moves
            or Action.MOVE_RIGHT not in possible_moves
        ):
            self.mode = top_or_down["Change Mode"]
            return top_or_down["Down or Top"]

        elif (
            Action.MOVE_LEFT not in possible_moves
            or Action.MOVE_RIGHT not in possible_moves
        ):
            # Track rows that have been checked
            if self.agent.knowledge["x"] != 0:
                self.agent.knowledge["checked_rows"].append(self.agent.knowledge["y"])
            return top_or_down["Top or Down"]
        else:
            return self.agent.knowledge["LastAction"][-1]

    # Enhanced fusion deliberation with support for red agents
    def deliberate_fusion(self):
        if len(self.agent.knowledge["carrying"]) == 2 and not self.agent.color == Colors.RED:
            return Action.FUSION
        elif (
            len(self.agent.knowledge["carrying"]) == 1
            and self.agent.color + 1 == self.agent.knowledge["carrying"][0].color
        ):
            return Action.DROP
        
        # Special handling for red agents at disposal sites
        elif self.agent.color == Colors.RED and len(self.agent.knowledge["carrying"]) > 0 and any(
                (
                    isinstance(neighbor, WasteDisposalAgent)
                    and neighbor.pos == self.agent.pos
                )
                for neighbor in self.agent.knowledge["Neighbors"]
            ):
            return Action.DROP
        
        # Collect waste of matching color
        elif len(self.agent.knowledge["carrying"]) <= 1 and any(
            isinstance(others, WasteAgent)
            and others.color == self.agent.color
            and others.pos == self.agent.pos
            and others not in self.agent.knowledge["carrying"]
            for others in self.agent.knowledge["Neighbors"]
        ):
            return Action.COLLECT
        
        # Navigation with position tracking
        possible_directions = self.check_possible_directions()
        if Action.MOVE_DOWN not in possible_directions:
            if self.agent.knowledge["y"] is None:
                self.agent.knowledge["y"] = 1
            return Action.MOVE_UP

        elif Action.MOVE_UP not in possible_directions:
            if self.agent.knowledge["y"] is None:
                self.agent.knowledge["y"] = -1
            elif self.agent.knowledge["height"] is None:
                # Calculate map height when reaching the top
                if self.agent.knowledge["y"] > 0:
                    self.agent.knowledge["height"] = self.agent.knowledge["y"] - 1
                    self.agent.knowledge["y"] = 0
                else:
                    self.agent.knowledge["height"] = self.agent.knowledge["y"] + 1
                    self.agent.knowledge["y"] = self.agent.knowledge["height"]

            return Action.MOVE_DOWN

        else:
            for action in reversed(self.agent.knowledge["LastAction"]):
                if action not in [Action.COLLECT, Action.FUSION, Action.DROP]:
                    return action

    # Main deliberation method with communication
    def deliberate(self):
        self.communicate()  # Process communication before deciding action
        match self.mode:
            case AgentModeFusionAndResearch.FUSION:
                if self.finished_fusion:
                    return self.deliberate_red_seeking()
                return self.deliberate_fusion()
            case AgentModeFusionAndResearch.CARRYING:
                return self.deliberate_carrying()
            case AgentModeFusionAndResearch.RESEARCHING_TOP:
                if self.finished_fusion:
                    return self.deliberate_red_seeking()
                return self.deliberate_research(
                    {
                        "Top or Down": Action.MOVE_DOWN,
                        "Down or Top": Action.MOVE_UP,
                        "Change Mode": AgentModeFusionAndResearch.RESEARCHING_DOWN,
                    }
                )
            case AgentModeFusionAndResearch.RESEARCHING_DOWN:
                if self.finished_fusion:
                    return self.deliberate_red_seeking()
                return self.deliberate_research(
                    {
                        "Top or Down": Action.MOVE_UP,
                        "Down or Top": Action.MOVE_DOWN,
                        "Change Mode": AgentModeFusionAndResearch.RESEARCHING_TOP,
                    }
                )
            case AgentModeFusionAndResearch.PLACING_FUSION:
                return self.deliberate_placing(Action.MOVE_RIGHT)
            case AgentModeFusionAndResearch.PLACING_TOP:
                return self.deliberate_placing(Action.MOVE_UP)
            case AgentModeFusionAndResearch.PLACING_DOWN:
                return self.deliberate_placing(Action.MOVE_DOWN)
            case _:
                # Default random movement
                return random.choice(
                    [
                        Action.MOVE_LEFT,
                        Action.MOVE_RIGHT,
                        Action.MOVE_UP,
                        Action.MOVE_DOWN,
                    ]
                )
