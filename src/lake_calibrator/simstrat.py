import os
import json
import shutil
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.interpolate import interp1d
from .functions import parse_observation_file, days_since_year


def edit_par_file(folder, initial=False, parameter_names=[], parameter_values=[], end_date=False):
    par_files = [f for f in os.listdir(folder) if f.endswith(".par")]
    par_file = os.path.join(folder, par_files[0])
    with open(par_file) as f:
        data = json.load(f)

    if initial:
        data["Output"]["Depths"] = "z_out.dat"
        data["Output"]["Times"] = "t_out.dat"
        data["Output"]["Path"] = "Results"
        data["Output"]["All"] = False

        data["Simulation"]["DisplaySimulation"] = 0
        data["Simulation"]["Continue from last snapshot"] = False
        data["Simulation"]["Show progress bar"] = False
        data["Simulation"]["Save text restart"] = False
        data["Simulation"]["Use text restart"] = False

    if end_date:
        data["Simulation"]["End d"] = end_date

    if len(parameter_names) > 0 and len(parameter_names) == len(parameter_values):
        for index, parameter in enumerate(parameter_names):
            data["ModelParameters"][parameter] = parameter_values[index]
    with open(par_file, "w") as f:
        json.dump(data, f, indent=4)
    return data


def copy_simstrat_inputs(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    par_files = [f for f in os.listdir(src) if f.endswith(".par")]
    if len(par_files) != 1:
        raise ValueError("Only 1 PAR file permitted in simulation folder ({} detected)".format(len(par_files)))
    if par_files[0] == "Calibration.par":
        raise ValueError("PAR file must not be called Calibration.par")
    shutil.copy2(os.path.join(src, par_files[0]), os.path.join(dst, "Calibration.par"))
    for item in os.listdir(src):
        if item.endswith(".par"):
            continue
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if os.path.basename(s) != "Results":
                shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

def simstrat_rms(objective_variables, objective_weights, observations, reference_year, folder):
    residuals = 0
    weights = 0
    for i, objective_variable in enumerate(objective_variables):
        if objective_variable == "temperature":
            obs = [o for o in observations if o["parameter"] == "temperature"]
            if len(obs) != 1:
                raise ValueError("Cannot find temperature observations to calculate residuals")
            obs = obs[0]
            df_obs = parse_observation_file(obs["file"], datetime.fromisoformat(obs["start"]), datetime.fromisoformat(obs["end"]))
            df_sim = parse_output_file(os.path.join(folder, "T_out.dat"), reference_year)
            df_sim = df_sim.reset_index().melt(id_vars='time', var_name='depth', value_name='value')
            df_sim['depth'] = df_sim['depth'].astype(float) * -1
            df_sim['time'] = df_sim['time'].dt.round('min')
            df = df_obs.merge(df_sim, on=['time', 'depth'], how='left', suffixes=('_obs', '_sim'))
            df = df.dropna()
            df["residuals"] = (objective_weights[i] * df["weight"] * (df["value_obs"] - df["value_sim"]) ** 2)
            df["obj_weights"] = (objective_weights[i] * df["weight"])
            residuals = residuals + df['residuals'].sum()
            weights = weights + df['obj_weights'].sum()
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
    with open(os.path.join(calibration_folder, "z_out.dat"), 'w') as file:
        file.write("output depths\n")
        for z in depths:
            file.write("%.2f\n" % -abs(z))
    with open(os.path.join(calibration_folder, "t_out.dat"), 'w') as file:
        file.write("output times\n")
        for t in times:
            file.write("%.4f\n" % days_since_year(t, reference_year))

def simstrat_max_depth(simulation_folder, bathymetry_file):
    df = pd.read_csv(os.path.join(simulation_folder, bathymetry_file), skiprows=1, sep='\s+', header=None)
    return abs(df.iloc[:, 0].min())
