import mesa


class Colors:
    GREEN = 0
    YELLOW = 1
    RED = 2


class RadioactivityAgent(mesa.Agent):
    def __init__(self, model, radiocativity):
        """initialize a RadioactivityAgent instance.

        Args:
            model: A model instance
        """
        super().__init__(model)
        self.radioactivity = radiocativity
        self.unique_id = model.next_id()

    def get_radioactivity(self):
        return self.radioactivity
    
    def step(self):
        
        pass


class WasteAgent(mesa.Agent):
    def __init__(self, model, carried=False, color=None):
        """initialize a WasteAgent instance.

        Args:
            model: A model instance
        """
        super().__init__(model)
        if color is None:
            self.init_color(carried)
        else:
            self.color = color
        self.carried = carried
        self.unique_id = model.next_id()
    
    def step(self):
        
        pass

    def init_color(self, carried):
        if not carried:
            cellmates = self.model.grid.get_cell_list_contents([self.pos])
            for agent in cellmates:
                if isinstance(agent, RadioactivityAgent):
                    if agent.get_radioactivity() > 0.66:
                        self.color = Colors.RED
                    elif agent.get_radioactivity() > 0.33:
                        self.color = Colors.YELLOW
                    else:
                        self.color = Colors.GREEN
                    break

    def destruct_agent(self):
        self.model.grid.remove_agent(self)


class WasteDisposalAgent(mesa.Agent):
    def __init__(self, model):
        """initialize a WasteDisposalAgent instance.

        Args:
            model: A model instance
        """
        super().__init__(model)
        self.unique_id = model.next_id()

    def step(self):
        
        pass