import mesa
from objects import RadioactivityAgent, WasteAgent, WasteDisposalAgent, Colors
from agents import GreenAgent, YellowAgent, RedAgent, Action
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector


class WasteModelRed(mesa.Model):
    """A model with some number of agents."""

    def next_id(self):
        """Generate the next unique ID for an agent."""
        self._next_id += 1
        return self._next_id

    def __init__(
        self,
        width=21,
        height=10,
        num_green_agents=3,
        num_yellow_agents=3,
        num_red_agents=3,
        num_green_waste=3,
        num_yellow_waste=0,
        num_red_waste=5,
        proportion_z3=1 / 3,
        proportion_z2=1 / 3,
        seed=None,
    ):
        super().__init__(seed=seed)
        
        self.grid = MultiGrid(width, height, torus=False)
        self.width = width
        self.height = height
        
        # Calculate zone widths
        self.width_z3 = int(width * proportion_z3)
        self.width_z2 = int(width * proportion_z2)
        self.width_z1 = width - self.width_z3 - self.width_z2
        
        self.num_agents = {
            "green": num_green_agents,
            "yellow": num_yellow_agents,
            "red": num_red_agents,
        }
        
        self.num_waste = {
            "green": num_green_waste,
            "yellow": num_yellow_waste,
            "red": num_red_waste,
        }
        
        self._next_id = 0
        self._initialize_radioactivity()
        self._initialize_waste()
        self._initialize_agents()
        self._initialize_waste_disposal()
    
    def _initialize_radioactivity(self):
        zones = [(self.width_z1, 0.1), (self.width_z2, 0.5), (self.width_z3, 0.9)]
        start_x = 0
        
        for width, radioactivity in zones:
            for j in range(self.height):
                for i in range(width):
                    agent = RadioactivityAgent(self, radiocativity=radioactivity)
                    self.grid.place_agent(agent, (start_x + i, j))
            start_x += width
    
    def _initialize_waste(self):
        zones = [
            (self.width_z1, "green"),
            (self.width_z2, "yellow"),
            (self.width_z3, "red"),
        ]
        start_x = 0
        
        for width, color in zones:
            num_waste = self.num_waste[color]
            if width > 0 and num_waste > 0:
                agents = WasteAgent.create_agents(self, n=num_waste, color=getattr(Colors, color.upper()))
                x = self.random.choices(range(start_x, start_x + width), k=num_waste)
                y = self.random.choices(range(self.height), k=num_waste)
                for a, i, j in zip(agents, x, y):
                    self.grid.place_agent(a, (i, j))
            else:
                print(f"No {color} waste in Zone {zones.index((width, color)) + 1}")
            start_x += width
    
    def _initialize_agents(self):
        agent_classes = {"green": GreenAgent, "yellow": YellowAgent, "red": RedAgent}
        start_x = {"green": 0, "yellow": self.width_z1, "red": self.width_z1 + self.width_z2}
        
        for color, num in self.num_agents.items():
            for _ in range(num):
                unique_id = self.next_id()
                agent = agent_classes[color](self, unique_id)
                x = self.random.choice(range(self.width_z1 if color == "green" else 
                                            self.width_z2 if color == "yellow" else 
                                            self.width_z3))
                y = self.random.choice(range(self.height))
                self.grid.place_agent(agent, (start_x[color] + x, y))
    
    def _initialize_waste_disposal(self):
        x = self.width - 1
        y = self.random.choice(range(self.height))
        agent = WasteDisposalAgent(self)
        self.grid.place_agent(agent, (x, y))

    def is_movement_possible(self, agent, pos):
        x, y = pos
        return (
            0 <= x < self.width
            and 0 <= y < self.height
            and agent.max_radioactivity >= self.get_radioactivity(x, y)
        )

    def is_collect_possible(self, agent, pos):  # TODO
        for PossibleAgent in self.grid.get_cell_list_contents([pos]):
            if (
                isinstance(PossibleAgent, WasteAgent)
                and PossibleAgent.color == agent.color
            ):
                return PossibleAgent
        return False

    def do(self, agent, action):
        """Advance the model by one step."""

        if action == Action.MOVE_LEFT and self.is_movement_possible(
            agent, (agent.pos[0] - 1, agent.pos[1])
        ):
            self.grid.move_agent(agent, (agent.pos[0] - 1, agent.pos[1]))
            agent.knowledge["LastActionWorked"] = True

        elif action == Action.MOVE_RIGHT and self.is_movement_possible(
            agent, (agent.pos[0] + 1, agent.pos[1])
        ):
            self.grid.move_agent(agent, (agent.pos[0] + 1, agent.pos[1]))
            agent.knowledge["LastActionWorked"] = True

        elif action == Action.MOVE_UP and self.is_movement_possible(
            agent, (agent.pos[0], agent.pos[1] - 1)
        ):
            self.grid.move_agent(agent, (agent.pos[0], agent.pos[1] - 1))
            agent.knowledge["LastActionWorked"] = True

        elif action == Action.MOVE_DOWN and self.is_movement_possible(
            agent, (agent.pos[0], agent.pos[1] + 1)
        ):
            self.grid.move_agent(agent, (agent.pos[0], agent.pos[1] + 1))
            agent.knowledge["LastActionWorked"] = True
        elif action == Action.FUSION:  # TODO
            if (
                agent.knowledge["carrying"][0].color
                == agent.knowledge["carrying"][1].color
            ):
                agent.knowledge["carrying"] = [
                    WasteAgent.create_agents(model=self, n=1, color=Colors.YELLOW)[0]
                ]
                print(agent.knowledge["carrying"])
                agent.knowledge["LastActionWorked"] = True
            else:
                agent.knowledge["LastActionWorked"] = False
        elif action == Action.COLLECT:  # TODO
            PossibleAgent = self.is_collect_possible(agent, agent.pos)

            if PossibleAgent and PossibleAgent.pos:
                self.grid.remove_agent(PossibleAgent)
                agent.knowledge["carrying"].append(PossibleAgent)
                agent.knowledge["LastActionWorked"] = True
            else:
                agent.knowledge["LastActionWorked"] = False
        else:
            agent.knowledge["LastActionWorked"] = False
        return agent.knowledge

    def step(self):
        self.agents.shuffle_do("step")

    def get_radioactivity(self, i, j):
        for agent in self.grid.get_cell_list_contents([(i, j)]):
            if isinstance(agent, RadioactivityAgent):
                return agent.get_radioactivity()
        return None
