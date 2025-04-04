from model import WasteModel
from time import time
from tqdm import tqdm
import pandas as pd
import os
import matplotlib.pyplot as plt


def save_waste_df(model, output_path):
    """
    Save the waste data frame to a CSV file.
    """
    waste_df = model.datacollector.get_model_vars_dataframe()

    waste_df.to_csv(output_path, index=False)


def run_and_save(model_config, output_path):
    """
    Run the model and save the waste data frame to a CSV file.
    """
    # Create the model
    model = WasteModel(**model_config)
    start_time = time()
    # Run the model
    for i in tqdm(range(400)):
        model.step()
    end_time = time()

    # Print the elapsed time
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    # Save the waste data frame
    save_waste_df(model, output_path)
    plot_waste(output_path, elapsed_time)

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
def plot_waste(waste_df_path, elapsed_time):
    # Load the waste data frame from the CSV file
    waste_df = pd.read_csv(waste_df_path)
    # Find the first time step where 'Red Wastes' reaches zero
    if 'Red Wastes' in waste_df.columns:
        zero_red_index = waste_df[waste_df['Red Wastes'] == 0].index.min()
        if not pd.notna(zero_red_index):
            print("'Red Wastes' never reaches zero.")
    else:
        print("'Red Wastes' column not found in the data.")
    min_green_index, min_green_value = extract_min_index_min_value(waste_df, 'Green Wastes')
    min_yellow_index, min_yellow_value = extract_min_index_min_value(waste_df, 'Yellow Wastes')
    min_total_index, min_total_value = extract_min_index_min_value(waste_df, 'Wastes')

    # Plot each column as a curve
    plt.figure(figsize=(10, 6))
    color_map = {
        'Green Wastes': 'green',
        'Yellow Wastes': 'orange',
        'Red Wastes': 'red',
        'Wastes': 'grey'
    }

    for column in waste_df.columns:
        color = color_map.get(column, None)
        linestyle = '--' if column == 'Wastes' else '-'
        plt.plot(waste_df.index, waste_df[column], label=column, color=color, linestyle=linestyle)

    # Add labels, title, and legend
    plt.xlabel("Time Step")
    plt.ylabel("Value")
    plt.title("Waste Data Over Time")
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

    # Annotate the first time step where 'Red Wastes' reaches zero
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


if __name__ == "__main__":
    config = {
        "width": 21,
        "height": 10,
        "num_green_agents": 3,
        "num_yellow_agents": 3,
        "num_red_agents": 10,
        "num_green_waste": 10,
        "num_yellow_waste": 10,
        "num_red_waste": 5,
        "proportion_z3": 1 / 3,
        "proportion_z2": 1 / 3,
        "seed": None,
        "Strategy_Green": "Random",
        "Strategy_Yellow": "Random",
        "Strategy_Red": "Random",
    }
    timestamp = time()
    # Generate a timestamp for the output file
    # Create the directory if it doesn't exist
    os.makedirs("data/model_runs", exist_ok=True)
    os.makedirs("data/waste_plots", exist_ok=True)
    output_path = f"data/model_runs/waste_data_{timestamp}.csv"
    run_and_save(config, output_path)
