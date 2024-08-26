import os
import shutil
from scipy.optimize import minimize
from simstrat import edit_par_file, copy_simstrat_inputs, simstrat_rms
from functions import run_subprocess

iteration = 0
run = 0

def scipy_calibrate(args, log):
    log.info("Calibrating {} with Scipy {}".format(args["simulation"], args["calibration_options"]["method"]))

    x0 = [parameter["initial"] for parameter in args["parameters"]]
    bounds = tuple(tuple([parameter["min"], parameter["max"]]) for parameter in args["parameters"])
    parameter_names = [parameter["name"] for parameter in args["parameters"]]

    if args["simulation"] == "simstrat":
        fun = simstrat304_iterator

    if args["calibration_options"]["method"] == "Nelder-Mead":
        options = {
            "maxfev": args["calibration_options"]["maxfev"],
            "disp": args["calibration_options"]["disp"],
            "fatol": args["calibration_options"]["fatol"],
            "xatol": args["calibration_options"]["xatol"]
        }

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

    return {
        "parameters": dict(zip(parameter_names, results["x"])),
        "error": results["fun"]
    }

def simstrat304_iterator(parameter_values, args, log):
    log.info("Running: [{}]".format(", ".join(map(str, parameter_values))), indent=2)
    global run
    folder = os.path.abspath(os.path.join(args["calibration_folder"], "{}_{}".format(iteration, run)))
    copy_simstrat_inputs(args["simulation_folder"], folder)
    parameter_names = [parameter["name"] for parameter in args["parameters"]]
    reference_year = edit_par_file(folder, parameter_names, parameter_values)
    run_subprocess(args["execute"].format(calibration_folder=folder))
    calib = args["calibration_options"]
    if calib["objective_function"] == "rms":
        error = simstrat_rms(calib["objective_variables"],
                             calib["objective_weights"],
                             calib["time_mode"],
                             calib["depth_mode"],
                             args["observations"],
                             reference_year,
                             os.path.join(folder, "Results"))
    else:
        raise ValueError("Unrecognized objective function {}".format(calib["objective_function"]))
    shutil.rmtree(folder)
    log.info("Error: {}".format(error), indent=3)
    run += 1
    return error
