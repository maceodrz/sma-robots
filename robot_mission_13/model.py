import mesa
from objects import RadioactivityAgent, WasteAgent, WasteDisposalAgent, Colors
from agents import GreenAgent, YellowAgent, RedAgent
from strategy import Action
from mesa.space import MultiGrid


def compute_waste_number(model, color=None):
    if color is None:
        waste_agents = [
            agent
            for agent in model.agents_by_type[WasteAgent]
            if isinstance(agent, WasteAgent)
        ]
        return len(waste_agents)

    waste_agents = [
        agent
        for agent in model.agents_by_type[WasteAgent]
        if isinstance(agent, WasteAgent) and agent.color == color
    ]
    return len(waste_agents)


def compute_waste_model_red(model):
    return compute_waste_number(model, color=Colors.RED)


def compute_waste_model_yellow(model):
    return compute_waste_number(model, color=Colors.YELLOW)


def compute_waste_model_green(model):
    return compute_waste_number(model, color=Colors.GREEN)


class WasteModel(mesa.Model):
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
        Strategy = "Random",
        seed=None,
    ):
        super().__init__(seed=seed)

        self.grid = MultiGrid(width, height, torus=False)
        self.width = width
        self.height = height
        self.Strategy = Strategy

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

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Wastes": compute_waste_number,
                "Red Wastes": compute_waste_model_red,
                "Yellow Wastes": compute_waste_model_yellow,
                "Green Wastes": compute_waste_model_green,
            },
            agent_reporters={
                "carrying": "carrying",
                "LastActionNotWorked": "LastActionNotWorked",
                "color": "color",
            },  # TODO : voir lesquels sont utiles
        )
        self.datacollector.collect(self)

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
                agents = WasteAgent.create_agents(
                    self, n=num_waste, color=getattr(Colors, color.upper())
                )
                x = self.random.choices(range(start_x, start_x + width), k=num_waste)
                y = self.random.choices(range(self.height), k=num_waste)
                for a, i, j in zip(agents, x, y):
                    self.grid.place_agent(a, (i, j))
            else:
                print(f"No {color} waste in Zone {zones.index((width, color)) + 1}")
            start_x += width

    def _initialize_agents(self):
        agent_classes = {"green": GreenAgent, "yellow": YellowAgent, "red": RedAgent}
        start_x = {
            "green": 0,
            "yellow": self.width_z1,
            "red": self.width_z1 + self.width_z2,
        }

        for color, num in self.num_agents.items():
            for _ in range(num):
                unique_id = self.next_id()
                agent = agent_classes[color](self, unique_id, self.Strategy)
                x = self.random.choice(
                    range(
                        self.width_z1
                        if color == "green"
                        else self.width_z2
                        if color == "yellow"
                        else self.width_z3
                    )
                )
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

        movement_actions = {
            Action.MOVE_LEFT: (-1, 0),
            Action.MOVE_RIGHT: (1, 0),
            Action.MOVE_UP: (0, 1),
            Action.MOVE_DOWN: (0, -1),
        }

        match action:
            case action if action in movement_actions:
                new_pos = (
                    agent.pos[0] + movement_actions[action][0],
                    agent.pos[1] + movement_actions[action][1],
                )
                if self.is_movement_possible(agent, new_pos):
                    self.grid.move_agent(agent, new_pos)
                    agent.knowledge["LastActionNotWorked"] = None
                else:
                    agent.knowledge["LastActionNotWorked"] = action

            case Action.FUSION:
                carrying = agent.knowledge["carrying"]
                if len(carrying) >= 2 and carrying[0].color == carrying[1].color:
                    for waste in carrying:
                        waste.remove()
                    agent.knowledge["carrying"] = [
                        WasteAgent.create_agents(
                            model=self, n=1, color=agent.color + 1
                        )[0]
                    ]

                    print(
                        "je fusionne deux déchets de la couleur ",
                        agent.color,
                        "à l endroit ",
                        agent.pos,
                    )
                    agent.knowledge["LastActionNotWorked"] = None
                else:
                    agent.knowledge["LastActionNotWorked"] = action

            case Action.COLLECT:
                possible_agent = self.is_collect_possible(agent, agent.pos)
                if possible_agent and possible_agent.pos:
                    self.grid.remove_agent(possible_agent)
                    agent.knowledge["carrying"].append(possible_agent)
                    agent.knowledge["LastActionNotWorked"] = None
                else:
                    agent.knowledge["LastActionNotWorked"] = action

            case Action.DROP:
                if len(agent.knowledge["carrying"]) > 0:
                    DroppedAgent = agent.knowledge["carrying"].pop()
                    agent.knowledge["LastActionNotWorked"] = None
                    if any(
                        isinstance(cell_content, WasteDisposalAgent)
                        for cell_content in self.grid.get_cell_list_contents(
                            [agent.pos]
                        )
                    ):
                        DroppedAgent.remove()
                    else:
                        self.grid.place_agent(DroppedAgent, agent.pos)
                    print(
                        "je pose à cet endroit ",
                        agent.pos,
                        " et je suis de la couleur ",
                        agent.color,
                    )
                else:
                    agent.knowledge["LastActionNotWorked"] = action
            case _:
                agent.knowledge["LastActionNotWorked"] = action

        return agent.knowledge

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
        if self.steps == 1000:
            wastes_df = self.datacollector.get_agent_vars_dataframe()
            
            
            

    def get_radioactivity(self, i, j):
        for agent in self.grid.get_cell_list_contents([(i, j)]):
            if isinstance(agent, RadioactivityAgent):
                return agent.get_radioactivity()
        return None
