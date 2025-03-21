from model import WasteModelRed
from objects import RadioactivityAgent, WasteDisposalAgent, WasteAgent
from agents import Robot, GreenAgent, YellowAgent, RedAgent
from mesa.visualization import SolaraViz, make_plot_component, make_space_component  # type: ignore


def agent_portrayal(agent):
    if isinstance(agent, RadioactivityAgent):
        if agent.get_radioactivity() > 0.66:
            return {
                "color": "#FF00004C",  # Rouge avec transparence 0.8
                "size": 400,
                "layer": "background",
                "marker": "s",

            }
        elif agent.get_radioactivity() > 0.33:
            return {
                "color": "#FFA5004C",  # Orange avec transparence 0.8
                "size": 400,
                "zorder": 1,
                "marker": "s",
                
                
            }
        else:
            return {
                "color": "#00FF004C",  # Vert avec transparence 0.8
                "size": 400,
                "layer": "background",
                "marker": "s",

            }
    if isinstance(agent, GreenAgent):
                return {
                    "color": "darkgreen",
                    "size": 50,
                    "zorder": 2,
                }
    elif isinstance(agent, YellowAgent):
                return {
                    "color": "goldenrod",
                    "size": 50,
                    "zorder": 2,
                }
    elif isinstance(agent, RedAgent):
                return {
                    "color": "darkred",
                    "size": 50,
                    "zorder": 2,
                }
    elif isinstance(agent, WasteDisposalAgent):
        return {
            "color": "black",
            "size": 200,
        }
    elif isinstance(agent, WasteAgent):
        if agent.color == 0:
            return {
                "color": "green",
                "shape": "s",
                "size": 50//2,
            }
        elif agent.color == 1:
            return {
                "color": "orange",
                "shape": "s",
                "size": 50//2,
            }
        elif agent.color == 2:
            return {
                "color": "red",
                "shape": "s",
                "size": 50//2,
            }
    else:
        return {
            "color": "white",
            "size": 50,
        }


model_params = { 
    'width': 21,
    'height': 10,
    'num_green_agents': 3,
    'num_yellow_agents': 3,
    'num_red_agents': 3,
    'num_green_waste': 3,
    'num_yellow_waste': 3,
    'num_red_waste': 5,
    'proportion_z3': 1/3,
    'proportion_z2': 1/3,
    'seed': None,
}

model_params_Slider = {
    "width": {
        "name": "Width",
        "type": "SliderInt",
        "value": 21,
        "min": 5,
        "max": 50,
    },
    "height": {
        "name": "Height",
        "type": "SliderInt",
        "value": 10,
        "min": 5,
        "max": 50,
    },
    "num_green_agents": {
        "name": "Number of Green Agents",
        "type": "SliderInt",
        "value": 3,
        "min": 0,
        "max": 10,
    },
    "num_yellow_agents": {
        "name": "Number of Yellow Agents",
        "type": "SliderInt",
        "value": 3,
        "min": 0,
        "max": 10,
    },
    "num_red_agents": {
        "name": "Number of Red Agents",
        "type": "SliderInt",
        "value": 3,
        "min": 0,
        "max": 10,
    },
    "num_green_waste": {
        "name": "Number of Green Waste",
        "type": "SliderInt",
        "value": 3,
        "min": 0,
        "max": 10,
    },
    "num_yellow_waste": {
        "name": "Number of Green Waste",
        "type": "SliderInt",
        "value": 3,
        "min": 0,
        "max": 10,
    },
    "num_red_waste": {
        "name": "Number of Green Waste",
        "type": "SliderInt",
        "value": 3,
        "min": 0,
        "max": 10,
    },
    
    
}

waste_model = WasteModelRed(**model_params)

SpaceGraph = make_space_component(agent_portrayal)

page = SolaraViz(
    waste_model,
    [SpaceGraph],
    name="Waste Robots, les nazes",
    model_params = model_params_Slider,
)

if __name__ == "__main__":
    page
