import mesa
from mesa import Agent, Model
from mesa.space import MultiGrid

possible_actions = ['move', 'collect', 'drop']



class Robot(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)
        self.percepts = {  }
        self.knowledge = {"current_position": (0, 0), "target": None}
        self.unique_id = unique_id
        self.action = None
        
    def percept(self):
        pass
    
    def deliberate(self):
        pass   
    
    def step_agent (self): 
        self.knowledge = self.percept()
        self.action = self.deliberate(self.knowledge) 
        self.percepts = self.model.do(self, self.action)


class GreenAgent(Robot):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
    def percept(self):
        pass
    
    def deliberate(self, knowledge):
        pass


class YellowAgent(Robot):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
    def percept(self):
        pass
    
    def deliberate(self, knowledge):
        pass

class RedAgent(Robot):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
    def percept(self):
        pass
    
    def deliberate(self, knowledge):
        pass

