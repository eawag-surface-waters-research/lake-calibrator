import os
import json
import time
import shutil
import socket
import platform
import subprocess

import numpy as np
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

from .functions import run_subprocess, read_observation_data, list_from_selection, datetime_from_days, days_since_year
from .simstrat import set_simstrat_outputs, simstrat_max_depth

def pest_calibrate(args, log):
    log.info("Calibrating {} with PEST".format(args["simulation"]))
    if "docker_host_calibration_folder" not in args:
        args["docker_host_calibration_folder"] = os.path.abspath(args["calibration_folder"])
    observations = pest_input_files(args, log)
    if "run" in args["calibration_options"] and not args["calibration_options"]["run"]:
        log.info("Not running PEST, existing after producing inputs.")
        return {}
    log.info("Running PEST")
    if "Calibration.par" not in args["execute"]:
        raise ValueError('Execute command in argument file should contain "Calibration.par" NOT the name of your par file.')
    if "docker" in args["calibration_options"] and not args["calibration_options"]["docker"]:
        pest_local(args["calibration_options"], args["calibration_folder"], args["execute"])
    else:
        cmd = ("docker run -v /var/run/docker.sock:/var/run/docker.sock -v {}:/pest/calibrate --rm "
               "eawag/pest_hp:18.0.0 -f pest -a {} -p {}".format(args["docker_host_calibration_folder"],
                                                                     args["calibration_options"]["agents"],
                                                                     args["calibration_options"]["port"]))
        log.info(cmd, indent=1)
        debug = "debug" in args["calibration_options"] and args["calibration_options"]["debug"]
        run_subprocess(cmd, debug=debug)
    log.info("PEST completed, reading output files.")
    result = pest_output_files(args["calibration_folder"])
    result["observations"] = observations
    return result

def pest_input_files(args, log):
    log.info("Copying model input files", indent=1)
    input_folder = os.path.join(args["calibration_folder"], "inputs")
    copy_model_inputs(input_folder, args["simulation_folder"])

    log.info("Creating PEST .tpl file", indent=1)
    config = write_pest_tpl_file(args["calibration_folder"], args["simulation_folder"], args["parameters"], args["simulation"])

    if args["simulation"] == "simstrat":
        if "burn_in_days" in args["calibration_options"]:
            log.info('Using burn in period of {} days'.format(args["calibration_options"]["burn_in_days"]), indent=2)
            start_date = datetime_from_days(config["Simulation"]["Start d"], config["Simulation"]["Reference year"]) + relativedelta(days=args["calibration_options"]["burn_in_days"])
        else:
            log.info('"burn_in_days" not defined in calibration_options, using default of 365 days', indent=2)
            start_date = datetime_from_days(config["Simulation"]["Start d"], config["Simulation"]["Reference year"]) + relativedelta(years=1)
        end_date = datetime_from_days(config["Simulation"]["End d"], config["Simulation"]["Reference year"])
        max_depth = simstrat_max_depth(args["simulation_folder"], config["Input"]["Morphology"])
    else:
        raise ValueError("Input files not implemented for {}".format(args["simulation"]))

    log.info("Reading observation data", indent=1)
    times, depths, observations = read_observation_data(args["calibration_options"], args["observations"], start_date, end_date, max_depth)

    log.info("Creating PEST run file", indent=1)
    run_file = write_pest_run_file(args["calibration_folder"], args["docker_host_calibration_folder"], args["execute"], args["calibration_options"])

    if args["simulation"] == "simstrat":
        if times[-1] + relativedelta(days=1) < end_date:
            log.info("Editing PEST .tpl file to stop simulation at last observation", indent=1)
            overwrite_simstrat_tpl(args["calibration_folder"], times[-1], config["Simulation"]["Reference year"])
        log.info("Setting Simstrat output files", indent=1)
        set_simstrat_outputs(input_folder, times, depths, config["Simulation"]["Reference year"])

    log.info("Creating PEST .ins files", indent=1)
    combined_observations = write_pest_ins_file(args["calibration_folder"], args["calibration_options"], args["simulation"], observations, times, depths)

    log.info("Creating PEST .pst file", indent=1)
    write_pest_pst_file(args["calibration_folder"], args["simulation_folder"], args["parameters"], args["simulation"], args["calibration_options"], combined_observations, run_file)

    observations_summary = {}
    for obv in observations:
        observations_summary[obv["parameter"]] = {"times": len(set(obv["df"].index)), "depths": len(set(obv["df"]["depth"])), "total": len(obv["df"])}
    return observations_summary

