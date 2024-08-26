import os
import json
import shutil
import numpy as np
import pandas as pd
from .functions import run_subprocess, parse_observation_file
from .simstrat import set_simstrat_outputs

def pest_calibrate(args, log):
    log.info("Calibrating {} with PEST".format(args["simulation"]))
    pest_input_files(args, log)
    exit()
    log.info("Running PEST")
    cmd = ("docker run -v /var/run/docker.sock:/var/run/docker.sock -v {}:/pest/calibrate --rm "
           "eawag/pest_hp:18.0.0 -f pest -a {} -p {}".format(os.path.abspath(args["calibration_folder"]),
                                                                 args["calibration_options"]["agents"],
                                                                 args["calibration_options"]["port"]))
    log.info(cmd, indent=1)
    debug = "debug" in args["calibration_options"] and args["calibration_options"]["debug"]
    run_subprocess(cmd, debug=debug)
    log.info("PEST completed, reading output files.")
    result = pest_output_files(args["calibration_folder"])
    return result

def pest_input_files(args, log):
    log.info("Copying model input files", indent=1)
    copy_model_inputs(args["calibration_folder"], args["simulation_folder"])

    log.info("Reading observation data", indent=1)
    times, depths, observations = read_observation_data(args["calibration_options"], args["observations"])

    log.info("Creating PEST run file", indent=1)
    write_pest_run_file(args["calibration_folder"], args["execute"])

    log.info("Creating PEST .tpl file", indent=1)
    config = write_pest_tpl_file(args["calibration_folder"], args["simulation_folder"], args["parameters"], args["simulation"])

    if args["simulation"] == "simstrat":
        log.info("Setting Simstrat output files", indent=1)
        set_simstrat_outputs(args["calibration_folder"], times, depths, config["Simulation"]["Reference year"])

    log.info("Creating PEST .ins files", indent=1)
    combined_observations = write_pest_ins_file(args["calibration_folder"], args["calibration_options"], args["simulation"], observations, times, depths)

    log.info("Creating PEST .pst file", indent=1)
    write_pest_pst_file(args["calibration_folder"], args["simulation_folder"], args["parameters"], args["simulation"], args["calibration_options"], combined_observations)

def copy_model_inputs(calibration_folder, simulation_folder):
    output_folder = os.path.join(calibration_folder, "inputs")
    os.makedirs(output_folder)
    for item in os.listdir(simulation_folder):
        file = os.path.join(simulation_folder, item)
        if os.path.isfile(file):
            shutil.copy2(file, output_folder)
        elif item != "Results":
            shutil.copytree(file, os.path.join(output_folder, item))

def read_observation_data(calibration_options, observations):
    times = []
    depths = []
    for objective_variable in calibration_options["objective_variables"]:
        obs_ids = [i for i in range(len(observations)) if observations[i]["parameter"] == objective_variable]
        if len(obs_ids) != 1:
            raise ValueError("Cannot find {} observations to calculate residuals".format(objective_variable))
        obs = observations[obs_ids[0]]
        df = parse_observation_file(obs["file"], obs["start"], obs["end"])
        times.extend(df.index.tolist())
        depths.extend([d for d in df["depth"].tolist() if not np.isnan(d)])
        observations[obs_ids[0]]["df"] = df
    times = sorted(set(times))
    depths = sorted(set(depths))
    return times, depths, observations

def write_pest_run_file(calibration_folder, execute):
    with open(os.path.join(calibration_folder, "run.sh"), 'w') as file:
        file.write('#!/bin/bash\n')
        file.write('dir="$(dirname "$(realpath "$0")")"\n')
        file.write('folder=$(basename "$(dirname "$(realpath "$0")")")\n')
        file.write('cp -r "/pest/calibrate/inputs"/* "$dir"/\n')
        file.write(execute.format(calibration_folder=os.path.abspath(calibration_folder) + "/$folder"))
    os.chmod(os.path.join(calibration_folder, "run.sh"), 0o755)

