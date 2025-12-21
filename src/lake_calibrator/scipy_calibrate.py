import os
import shutil
from datetime import datetime
from dateutil.relativedelta import relativedelta
from scipy.optimize import minimize
from .simstrat import edit_par_file, copy_simstrat_inputs, simstrat_rms, simstrat_max_depth, set_simstrat_outputs
from .functions import run_subprocess, read_observation_data, datetime_from_days, days_since_year

iteration = 1
run = 0

def scipy_calibrate(args, log):
    log.info("Calibrating {} with Scipy {}".format(args["simulation"], args["calibration_options"]["method"]))

    x0 = [parameter["initial"] for parameter in args["parameters"]]
    bounds = tuple(tuple([parameter["min"], parameter["max"]]) for parameter in args["parameters"])
    parameter_names = [parameter["name"] for parameter in args["parameters"]]

    if "Calibration.par" not in args["execute"]:
        raise ValueError('Execute command in argument file should contain "Calibration.par" NOT the name of your par file.')

    if args["simulation"] == "simstrat":
        base_folder = os.path.join(args["calibration_folder"], "base")
        copy_simstrat_inputs(args["simulation_folder"], base_folder)
        config = edit_par_file(base_folder, initial=True)
        if "burn_in_days" in args["calibration_options"]:
            log.info('Using burn in period of {} days'.format(args["calibration_options"]["burn_in_days"]), indent=2)
            start_date = datetime_from_days(config["Simulation"]["Start d"], config["Simulation"]["Reference year"]) + relativedelta(days=args["calibration_options"]["burn_in_days"])
        else:
            log.info('"burn_in_days" not defined in calibration_options, using default of 365 days', indent=2)
            start_date = datetime_from_days(config["Simulation"]["Start d"], config["Simulation"]["Reference year"]) + relativedelta(years=1)
        end_date = datetime_from_days(config["Simulation"]["End d"], config["Simulation"]["Reference year"])
        max_depth = simstrat_max_depth(args["simulation_folder"], config["Input"]["Morphology"])
        times, depths, observations = read_observation_data(args["calibration_options"], args["observations"], start_date, end_date, max_depth)
        if times[-1] + relativedelta(days=1) < end_date:
            log.info("Editing PAR file to stop simulation at last observation", indent=1)
            end_date = days_since_year(times[-1] + relativedelta(days=1), config["Simulation"]["Reference year"])
            edit_par_file(base_folder, end_date=end_date)
        log.info("Setting Simstrat output files", indent=1)
        set_simstrat_outputs(base_folder, times, depths, config["Simulation"]["Reference year"])
        fun = simstrat304_iterator
    else:
        raise ValueError("Not implemented for {}".format(args["simulation"]))

    if args["calibration_options"]["method"] == "Nelder-Mead":
        options = {
            "maxfev": args["calibration_options"]["maxfev"],
            "disp": args["calibration_options"]["disp"],
            "fatol": args["calibration_options"]["fatol"],
            "xatol": args["calibration_options"]["xatol"]
        }
    else:
        raise ValueError("Not implemented for {}".format(args["calibration_options"]["method"]))

    def iteration_information(p):
        global iteration
        log.info("Iteration {}".format(iteration), indent=1)
        iteration += 1

    iteration_information([])

    results = minimize(
        fun=fun,
        x0=x0,
        args=(args, log),
        method=args["calibration_options"]["method"],
        bounds=bounds,
        options=options,
        callback=iteration_information
    )

    if not results.success:
        raise ValueError("Optimizer existed unsuccessfully: {}".format(results.message))

    log.info("Running final simulation with optimal parameters", indent=1)
    final_folder = os.path.abspath(os.path.join(args["calibration_folder"], "final"))
    shutil.copytree(os.path.join(args["calibration_folder"], "base"), final_folder)
    config = edit_par_file(final_folder, parameter_names=parameter_names, parameter_values=results.x)
    reference_year = config["Simulation"]["Reference year"]
    run_subprocess(args["execute"].format(calibration_folder=final_folder), cwd=final_folder)
    calib = args["calibration_options"]
    error = simstrat_rms(calib["objective_variables"], calib["objective_weights"], args["observations"], reference_year,
                         os.path.join(final_folder, "Results"))

    return {
        "parameters": dict(zip(parameter_names, results["x"])),
        "error": error
    }

def simstrat304_iterator(parameter_values, args, log):
    log.info("Running: [{}]".format(", ".join(map(str, parameter_values))), indent=2)
    global run
    folder = os.path.abspath(os.path.join(args["calibration_folder"], "{}_{}".format(iteration, run)))
    shutil.copytree(os.path.join(args["calibration_folder"], "base"), folder)
    parameter_names = [parameter["name"] for parameter in args["parameters"]]
    config = edit_par_file(folder, parameter_names=parameter_names, parameter_values=parameter_values)
    reference_year = config["Simulation"]["Reference year"]
    run_subprocess(args["execute"].format(calibration_folder=folder), cwd=folder)
    calib = args["calibration_options"]
    if calib["objective_function"] == "rms":
        error = simstrat_rms(calib["objective_variables"],
                             calib["objective_weights"],
                             args["observations"],
                             reference_year,
                             os.path.join(folder, "Results"))
    else:
        raise ValueError("Unrecognized objective function {}".format(calib["objective_function"]))
    shutil.rmtree(folder)
    log.info("Error: {}".format(error["overall"]), indent=3)
    run += 1
    return error["overall"]