def copy_model_inputs(output_folder, simulation_folder):
    os.makedirs(output_folder)
    for item in os.listdir(simulation_folder):
        file = os.path.join(simulation_folder, item)
        if file.lower().endswith(".par"):
            continue
        if os.path.isfile(file):
            shutil.copy2(file, output_folder)
        elif item != "Results":
            shutil.copytree(file, os.path.join(output_folder, item))

def write_pest_run_file(calibration_folder, docker_host_calibration_folder, execute, calibration_options):
    if "docker" in calibration_options and not calibration_options["docker"]:
        if platform.system() != 'Linux':
            return "run.bat"
    else:
        with open(os.path.join(calibration_folder, "run.sh"), 'w') as file:
            file.write('#!/bin/bash\n')
            file.write('dir="$(dirname "$(realpath "$0")")"\n')
            file.write('folder=$(basename "$(dirname "$(realpath "$0")")")\n')
            file.write('cp -r "/pest/calibrate/inputs"/* "$dir"/\n')
            file.write(execute.format(calibration_folder=docker_host_calibration_folder + "/$folder") + "\n")
            file.write('echo "Run Complete"')
        os.chmod(os.path.join(calibration_folder, "run.sh"), 0o755)
    return "./run.sh"

def write_pest_pst_file(calibration_folder, simulation_folder, parameters, simulation, calibration_options, combined_observations, run_file):
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
            file.write('%-12s\t%12.4e\t%f\t%s\n' % (row["id"], row["value"], row["weight"], row["group"]))
        file.write('* model command line\n')
        file.write("{}\n".format(run_file))
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
            raise ValueError("Only 1 PAR file permitted in simulation folder ({} detected)".format(len(par_files)))
        if par_files[0] == "Calibration.par":
            raise ValueError("PAR file must not be called Calibration.par, this will cause PEST to fail.")
        with open(os.path.join(simulation_folder, par_files[0]), 'r') as file:
            config = json.load(file)
        for parameter in parameters:
            config["ModelParameters"][parameter["name"]] = '$$%10s$$' % parameter["name"]

        config["Output"]["Depths"] = "z_out.dat"
        config["Output"]["Times"] = "t_out.dat"
        config["Output"]["Path"] = "Results"
        config["Output"]["All"] = False

        config["Simulation"]["DisplaySimulation"] = 0
        config["Simulation"]["Continue from last snapshot"] = False
        config["Simulation"]["Show progress bar"] = False
        config["Simulation"]["Save text restart"] = False
        config["Simulation"]["Use text restart"] = False

        config_text = json.dumps(config)
        config_text = config_text.replace('$$"', '#"').replace('"$$', '"#')
        config_text = config_text.replace('}', '\n}').replace(', ', ',\n').replace('{', '{\n')
    else:
        raise ValueError("write_pest_tpl_file not implemented for simulation: {}".format(simulation))
    with open(os.path.join(calibration_folder, "pest.tpl"), 'w') as file:
        file.write('ptf #\n')
        file.write(config_text)
    return config

def overwrite_simstrat_tpl(calibration_folder, end_date, reference_year):
    with open(os.path.join(calibration_folder, "pest.tpl"), 'r') as file:
        lines = file.readlines()
    modified_lines = []
    for line in lines:
        if "End d" in line:
            new_line = f'"End d": {days_since_year(end_date + relativedelta(days=1), reference_year)},\n'
            modified_lines.append(new_line)
        else:
            modified_lines.append(line)

    with open(os.path.join(calibration_folder, "pest.tpl"), 'w') as file:
        file.writelines(modified_lines)


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
                            if d in list_from_selection(df_t['depth']):
                                if isinstance(df_t, pd.DataFrame):
                                    row = df_t[df_t['depth'] == d].iloc[0]
                                else:
                                    row = df_t
                                strf = strf + ' @,@ !%s_%d_%d!' % (objective_variable[0], i, j)
                                combined_observations.append({
                                    'id': f"{objective_variable[0]}_{i}_{j}",
                                    'value': row["value"],
                                    'weight': row["weight"],
                                    'group': objective_variable
                                })
                            else:
                                strf = strf + ' @,@'
                        if len(strf) > 2000:
                            raise ValueError("Instruction file .ins: line exceeds 2000 characters - reduce the number of depths in the observations file.")
                        file.write(strf + '\n')
            else:
                raise ValueError("write_pest_ins_file not implemented for simulation: {}".format(simulation))
    combined_observations = pd.DataFrame(combined_observations, columns=['id', 'value', 'weight', 'group'])
    return combined_observations


def weighted_rms(g):
    return np.sqrt(g["Residual2*Weight"].sum() / g["Weight"].sum())


