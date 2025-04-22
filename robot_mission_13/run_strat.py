from model import WasteModel
from time import time
from tqdm import tqdm
import pandas as pd
import os
import matplotlib.pyplot as plt


def save_waste_df(waste_dfs, output_path):
    """
    Save the waste data frame to a CSV file.
    """
    # Combine all dataframes in waste_dfs by calculating the mean and standard deviation
    combined_df = pd.concat(waste_dfs).groupby(level=0).agg(['mean', 'std'])
    # Flatten the multi-level columns
    combined_df.columns = ['_'.join(col).strip() for col in combined_df.columns.values]
    # Save the combined dataframe to a CSV file
    combined_df.to_csv(output_path, index=False)

def extract_min_index_min_value(df, column_name):
    """
    Extract the index and minimum value of a specified column in a DataFrame.
    """
    if column_name in df.columns:
        min_value = df[column_name].min()
        min_index = df[df[column_name] == min_value].index.min()
        return min_index, min_value
    else:
        print(f"Column '{column_name}' not found in the DataFrame.")
        return None, None

def extract_data_of_interest(df, data_dict):
    min_green_index, min_green_value = extract_min_index_min_value(df, 'Green Wastes')
    min_yellow_index, min_yellow_value = extract_min_index_min_value(df, 'Yellow Wastes')
    min_total_index, min_total_value = extract_min_index_min_value(df, 'Wastes')
    min_red_index, min_red_value = extract_min_index_min_value(df, 'Red Wastes')
    
    # Append the data to the dictionary
    data_dict['red'].append([min_red_index, min_red_value])
    data_dict['green'].append([min_green_index, min_green_value])
    data_dict['yellow'].append([min_yellow_index, min_yellow_value])
    data_dict['total'].append([min_total_index, min_total_value])
    return data_dict

def plot_waste(waste_df_path, elapsed_time, with_interval=True):
    # Load the waste data frame from the CSV file
    waste_df = pd.read_csv(waste_df_path)
    # Find the first time step where 'Red Wastes' reaches zero
    if 'Red Wastes_mean' in waste_df.columns:
        zero_red_index = waste_df[waste_df['Red Wastes_mean'] == 0].index.min()
        if not pd.notna(zero_red_index):
            print("'Red Wastes_mean' never reaches zero.")
    else:
        print("'Red Wastes_mean' column not found in the data.")
    min_green_index, min_green_value = extract_min_index_min_value(waste_df, 'Green Wastes_mean')
    min_yellow_index, min_yellow_value = extract_min_index_min_value(waste_df, 'Yellow Wastes_mean')
    min_total_index, min_total_value = extract_min_index_min_value(waste_df, 'Wastes_mean')

    # Plot each column mean with optional 95% confidence interval
    plt.figure(figsize=(10, 6))
    color_map = {
        'Green Wastes': 'green',
        'Yellow Wastes': 'orange',
        'Red Wastes': 'red',
        'Wastes': 'grey'
    }

    for waste_type in ['Green Wastes', 'Yellow Wastes', 'Red Wastes', 'Wastes']:
        mean_col = f"{waste_type}_mean"
        std_col = f"{waste_type}_std"
        if mean_col in waste_df.columns and std_col in waste_df.columns:
            color = color_map.get(waste_type, None)
            linestyle = '--' if waste_type == 'Wastes' else '-'
            mean_values = waste_df[mean_col]
            std_values = waste_df[std_col]
            plt.plot(waste_df.index, mean_values, label=waste_type, color=color, linestyle=linestyle)
            if with_interval:
                ci_upper = mean_values + 1.96 * std_values
                ci_lower = mean_values - 1.96 * std_values
                plt.fill_between(waste_df.index, ci_lower, ci_upper, color=color, alpha=0.2)

    # Add labels, title, and legend
    plt.xlabel("Time Step")
    plt.ylabel("Value")
    plt.title("Waste Data Over Time with 95% Confidence Interval" if with_interval else "Waste Data Over Time")
    plt.legend()
    plt.grid()

    # Annotate the minimum values on the plot
    annotations = [
        ("Min Green", min_green_index, min_green_value, 15, 'green', 'green'),
        ("Min Yellow", min_yellow_index, min_yellow_value, 10, 'yellow', 'orange'),
        ("Min Total", min_total_index, min_total_value, 7, 'black', 'black')
    ]

    for label, index, value, offset, arrow_color, text_color in annotations:
        if pd.notna(index):
            plt.annotate(f"{label}: {value} (Index: {index})",
                         xy=(index, value),
                         xytext=(index, value + offset),
                         arrowprops=dict(facecolor=arrow_color, arrowstyle='->', lw=0.2),
                         fontsize=9, color=text_color)
    # Annotate the elapsed time on the plot
    plt.annotate(f"Elapsed Time: {elapsed_time:.2f}s",
                 xy=(0.05, 0.95),
                 xycoords='axes fraction',
                 fontsize=10,
                 color='blue',
                 bbox=dict(facecolor='white', alpha=0.8, edgecolor='blue'))

    # Annotate the first time step where 'Red Wastes_mean' reaches zero
    if pd.notna(zero_red_index):
        plt.annotate(f"Zero Red Index: {zero_red_index}",
                     xy=(zero_red_index, 0),
                     xytext=(zero_red_index, 5),
                     arrowprops=dict(facecolor='red', arrowstyle='->'),
                     fontsize=9,
                     color='red')

    # Save the plot to a file
    timestamp = time()
    plot_path = f"data/waste_plots/waste_plot_{timestamp}.png"
    plt.savefig(plot_path)


