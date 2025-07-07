import os
import json
import subprocess
import numpy as np


def create_config_files(folder, trace_len, file_count, file_equal_prefix, file_not_equal_prefix):
    """
    Create configuration files for specific t-test based on trace files.

    NOTE: Config files are created in "folder"

    Parameters:
        folder (str): Path to the folder containing trace files.
        trace_len (int): Number of samples per trace.
        file_count (int): Number of equal and not-equal trace files (e.g., 10 for 0...9).
    """
    uint16_size = 2  # Size of uint16 in bytes
    bytes_per_trace = trace_len * uint16_size  # Total bytes per trace

    # Iterate over the file count (e.g., 0...9)
    for chunk_index in range(file_count):
        # File paths for equal and not-equal traces
        equal_file = os.path.join(folder, f"{file_equal_prefix}-{chunk_index}.bin")
        not_equal_file = os.path.join(folder, f"{file_not_equal_prefix}-{chunk_index}.bin")

        # Calculate trace counts
        equal_trace_cnt = os.path.getsize(equal_file) // bytes_per_trace if os.path.exists(equal_file) else 0
        not_equal_trace_cnt = os.path.getsize(not_equal_file) // bytes_per_trace if os.path.exists(not_equal_file) else 0

        # Create configuration data
        config_data = {
            "id": f"ttest-{chunk_index}",
            "ttest-module": "ttest",
            "function": "create",
            "random-traces": not_equal_file,
            "random-traces-count": str(not_equal_trace_cnt),  # Quote the number
            "constant-traces": equal_file,
            "constant-traces-count": str(equal_trace_cnt),  # Quote the number
            "samples-per-trace": str(trace_len)  # Quote the number
        }


        # Save configuration data to a JSON file
        config_file_path = os.path.join(folder, f"ttest_create_{chunk_index}.json")
        with open(config_file_path, 'w') as config_file:
            json.dump(config_data, config_file, indent=4)
        print(f"Created config file: {config_file_path}")



def create_contexts(folder, file_count, stan_exe = r".\sicak-1.2.1\stan.exe"):
    """
    Call stan.exe for each configuration file in the specified folder.

    NOTE: Context files are created in "." folder (current working directory).

    Parameters:
        folder (str): Path to the folder containing configuration files.
        file_count (int): Number of configuration files to process (e.g., 10 for 0...9).
    """

    # Iterate over the configuration files
    for chunk_index in range(file_count):
        # Path to the configuration file
        config_file = os.path.join(folder, f"ttest_create_{chunk_index}.json")

        # Check if the configuration file exists
        if not os.path.exists(config_file):
            print(f"Configuration file not found: {config_file}")
            continue

        # Call stan.exe with the configuration file
        try:
            print(f"Running stan.exe for {config_file}...")
            result = subprocess.run([stan_exe, config_file], check=True, capture_output=True, text=True)
            print(f"Output for config_create_{chunk_index}.json:\n{result.stdout}")
        except FileNotFoundError:
            print(f"Error: The file {stan_exe} was not found.")
            break
        except subprocess.CalledProcessError as e:
            print(f"Error while processing {config_file}:\n{e.stderr}")
            break

def run_merge_and_finalize(chunks, stan_exe = r".\sicak-1.2.1\stan.exe"):
    """
    Run merge methods until only one merged context file remains, then finalize.

    NOTE: Context files are created in "." folder (current working directory).

    Parameters:
        folder (str): Path to the folder containing merge configuration files.
        chunks (int): Number of chunks (must be even, as pairs are formed).
        stan_exe (str): Path to the stan.exe tool. Defaults to the relative path. (optional).
    """

    # Ensure the number of chunks is even
    if chunks % 2 != 0:
        raise ValueError("Chunks must be an even number to create pairs.")

    # Initialize the current round of context files
    current_contexts = [f"ttest-ttest-{i}.ctx" for i in range(chunks)]

    id_counter = 0  # ID counter for merged files
    while len(current_contexts) > 1:
        print(f"Starting merge round with {len(current_contexts)} contexts...")

        # Create merge configuration files for the current round
        next_contexts = []
        for i in range(0, len(current_contexts), 2):
            if i + 1 >= len(current_contexts):
                # If there's an odd number of contexts, carry the last one to the next round
                next_contexts.append(current_contexts[i])
                continue

            # Paths to context files for the pair
            context_a = os.path.join(".", current_contexts[i])
            context_b = os.path.join(".", current_contexts[i + 1])

            # Create merge configuration data
            merge_config = {
                "context-a": context_a,
                "context-b": context_b,
                "function": "merge",
                "ttest-module": "ttest",
                "id": f"{id_counter}"  # Use the id counter for naming
            }

            # Save merge configuration to a JSON file
            merge_config_file = os.path.join(".", f"ttest_merge_{id_counter}.json")
            with open(merge_config_file, 'w') as config_file:
                json.dump(merge_config, config_file, indent=4)
            print(f"Created merge config file: {merge_config_file}")

            # Add the merged context file to the next round
            merged_context = f"ttest-{id_counter}-merged.ctx"
            next_contexts.append(merged_context)

            # Run the merge process
            try:
                print(f"Running stan.exe for {merge_config_file}...")
                result = subprocess.run([stan_exe, merge_config_file], check=True, capture_output=True, text=True)
                print(f"Output for {merge_config_file}:\n{result.stdout}")
            except FileNotFoundError:
                print(f"Error: The file {stan_exe} was not found.")
                return
            except subprocess.CalledProcessError as e:
                print(f"Error while processing {merge_config_file}:\n{e.stderr}")
                return

            # Increment the ID counter
            id_counter += 1

        # Move to the next round
        current_contexts = next_contexts

    # Finalize the last remaining context
    if len(current_contexts) == 1:
        final_context = current_contexts[0]
        finalize_config = {
            "context-a": os.path.join(".", final_context),
            "function": "finalize",
            "ttest-module": "ttest",
            "id": "ttest-0"
        }

        # Save the finalize configuration to a JSON file
        finalize_config_file = os.path.join(".", "ttest_finalize.json")
        with open(finalize_config_file, 'w') as config_file:
            json.dump(finalize_config, config_file, indent=4)
        print(f"Created finalize config file: {finalize_config_file}")

        # Run the finalize process
        try:
            print(f"Running stan.exe for {finalize_config_file}...")
            result = subprocess.run([stan_exe, finalize_config_file], check=True, capture_output=True, text=True)
            print(f"Output for {finalize_config_file}:\n{result.stdout}")
        except FileNotFoundError:
            print(f"Error: The file {stan_exe} was not found.")
        except subprocess.CalledProcessError as e:
            print(f"Error while processing {finalize_config_file}:\n{e.stderr}")

