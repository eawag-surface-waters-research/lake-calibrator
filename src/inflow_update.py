import json
import os

def update_tin_dat_from_par():
    """
    Updates the Tin.dat file based on the parameters in the file.par JSON file.

    Args:
        par_file_path (str): Path to the file.par JSON file.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
    par_file_path = os.path.join(script_dir, 'Calibration.par')
    print(f"Path to file.par: {par_file_path}")
    #par_file_path = r'config_files\file.par'
    try:
        # Step 1: Read the file.par JSON file
        with open(par_file_path, 'r') as par_file:
            config = json.load(par_file)

        # Step 2: Extract relevant paths and parameters
        input_paths = config.get("Input", {})
        model_parameters = config.get("ModelParameters", {})

        tin_dat_path = input_paths.get("Inflow temperature")
        tin_dat_path = os.path.abspath(tin_dat_path)
        print(f"Path to Tin.dat: {tin_dat_path}")
        if not tin_dat_path:
            raise ValueError("Path to Tin.dat file is not provided in 'Input'.")
        
        # Filter T_i_j parameters from model_parameters
        t_ij_parameters = {key: value for key, value in model_parameters.items() if key.startswith("T_")}
        
        # determining whether is the calibration case
        is_calibration = os.path.basename(par_file_path) == "Calibration.par"
        print(f"Is Calibration.par: {is_calibration}")

        # Check if there are T_i_j parameters
        if not t_ij_parameters:
            print("No T_i_j parameters found in 'ModelParameters'. No updates will be made.")
            return

        # Step 3: Read the Tin.dat file
        with open(tin_dat_path, 'r') as tin_file:
            lines = tin_file.readlines()

        # Parse the header and data rows
        header = lines[:3]  # Assume the first three rows are header
        t4_row = list(map(float, lines[-2].split()))
        t5_row = list(map(float, lines[-1].split()))

        # Step 4: Update the rows based on T_i_j parameters
        for key, value in t_ij_parameters.items():
            _, i, j = key.split('_')
            i, j = int(i), int(j)
            
            # Handle Calibration.par case
            if is_calibration:
                 value = float(value)

            # Ensure T_4_j and T_5_j are updated equally
            if i == 4:
                t4_row[j] = value
                t5_row[j] = value
            elif i == 5:
                t4_row[j] = value
                t5_row[j] = value

        # Step 5: Write updated data back to Tin.dat
        with open(tin_dat_path, 'w') as tin_file:
            # Write the header
            for line in header:
                tin_file.write(line)
            # Write the updated rows
            tin_file.write(' '.join(map(str, t4_row)) + '\n')
            tin_file.write(' '.join(map(str, t5_row)) + '\n')

        print(f"Tin.dat file successfully updated at {tin_dat_path}.")
    
    except Exception as e:
        print(f"An error occurred: {e}")



update_tin_dat_from_par()
