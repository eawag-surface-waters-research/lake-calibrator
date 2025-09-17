import os
import json
import shutil
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from .functions import parse_observation_file, days_since_year


def edit_par_file(folder, parameter_names, parameter_values):
    par_files = [f for f in os.listdir(folder) if f.endswith(".par")]
    if len(par_files) != 1:
        raise ValueError("Could not locate par file")
    par_file = os.path.join(folder, par_files[0])
    with open(par_file) as f:
        data = json.load(f)
    reference_year = data["Simulation"]["Reference year"]
    if data["Output"]["Depths"] != "z_out.dat":
        raise ValueError('Simstrat PAR file - Output Depths must be set to "z_out.dat"')
    if data["Output"]["Times"] != "t_out.dat":
        raise ValueError('Simstrat PAR file - Output Times must be set to "t_out.dat"')
    for index, parameter in enumerate(parameter_names):
        data["ModelParameters"][parameter] = parameter_values[index]
    with open(par_file, "w") as f:
        json.dump(data, f, indent=4)
    return reference_year


def copy_simstrat_inputs(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if os.path.basename(s) != "Results":
                shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

def simstrat_rms(objective_variables, objective_weights, time_mode, depth_mode, observations, reference_year, folder):
    residuals = 0
    weights = 0
    for i, objective_variable in enumerate(objective_variables):
        if objective_variable == "temperature":
            obs = [o for o in observations if o["parameter"] == "temperature"]
            if len(obs) != 1:
                raise ValueError("Cannot find temperature observations to calculate residuals")
            obs = obs[0]
            df_obs = parse_observation_file(obs["file"], obs["start"], obs["end"])
            df_sim = parse_output_file(os.path.join(folder, "T_out.dat"), reference_year)
            for index, row in df_obs.iterrows():
                if time_mode == "nearest":
                    time_index = df_sim.index.get_indexer([index], method='nearest')[0]
                else:
                    raise ValueError("Please select time_mode from [nearest]")
                sim_row = df_sim.iloc[time_index]
                if depth_mode == "linear_interpolation":
                    x = sim_row.index.to_numpy().astype(float) * -1
                    y = sim_row.values.astype(float)
                    d = float(row["depth"])
                    if d < np.min(x) or d > np.max(x):
                        continue
                    idx = np.argmax(x == d)
                    if x[idx] == d:
                        sim_value = y[idx]
                    else:
                        f = interp1d(x, y, kind='linear')
                        sim_value = f(d)
                else:
                    raise ValueError("Please select depth_mode from [linear_interpolation]")
                residuals = residuals + (objective_weights[i] * row["weight"] * (row["value"] - sim_value) ** 2)
                weights = weights + (objective_weights[i] * row["weight"])
        else:
            raise ValueError("Not implemented for objective variable {}".format(objective_variable))
    return (residuals / weights) ** 0.5

def parse_output_file(file, reference_year):
    df = pd.read_csv(file)
    base_date = pd.Timestamp('{}-01-01'.format(reference_year))
    df["time"] = (base_date + pd.to_timedelta(df['Datetime'], unit='D')).dt.tz_localize('UTC')
    df = df.drop('Datetime', axis=1)
    df = df.set_index('time')
    df = df.sort_index()
    return df

def set_simstrat_outputs(calibration_folder, times, depths, reference_year):
    if len(depths) < 2:
        raise ValueError("There is a single output depth in file (probably because there are observations only at one depth). This will be misunderstood by Simstrat.")
    with open(os.path.join(calibration_folder, "inputs", "z_out.dat"), 'w') as file:
        file.write("output depths\n")
        for z in depths:
            file.write("%.2f\n" % -abs(z))
    with open(os.path.join(calibration_folder, "inputs", "t_out.dat"), 'w') as file:
        file.write("output times\n")
        for t in times:
            file.write("%.4f\n" % days_since_year(t, reference_year))

def simstrat_max_depth(simulation_folder, bathymetry_file):
    df = pd.read_csv(os.path.join(simulation_folder, bathymetry_file), skiprows=1, delim_whitespace=True, header=None)
    return abs(df.iloc[:, 0].min())