def write_pest_pst_file(calibration_folder, simulation_folder, parameters, simulation, calibration_options, combined_observations):
    if simulation == "simstrat":
        file_dict = {
            "temperature": "Results/T_out.dat"
        }
        par_file = "Calibration.par"

    with open(os.path.join(calibration_folder, "pest.pst"), 'w') as file:
        file.write('pcf\n')
        file.write('* control data\n')
        file.write('norestart estimation\n')
        file.write('%d %d 1 0 %d\n' % (len(parameters), len(combined_observations), len(calibration_options["objective_variables"])))
        file.write('1 %d single nopoint 1 0 0\n' % len(calibration_options["objective_variables"]))
        file.write('5.0 2.0 0.3 0.01 10 run_abandon_fac=1.5\n')
        file.write('5.0 5.0 0.001\n')
        file.write('0.1\n')
        file.write('20 0.005 4 3 0.01 3\n')
        file.write('0 0 0\n')
        file.write('* parameter groups\n')
        file.write(' fit\trelative\t0.01\t0.00001\tswitch\t2.0\tparabolic\n')
        file.write('* parameter data\n')
        for parameter in parameters:
            adjust = "factor"
            if "adjust" in parameter:
                adjust = parameter["adjust"]
            file.write('%6s\t%s\t%s\t%10.4e\t%10.4e\t%10.4e\t%4s\t1.0\t0.0\t1\n' % (
            parameter["name"], "none", adjust, parameter["initial"], parameter["min"], parameter["max"], "fit"))
        file.write('* observation groups\n')
        for objective_variable in calibration_options["objective_variables"]:
            file.write('{}\n'.format(objective_variable))
        file.write('* observation data\n')
        for index, row in combined_observations.iterrows():
            file.write('%-20s\t%12.4e\t%f\t%s\n' % (row["id"], row["value"], row["weight"], row["id"].split("_")[0]))
        file.write('* model command line\n')
        file.write('./run.sh\n')
        file.write('* model input/output\n')
        file.write('pest.tpl	{}\n'.format(par_file))
        for objective_variable in calibration_options["objective_variables"]:
            if objective_variable not in file_dict:
                raise ValueError("{} not defined in file dictionary.".format(objective_variable))
            file.write('{}.ins	{}\n'.format(objective_variable, file_dict[objective_variable]))
        file.write('* prior information\n')

def write_pest_tpl_file(calibration_folder, simulation_folder, parameters, simulation):
    if simulation == "simstrat":
        par_files = [file for file in os.listdir(simulation_folder) if file.endswith(".par")]
        if len(par_files) != 1:
            raise ValueError("{} PAR files located in simulation folder".format(len(par_files)))
        with open(os.path.join(simulation_folder, par_files[0]), 'r') as file:
            config = json.load(file)
        for parameter in parameters:
            config["ModelParameters"][parameter["name"]] = '$$%10s$$' % parameter["name"]
        config["Simulation"]["Continue from last snapshot"] = False
        config_text = json.dumps(config)
        config_text = config_text.replace('$$"', '#"').replace('"$$', '"#')
        config_text = config_text.replace('}', '\n}').replace(', ', ',\n').replace('{', '{\n')
    else:
        raise ValueError("write_pest_tpl_file not implemented for simulation: {}".format(simulation))
    with open(os.path.join(calibration_folder, "pest.tpl"), 'w') as file:
        file.write('ptf #\n')
        file.write(config_text)
    return config

def write_pest_ins_file(calibration_folder, calibration_options, simulation, observations, times, depths):
    combined_observations = []
    depths_desc = sorted(depths, reverse=True)
    for objective_variable in calibration_options["objective_variables"]:
        obs_ids = [i for i in range(len(observations)) if observations[i]["parameter"] == objective_variable]
        if len(obs_ids) != 1:
            raise ValueError("Cannot find {} observations to calculate residuals".format(objective_variable))
        df = observations[obs_ids[0]]["df"]
        with open(os.path.join(calibration_folder, "{}.ins".format(objective_variable)), 'w') as file:
            file.write('pif @\n')
            if simulation == "simstrat":
                file.write('l1\n')
                for i, t in enumerate(times):
                    if t in df.index:
                        strf = 'l1'
                        df_t = df.loc[t]
                        for j, d in enumerate(depths_desc):
                            if d in df_t['depth'].values:
                                row = df_t[df_t['depth'] == d].iloc[0]
                                strf = strf + ' @,@ !%s_%d_%d!' % (objective_variable, i, j)
                                combined_observations.append({
                                    'id': f"{objective_variable}_{i}_{j}",
                                    'value': row["value"],
                                    'weight': row["weight"]
                                })
                            else:
                                strf = strf + ' @,@'
                        file.write(strf + '\n')
            else:
                raise ValueError("write_pest_ins_file not implemented for simulation: {}".format(simulation))
    combined_observations = pd.DataFrame(combined_observations, columns=['id', 'value', 'weight'])
    return combined_observations

def pest_output_files(calibration_folder):
    if not os.path.exists(os.path.join(calibration_folder, "pest.par")):
        raise ValueError("PEST failed to complete, run in debug mode to see log for more details.")
    df = pd.read_csv(os.path.join(calibration_folder, "pest.par"), skiprows=1, header=None, delim_whitespace=True)
    dfe = pd.read_csv(os.path.join(calibration_folder, "pest.res"), delim_whitespace=True)
    dfe["Residual2*Weight"] = dfe["Weight"] * dfe["Residual"] ** 2
    error = (dfe['Residual2*Weight'].sum() / dfe["Weight"].sum()) ** 0.5
    return {
        "parameters": dict(zip(df.iloc[:, 0], df.iloc[:, 1])),
        "error": error
    }