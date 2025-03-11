import mesa
from objects import RadioactivityAgent, WasteAgent, WasteDisposalAgent, Colors
from agents import GreenAgent, YellowAgent, RedAgent

class WasteModelRed(mesa.Model):
    """A model with some number of agents."""

    def __init__(self, width=10, height=10, num_green_agents=0, num_yellow_agents=0,num_red_agents=3, num_green_waste=3, num_yellow_waste=0, num_red_waste=5,proportion_z3=1, proportion_z2=0, seed=None):
        """Initialize a MoneyModel instance.

        Args:
            width: width of the grid.
            height: Height of the grid.
            num_red_agents: Number of red agents.
        """
        super().__init__(seed=seed)

        self.grid = mesa.grid.MultiGrid(width, height, torus=False)

        self.width_z3 = int(width * proportion_z3)
        self.width_z2 = int(width * (proportion_z2))
        self.width_z1 = width - self.width_z3 - self.width_z2
        self.width = width
        self.height = height
        
        self.num_green_agents = num_green_agents
        self.num_yellow_agents = num_yellow_agents
        self.num_red_agents = num_red_agents

        self.num_green_waste = num_green_waste
        self.num_yellow_waste = num_yellow_waste
        self.num_red_waste = num_red_waste
        
        # Create Radioactivity agents
        for j in range(self.height):
            if self.width_z1 > 0:
                for i in range(self.width_z1):
                    agent = RadioactivityAgent(self, radiocativity=0.1)
                    self.grid.place_agent(agent, (j, i))
            if self.width_z2 > 0:
                for i in range(self.width_z2):
                    agent = RadioactivityAgent(self, radiocativity=0.5)
                    self.grid.place_agent(agent, (j, i + self.width_z1))
            if self.width_z3 > 0:
                for i in range(self.width_z3):
                    agent = RadioactivityAgent(self, radiocativity=0.9)
                    self.grid.place_agent(agent, (j, i + self.width_z1 + self.width_z2))

        # Create Waste agents
            
        # Zone 1
        if self.width_z1 > 0 and self.num_green_waste > 0:
            agents = WasteAgent.create_agents(model=self, n=self.num_green_waste, color=Colors.GREEN)
            x = self.random.choices(range(self.width_z1), k=self.num_green_waste)
            y = self.random.choices(range(self.height), k=self.num_green_waste)
            for a, i, j in zip(agents, x, y):
                self.grid.place_agent(a, (i, j))
        else:
            self.num_green_waste = 0
            print("No green waste in Zone 1")
            
        # Zone 2
        if self.width_z2 > 0 and self.num_yellow_waste > 0:
            agents = WasteAgent.create_agents(model=self, n=self.num_yellow_waste, color=Colors.YELLOW)
            x = self.random.choices(range(self.width_z1, (self.width_z1 + self.width_z2)), k=self.num_yellow_waste)
            y = self.random.choices(range(self.height), k=self.num_yellow_waste)
            for a, i, j in zip(agents, x, y):
                self.grid.place_agent(a, (i + self.width_z1, i))
        else:
            self.num_yellow_waste = 0
            print("No yellow waste in Zone 2")
        
        # Zone 3
        if self.width_z3 > 0 and self.num_red_waste > 0:

            agents = WasteAgent.create_agents(model=self, n=self.num_red_waste, color=Colors.RED)
            x = self.random.choices(range(self.width_z3), k=self.num_red_waste)
            y = self.random.choices(range(self.height), k=self.num_red_waste)
            for a, i, j in zip(agents, x, y):
                self.grid.place_agent(a, (i + self.width_z1 + self.width_z2, i))
        else:
            self.num_red_waste = 0
            print("No red waste in Zone 3")
    
        # Create WasteDisposalAgent
        x = width - 1
        y = self.random.choices(range(self.height), k=1)
        agent = WasteDisposalAgent(self)
        self.grid.place_agent(agent, (x, y[0]))
    
    
        # Create RobotAgent
        # Green Robots
        for i in range(self.num_green_agents):
            unique_id = self.next_id()
            agent = GreenAgent(self, unique_id)
            x = self.random.choices(range(self.width_z1), k=1)
            y = self.random.choices(range(self.height), k=1)
            self.grid.place_agent(agent, (x[0], y[0]))
        
        
        for i in range(self.num_yellow_agents):
            unique_id = self.next_id()
            agent = YellowAgent(self, unique_id)
            x = self.random.choices(range(self.width_z2), k=1)
            y = self.random.choices(range(self.height), k=1)
            self.grid.place_agent(agent, (x[0] + self.width_z1, y[0]))
        
        
        for i in range(self.num_red_agents):
            unique_id = self.next_id()
            agent = RedAgent(self, unique_id)
            x = self.random.choices(range(self.width_z3), k=1)
            y = self.random.choices(range(self.height), k=1)
            self.grid.place_agent(agent, (x[0] + self.width_z1 + self.width_z2, y[0]))