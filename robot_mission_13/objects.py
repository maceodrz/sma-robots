import mesa

class RadioactivityAgent(mesa.Agent):
    def __init__(self, model, radiocativity):
        """initialize a RadioactivityAgent instance.

        Args:
            model: A model instance
        """
        super().__init__(model)
        self.radioactivity = radiocativity
        self.name = 'RadioactivityAgent'
    
    def get_radioactivity(self):
        return self.radioactivity

class WasteAgent(mesa.Agent):
    def __init__(self, model, carried, color = None):
        """initialize a WasteAgent instance.

        Args:
            model: A model instance
        """
        super().__init__(model)
        self.color = color
        self.name = 'WasteAgent'
        self.carried = carried
    
    def init_color(self, carried):
        if carried == False:
            cellmates = self.model.grid.get_cell_list_contents([self.pos])
            for agent in cellmates:
                if agent.name == 'RadioactivityAgent':
                    if agent.get_radioactivity() > 0.66:
                        self.color = 'Red'
                    elif agent.get_radioactivity() > 0.33:
                        self.color = 'Yellow'
                    else:
                        self.color = 'Green'
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
        self.name = 'WasteDisposalAgent'
    
