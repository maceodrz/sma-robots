import random
from objects import WasteAgent, RadioactivityAgent, WasteDisposalAgent, Colors
from enum import Enum


class AgentModeRandom(Enum):
    SEEKING = 0
    CARRYING = 1
    CARRYING_AND_SEEKING_WASTE_UP = 2
    CARRYING_AND_SEEKING_WASTE_DOWN = 3


class AgentModeFusionAndResearch(Enum):
    FUSION = 0
    CARRYING = 1
    RESEARCHING_TOP = 2
    RESEARCHING_DOWN = 3
    PLACING_FUSION = 4
    PLACING_TOP = 5
    PLACING_DOWN = 6
    REDSEEKING = 7


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
        self.mode = None
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
            neighbor.pos[0] < self.agent.pos[0]
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_LEFT)

        # Check if there is no neighbor more to the right
        if not any(
            neighbor.pos[0] > self.agent.pos[0]
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_RIGHT)

        # Check if there is no neighbor more above
        if not any(
            neighbor.pos[1] > self.agent.pos[1]
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_UP)

        # Check if there is no neighbor more below
        if not any(
            neighbor.pos[1] < self.agent.pos[1]
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_DOWN)

        # Check if there is a neighbor with too much radioactivity
        if any(
            isinstance(neighbor, RadioactivityAgent)
            and getattr(neighbor, "radioactivity", 0) > self.agent.max_radioactivity
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            possible_moves.remove(Action.MOVE_RIGHT)

        # If I am a red/Yellow agent, I don't want to go further than one step in the yellow zone
        if (self.agent.color in [Colors.RED, Colors.YELLOW]) and any(
            isinstance(neighbor, RadioactivityAgent)
            and neighbor.pos == self.agent.pos
            and neighbor.radioactivity <= self.agent.max_radioactivity - 1 / 3
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            if Action.MOVE_LEFT in possible_moves:
                possible_moves.remove(Action.MOVE_LEFT)
        return possible_moves

    def deliberate(self):
        pass


class StrategyRandom(Strategy):
    def __init__(self, model, agent):
        super().__init__(model, agent)
        self.mode = AgentModeRandom.SEEKING
    
    
    def check_equivalent_waste(self):
        if len(self.agent.knowledge["carrying"]) == 2 or (
            len(self.agent.knowledge["carrying"]) == 1
            and self.agent.color == Colors.RED
        ):
            self.mode = AgentModeRandom.CARRYING
            return Action.FUSION
        # First, check if there is a waste in its neighbors
        for neighbor in self.agent.knowledge["Neighbors"]:
            if isinstance(neighbor, WasteAgent) and neighbor.color == self.agent.color:
                # If the waste is at the agent's position, collect it
                if neighbor.pos == self.agent.pos and (
                    self.agent.knowledge["DroppedLast"] is None
                    or neighbor != self.agent.knowledge["DroppedLast"][0]
                ):
                    return Action.COLLECT
                # Otherwise, move towards the waste
                elif (
                    neighbor != self.agent.knowledge["DroppedLast"] is None
                    or neighbor != self.agent.knowledge["DroppedLast"][0]
                ):
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
        if len(self.agent.knowledge["carrying"]) == 0:
            self.mode = AgentModeRandom.SEEKING
            return Action.DO_NOTHING
        if self.agent.color == Colors.RED:
            # Check if any of the neighbors are radioactivity agents that exceed the agent's tolerance
            if (
                self.agent.knowledge["LastActionNotWorked"] == Action.MOVE_RIGHT
            ):  # TODO faire gaffe aux frontieres haut bas
                self.mode = AgentModeRandom.CARRYING_AND_SEEKING_WASTE_UP
            return Action.MOVE_RIGHT
        else:
            if any(
                isinstance(neighbor, RadioactivityAgent)
                and neighbor.radioactivity > self.agent.max_radioactivity
                for neighbor in self.agent.knowledge["Neighbors"]
            ):
                self.mode = AgentModeRandom.SEEKING
                return Action.DROP
            else:
                return Action.MOVE_RIGHT

    def DeliberateCarryingAndSeekingWaste(self):
        if self.agent.color == Colors.RED:
            if any(
                (
                    isinstance(neighbor, WasteDisposalAgent)
                    and neighbor.pos == self.agent.pos
                )
                for neighbor in self.agent.knowledge["Neighbors"]
            ):
                self.mode = AgentModeRandom.SEEKING
                return Action.DROP
            if (
                not self.agent.knowledge["LastActionNotWorked"] == Action.MOVE_UP
                and self.mode != AgentModeRandom.CARRYING_AND_SEEKING_WASTE_DOWN
            ):
                return Action.MOVE_UP
            else:
                self.mode = AgentModeRandom.CARRYING_AND_SEEKING_WASTE_DOWN
                return Action.MOVE_DOWN

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
                # Default case if none of the above match
                return random.choice(
                    [
                        Action.MOVE_LEFT,
                        Action.MOVE_RIGHT,
                        Action.MOVE_UP,
                        Action.MOVE_DOWN,
                    ]
                )


class FusionAndResearch(Strategy):
    def __init__(self, model, agent):
        super().__init__(model, agent)
        
        if not model.first_of_color[agent.color]:
            model.first_of_color[agent.color] = True
            self.agent_type = AgentModeFusionAndResearch.PLACING_FUSION
        else:
            self.agent_type = (
                AgentModeFusionAndResearch.PLACING_TOP
                if agent.unique_id % 2 == 0
                else AgentModeFusionAndResearch.PLACING_DOWN
            )
        self.mode = self.agent_type
        

    def deliberate_fusion(self):
        
        if len(self.agent.knowledge["carrying"]) == 2:
            return Action.FUSION
        elif (
            len(self.agent.knowledge["carrying"]) == 1
            and self.agent.color + 1 == self.agent.knowledge["carrying"][0].color
        ):
            return Action.DROP
        elif any(
            isinstance(others, WasteAgent)
            and others.color == self.agent.color
            and others.pos == self.agent.pos
            and others not in self.agent.knowledge["carrying"]
            for others in self.agent.knowledge["Neighbors"]
        ):
            return Action.COLLECT
        possible_directions = self.check_possible_directions()
        if Action.MOVE_DOWN not in possible_directions:
            return Action.MOVE_UP
        
        elif Action.MOVE_UP not in possible_directions :
            return Action.MOVE_DOWN

        else:
            for action in reversed(self.agent.knowledge["LastAction"]):
                if action not in [Action.COLLECT, Action.FUSION, Action.DROP]:
                    return action

    def deliberate_carrying(self):
        if len(self.agent.knowledge["carrying"]) == 0 and self.agent_type == AgentModeFusionAndResearch.PLACING_FUSION :
            self.mode = AgentModeFusionAndResearch.PLACING_FUSION
            return Action.DO_NOTHING
        
        possible_directions = self.check_possible_directions()

        if self.agent.color == Colors.RED and self.agent.knowledge["LastAction"][-1] == Action.COLLECT:
            if Action.MOVE_RIGHT not in possible_directions:
                return random.choice([Action.MOVE_UP, Action.MOVE_DOWN])
            return Action.MOVE_RIGHT
        
        

        if self.agent.color == Colors.RED and Action.MOVE_RIGHT not in possible_directions:
            if any(
                (
                    isinstance(neighbor, WasteDisposalAgent)
                    and neighbor.pos == self.agent.pos
                )
                for neighbor in self.agent.knowledge["Neighbors"]
            ):
                match self.agent_type:
                    case AgentModeFusionAndResearch.PLACING_TOP:
                        self.mode = AgentModeFusionAndResearch.RESEARCHING_TOP
                    case AgentModeFusionAndResearch.PLACING_DOWN:
                        self.mode = AgentModeFusionAndResearch.RESEARCHING_DOWN
                    case AgentModeFusionAndResearch.PLACING_FUSION:
                        self.mode = AgentModeFusionAndResearch.FUSION
                return Action.DROP
            
            elif Action.MOVE_DOWN not in possible_directions:
                return Action.MOVE_UP
        
            elif Action.MOVE_UP not in possible_directions:
                return Action.MOVE_DOWN
            
            if self.agent.color == Colors.RED and self.agent.knowledge['LastAction'][-1] == Action.MOVE_RIGHT:
                return random.choice([Action.MOVE_UP, Action.MOVE_DOWN])

            else:
                return self.agent.knowledge["LastAction"][-1]
        
        if self.agent.knowledge["carrying"][0].color == self.agent.color and any(
            isinstance(neighbor, WasteAgent)
            and neighbor.color == self.agent.color
            and neighbor.pos == self.agent.pos
            for neighbor in self.agent.knowledge["Neighbors"]
        ) and self.agent.color != Colors.RED:
            return Action.COLLECT

        elif len(self.agent.knowledge["carrying"]) == 2:
            return Action.FUSION

        elif any(
            isinstance(neighbor, RadioactivityAgent)
            and neighbor.radioactivity > self.agent.max_radioactivity
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            match self.agent_type:
                case AgentModeFusionAndResearch.PLACING_TOP:
                    self.mode = AgentModeFusionAndResearch.RESEARCHING_TOP
                case AgentModeFusionAndResearch.PLACING_DOWN:
                    self.mode = AgentModeFusionAndResearch.RESEARCHING_DOWN
            return Action.DROP

        return Action.MOVE_RIGHT

    def deliberate_research(self, top_or_down):
        
        if self.agent.knowledge["LastAction"][-1] == Action.DROP:
            return Action.MOVE_LEFT
        
        elif len( self.agent.knowledge["carrying"]) > 0:
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
        
        if self.agent.knowledge["LastAction"][-1] == top_or_down["Top or Down"]:
            possible_moves = self.check_possible_directions()
            if Action.MOVE_LEFT in possible_moves:
                return Action.MOVE_LEFT
            else:
                return Action.MOVE_RIGHT
            
        elif top_or_down["Top or Down"] not in possible_moves and (Action.MOVE_LEFT not in possible_moves or Action.MOVE_RIGHT not in possible_moves):
            self.mode = top_or_down["Change Mode"]
            return top_or_down["Down or Top"]
        
        elif (Action.MOVE_LEFT not in possible_moves or Action.MOVE_RIGHT not in possible_moves):
            return top_or_down["Top or Down"]
        
        
        
        else:
            return self.agent.knowledge["LastAction"][-1]


    def deliberate_red_seeking(self):
        if any( 
            isinstance(neighbor, WasteAgent)
            and neighbor.color == self.agent.color
            and neighbor.pos == self.agent.pos
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            self.mode = AgentModeFusionAndResearch.CARRYING
            return Action.COLLECT
        possible_moves = self.check_possible_directions()
        if Action.MOVE_LEFT in possible_moves:
            return Action.MOVE_LEFT
        
        elif self.agent.knowledge["LastAction"][-1] == Action.MOVE_LEFT:
            return random.choice([Action.MOVE_UP, Action.MOVE_DOWN])
        
        elif Action.MOVE_DOWN not in possible_moves:
            return Action.MOVE_UP
        
        elif Action.MOVE_UP not in possible_moves:
            return Action.MOVE_DOWN

        else:
            return self.agent.knowledge["LastAction"][-1]

    def deliberate_placing(self, action):
        
        
        if len( self.agent.knowledge['carrying'] ) <= 2 and any(
            isinstance(neighbor, WasteAgent)
            and neighbor.color == self.agent.color
            and neighbor.pos == self.agent.pos
            for neighbor in self.agent.knowledge["Neighbors"]
        ):
            if self.agent_type != AgentModeFusionAndResearch.PLACING_FUSION or self.agent.color == Colors.RED:
                self.mode = AgentModeFusionAndResearch.CARRYING
            return Action.COLLECT
        possible_moves = self.check_possible_directions()
        if action in possible_moves:
            return action
        else:
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
                

    def deliberate(self):
        match self.mode:
            case AgentModeFusionAndResearch.FUSION:
                if self.agent.color == Colors.RED:
                    return self.deliberate_red_seeking()
                return self.deliberate_fusion()
            case AgentModeFusionAndResearch.CARRYING:
                return self.deliberate_carrying()
            case AgentModeFusionAndResearch.RESEARCHING_TOP:
                return self.deliberate_research( { "Top or Down": Action.MOVE_DOWN,
                                                "Down or Top": Action.MOVE_UP,
                                                "Change Mode": AgentModeFusionAndResearch.RESEARCHING_DOWN } )
            case AgentModeFusionAndResearch.RESEARCHING_DOWN:
                return self.deliberate_research( { "Top or Down": Action.MOVE_UP,
                                                "Down or Top": Action.MOVE_DOWN,
                                                "Change Mode": AgentModeFusionAndResearch.RESEARCHING_TOP } )
            case AgentModeFusionAndResearch.PLACING_FUSION:
                if self.agent.color == Colors.RED:
                    return self.deliberate_placing(Action.MOVE_LEFT)
                return self.deliberate_placing(Action.MOVE_RIGHT)
            case AgentModeFusionAndResearch.PLACING_TOP:
                return self.deliberate_placing(Action.MOVE_UP)
            case AgentModeFusionAndResearch.PLACING_DOWN:
                return self.deliberate_placing(Action.MOVE_DOWN)
            
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
