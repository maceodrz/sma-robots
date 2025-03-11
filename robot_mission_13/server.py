from model import WasteModelRed
from agents import Robot, GreenAgent, YellowAgent, RedAgent
from mesa.visualization import SolaraViz, make_plot_component, make_space_component # type: ignore

def agent_portrayal(agent):
    if isinstance(agent, GreenAgent):
        return {
            "color": "green",
            "size": 50,
        }
    elif isinstance(agent, YellowAgent):
        return {
            "color": "yellow",
            "size": 50,
        }
    elif isinstance(agent, RedAgent):
        return {
            "color": "tab:red",
            "size": 50,
        }
    else:
        return {
            "color": "white",
            "size": 50,
        }


model_params = {
    'width':20,
    'height':10,
    'num_green_agents':3,
    'num_yellow_agents':3,
    'num_red_agents':3,
    'num_green_waste':3,
    'num_yellow_waste':0,
    'num_red_waste':5,
    'proportion_z3':0.3,
    'proportion_z2':0.3,
    'seed':None,
}




waste_model = WasteModelRed(**model_params)

SpaceGraph = make_space_component(agent_portrayal)

page = SolaraViz(
    waste_model,
    [SpaceGraph],
    name="Waste Robots, les nazes"
)

if __name__ == "__main__":
    page
