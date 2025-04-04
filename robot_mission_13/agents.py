from mesa import Agent
from objects import Colors
from strategy import StrategyRandom, AgentMode


class Robot(Agent):
    def __init__(self, model, unique_id, color=None, max_radioactivity=None):
        super().__init__(model)
        self.percepts = {}

        self.knowledge = {"Neighbors": [], "carrying": [], "LastActionNotWorked": None}
        self.unique_id = unique_id
        self.action = None
        self.color = color
        self.max_radioactivity = max_radioactivity
        self.model = model
        self.color = None
        self.strategy = StrategyRandom(model, self)


    def percept(self):
        self.knowledge["Neighbors"] = list(
            self.model.grid.get_neighbors(
                self.pos, moore=True, include_center=True, radius=1
            )
        )
        return self.knowledge

    def step_agent(self):
        self.knowledge = self.percept()
        self.action = self.strategy.deliberate()
        self.percepts = self.model.do(self, self.action)

    def step(self):
        self.step_agent()


class GreenAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id)
        self.model = model
        self.color = Colors.GREEN
        self.max_radioactivity = 1 / 3
        self.strategy = StrategyRandom(model, self)

class YellowAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id)
        self.max_radioactivity = 2 / 3
        self.color = Colors.YELLOW
        self.strategy = StrategyRandom(model, self)

class RedAgent(Robot):
    def __init__(self, model, unique_id):
        super().__init__(model, unique_id)
        self.max_radioactivity = 1
        self.color = Colors.RED
        self.strategy = StrategyRandom(model, self)