def pest_output_files(calibration_folder):
    if not os.path.exists(os.path.join(calibration_folder, "pest.par")):
        raise ValueError("PEST failed to complete, run in debug mode to see log for more details.")
    df = pd.read_csv(os.path.join(calibration_folder, "pest.par"), skiprows=1, header=None, delim_whitespace=True)
    dfe = pd.read_csv(os.path.join(calibration_folder, "pest.res"), delim_whitespace=True)
    dfe["Residual2*Weight"] = dfe["Weight"] * dfe["Residual"] ** 2
    dfe["depth_id"] = dfe['Name'].str.split('_').str[-1].astype(int)
    dfb = dfe[dfe['depth_id'] == dfe['depth_id'].min()]
    dfs = dfe[dfe['depth_id'] == dfe['depth_id'].max()]
    overall = (dfe['Residual2*Weight'].sum() / dfe["Weight"].sum()) ** 0.5
    bottom = (dfb['Residual2*Weight'].sum() / dfb["Weight"].sum()) ** 0.5
    surface = (dfs['Residual2*Weight'].sum() / dfs["Weight"].sum()) ** 0.5

    out = {
        "parameters": dict(zip(df.iloc[:, 0], df.iloc[:, 1])),
        "error": {
            "overall": overall,
            "surface": surface,
            "bottom": bottom
        }
    }

    try:
        dfd = dfe.groupby("depth_id").apply(
            lambda g: pd.Series({
                "rmse": weighted_rms(g),
                "count": len(g)
            })).reset_index()
        result_file = os.path.join(calibration_folder, "agent1/Results/T_out.dat")
        depths = np.abs(np.loadtxt(result_file, delimiter=",", max_rows=1, dtype=str)[1:].astype(float))
        dfd["depth_id"] = depths
        dfd.columns = ["depth", "rmse", "count"]
        out["error"]["by_depth"] = dfd.to_dict(orient='list')
    except:
        print("Failed to extract RMSE error per depth")

    return out

def pest_local_cleanup():
    if platform.system() == 'Linux':
        try:
            process_list = subprocess.check_output(['ps', '-e', '-o', 'pid,comm'], universal_newlines=True).splitlines()[1:]
        except subprocess.CalledProcessError:
            process_list = []
        for process in process_list:
            try:
                process_id, process_name = process.split(None, 1)
                if "pest_hp" in process_name or "agent_hp" in process_name:
                    os.kill(int(process_id), 9)
                    print(f"Killed {process_name} process with PID {process_id}")
                    time.sleep(1)
            except (ValueError, PermissionError, ProcessLookupError):
                continue
    else:
        os.system('taskkill /F /IM pest_hp.exe /T 2>nul')

def pest_local(calibration_options, calibration_folder, execute):
    if "local_compilation_pest" not in calibration_options:
        raise ValueError("local_compilation_pest must be defined in calibration_options to run PEST without docker")
    if "local_compilation_agent" not in calibration_options:
        raise ValueError("local_compilation_agent must be defined in calibration_options to run PEST without docker")
    pest_local_cleanup()
    proc = []
    ip_address = socket.gethostbyname(socket.gethostname())
    calibration_folder = os.path.abspath(calibration_folder)
    cmd = [calibration_options["local_compilation_pest"], "pest.pst", "/h", ":{}".format(calibration_options["port"])]
    p = subprocess.Popen(cmd, cwd=calibration_folder)
    proc.append(p)
    for i in range(calibration_options["agents"]):
        agent_dir = os.path.join(calibration_folder, f"agent{i}")
        os.makedirs(agent_dir, exist_ok=True)
        for file in os.listdir(calibration_folder):
            if file.endswith((".pst", ".tpl", ".ins", ".sh")):
                try:
                    shutil.copy(os.path.join(calibration_folder, file), agent_dir)
                except FileNotFoundError:
                    continue
        if platform.system() == 'Linux':
            with open(os.path.join(agent_dir, "run.sh"), 'w') as file:
                file.write('#!/bin/bash\n')
                file.write('cp -r "{}"/* "{}"/\n'.format(os.path.join(calibration_folder, "inputs"), agent_dir))
                file.write(execute.format(calibration_folder=agent_dir))
            os.chmod(os.path.join(agent_dir, "run.sh"), 0o755)
        else:
            with open(os.path.join(agent_dir, "run.bat"), 'w') as file:
                file.write(
                    'xcopy "{}" "{}" /E /I /Y\n'.format(os.path.join(calibration_folder, "inputs", "*"), agent_dir))
                file.write(execute.format(calibration_folder=agent_dir))
        cmd = [calibration_options["local_compilation_agent"], "pest.pst", "/h", "{}:{}".format(ip_address, calibration_options["port"])]
        p = subprocess.Popen(cmd, cwd=agent_dir)
        proc.append(p)
    for p in proc:
        out = p.wait()