def convert_sicak_tvals(sample_count, output_folder, output_file_name):
    """
    Convert the t-values from the SICAK output files to a more readable format.

    NOTE: The t-values are read from the file "ttest-ttest-0.tvals" in the current working directory.

    Parameters:
        sample_count (int): Number of samples per trace.
        output_folder (str): Path to the folder where the output file will be saved.
        output_file_name (str): Name of the output file (supports .bin or .npy extensions).
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Path to the SICAK t-values file
    tvals_file = os.path.join(".", "ttest-ttest-0.tvals")

    try:
        # Open the t-values file for reading
        with open(tvals_file, "rb") as tvals:
            # Read the specified number of doubles (8 bytes each)
            tvals_data = tvals.read(sample_count * 8)

        # Check the output file extension
        if output_file_name.endswith(".bin"):
            # Save as a binary file
            output_file = os.path.join(output_folder, output_file_name)
            with open(output_file, "wb") as output:
                output.write(tvals_data)
            print(f"Converted {sample_count} doubles from {tvals_file} to {output_file}")

        elif output_file_name.endswith(".npy"):
            # Convert to a numpy array and save as .npy
            tvals_array = np.frombuffer(tvals_data, dtype=np.float64)
            output_file = os.path.join(output_folder, output_file_name)
            np.save(output_file, tvals_array)
            print(f"Converted {sample_count} doubles from {tvals_file} to {output_file} as .npy")

        else:
            raise ValueError("Unsupported output file extension. Use .bin or .npy.")

    except FileNotFoundError:
        print(f"Error: The file {tvals_file} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def clean_up_contexts_configs(folder):
    """
    Clean up the generated files after processing.

    Remove al .ctx and .json files from the specified folder.

    Parameters:
        folder (str): Path to the folder containing generated files.
    """

    # List of file extensions to remove
    extensions_to_remove = ['.ctx', '.json', '.tvals']

    # Iterate over the files in the folder
    for filename in os.listdir(folder):
        # Check if the file starts with "ttest" and has one of the specified extensions
        if filename.startswith("ttest") and any(filename.endswith(ext) for ext in extensions_to_remove):
            file_path = os.path.join(folder, filename)
            try:
                os.remove(file_path)
                print(f"Removed file: {file_path}")
            except OSError as e:
                print(f"Error removing file {file_path}: {e}")

        # Check if the file matches the pattern of entirely numeric filenames with .json extension
        elif filename.endswith(".json") and filename[:-5].isdigit():
            file_path = os.path.join(folder, filename)
            try:
                os.remove(file_path)
                print(f"Removed file: {file_path}")
            except OSError as e:
                print(f"Error removing file {file_path}: {e}")


def perform_t_test(folder, trace_len, file_count, output_file_name, file_equal_prefix, file_not_equal_prefix, stan_exe_path = r".\sicak-1.2.1\stan.exe"):
    """
    Perform the SICAK specific t-test process.

    NOTE: Temporary files are created in the current working directory and in "folder" directory.

    Parameters:
        folder (str): Path to the folder containing sort traces.
        trace_len (int): Number of samples per trace.
        file_count (int): Number of equal and not-equal trace files (e.g., 10 for 0...9).
        output_file_name (str): Name of the output file (supports .bin or .npy extensions).
        file_equal_prefix (str): Prefix for equal traces.
        file_not_equal_prefix (str): Prefix for not-equal traces.
        stan_exe_path (str): Path to the stan.exe tool. Defaults to the relative path. (optional).
    """
    create_config_files(folder, trace_len, file_count, file_equal_prefix, file_not_equal_prefix)
    create_contexts(folder, file_count, stan_exe_path)
    run_merge_and_finalize(file_count, stan_exe=stan_exe_path)  # Assuming chunks is equal to file_count
    convert_sicak_tvals(sample_count=trace_len, 
                        output_folder=folder, 
                        output_file_name=output_file_name)

    clean_up_contexts_configs(".")  # Clean up generated files in the current directory after processing
    clean_up_contexts_configs(folder)  # Clean up generated files after processing