def run_and_save(model_config, output_path, batch_size=10):
    """
    Run the model and save the waste data frame to a CSV file.
    """
    start_time = time()
    waste_dfs = []
    data_dict = {
        'green':[],
        'yellow':[],
        'red':[],
        'total':[]
    }
    for iter in range(batch_size):
        # Create the model
        model = WasteModel(**model_config)
        # Run the model
        for i in range(700):
            model.step()
        # Collect data
        waste_dfs.append(model.datacollector.get_model_vars_dataframe())
        data_dict = extract_data_of_interest(waste_dfs[iter], data_dict)
        
    end_time = time()

    # Print the elapsed time
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    # Save the waste data frame
    save_waste_df(waste_dfs, output_path)
    plot_waste(output_path, elapsed_time)





def run_model_results(strategies, tuples_green_yellow_red_waste, tuples_green_yellow_red_agents, largeur, hauteur):
    """
    Run the model with different strategies and configurations, and save the results.
    """
    results = []
    for strategy in strategies:
        for waste_tuple in tuples_green_yellow_red_waste:
            for agent_tuple in tuples_green_yellow_red_agents:
                config = {
                    "width": largeur,
                    "height": hauteur,
                    "num_green_agents": agent_tuple[0],
                    "num_yellow_agents": agent_tuple[1],
                    "num_red_agents": agent_tuple[2],
                    "num_green_waste": waste_tuple[0],
                    "num_yellow_waste": waste_tuple[1],
                    "num_red_waste": waste_tuple[2],
                    "proportion_z3": 1 / 3,
                    "proportion_z2": 1 / 3,
                    "seed": None,
                    "Strategy_Green": strategy,
                    "Strategy_Yellow": strategy,
                    "Strategy_Red": strategy,
                }
                timestamp = time()
                os.makedirs("data/model_runs", exist_ok=True)
                os.makedirs("data/waste_plots", exist_ok=True)
                output_path = f"data/model_runs/waste_data_{timestamp}.csv"
                
                # Run the model and save results
                start_time = time()
                model = WasteModel(**config)
                steps = 0
                retry = False
                while True:
                    if retry:
                        print("Retrying with same configuration...")
                        model = WasteModel(**config)
                        steps = 0
                        retry = False
                    model.step()
                    steps += 1
                    waste_df = model.datacollector.get_model_vars_dataframe()
                    if 'Wastes' in waste_df.columns and waste_df['Wastes'].iloc[-1] == 0:
                        break
                    if steps >= 7000:
                        retry=True
                    
                    
                elapsed_time = time() - start_time
                results.append({
                    "strategy": strategy,
                    "waste_tuple": waste_tuple,
                    "agent_tuple": agent_tuple,
                    "steps": steps,
                    "elapsed_time": elapsed_time
                })
                print(f"Strategy: {strategy}, Waste: {waste_tuple}, Agents: {agent_tuple}, Steps: {steps}, Time: {elapsed_time:.2f}s")
    timestamp = time()
    # Save the results to a CSV file
    results_df = pd.DataFrame(results)
    results_output_path = f"data/model_runs/results_{timestamp}.csv"
    results_df.to_csv(results_output_path, index=False)
    print(f"Results saved to {results_output_path}")

if __name__ == "__main__":
    tuples_green_yellow_red_waste = [
        (2, 1, 2),
        (4, 2, 2),
        (10, 5, 5),
        (12, 10, 10),
        (24, 10, 10),
        (24, 20, 10),
        (36, 20, 20),
        (48, 20, 20)
    ]
    tuples_green_yellow_red_agents = [
        # (2, 2, 2),
        (3, 3, 3),
        # (4, 4, 4)
    ]

    strategies = [
        "Fusion And Research",
        "Random",
        "Fusion And Research With Communication"
    ]
    
    # run_model_results(strategies, tuples_green_yellow_red_waste, tuples_green_yellow_red_agents, largeur = 41, hauteur = 20)

    config = {
        "width": 21,
        "height": 20,
        "num_green_agents": 3,
        "num_yellow_agents": 3,
        "num_red_agents": 3,
        "num_green_waste": 20,
        "num_yellow_waste": 10,
        "num_red_waste": 10,
        "proportion_z3": 1 / 3,
        "proportion_z2": 1 / 3,
        "seed": None,
        "Strategy_Green": "Fusion And Research With Communication",
        "Strategy_Yellow": "Fusion And Research With Communication",
        "Strategy_Red": "Fusion And Research With Communication",
    }
    timestamp = time()
    # Generate a timestamp for the output file
    # Create the directory if it doesn't exist
    os.makedirs("data/model_runs", exist_ok=True)
    os.makedirs("data/waste_plots", exist_ok=True)
    output_path = f"data/model_runs/waste_data_{timestamp}.csv"
    run_and_save(config, output_path, batch_size=30)

    