# -*- coding: utf-8 -*-
import os
import json
import argparse
from functions.log import Logger
from functions.verify import verify_args, verify_file
from functions.scipy import scipy_calibrate
from functions.pest import pest_calibrate


def calibrate(arguments):
    verify_args(arguments)
    if "log" in arguments and arguments["log"]:
        log = Logger(path=arguments["calibration_folder"])
    else:
        log = Logger()
    log.initialise("Lake Calibrator")
    log.inputs("Arguments", arguments)
    if arguments["calibration_framework"] == "scipy":
        results = scipy_calibrate(arguments, log)
    elif arguments["calibration_framework"] == "PEST":
        results = pest_calibrate(arguments, log)
    else:
        raise ValueError("Unrecognised calibration framework: {}".format(arguments["calibration_framework"]))
    log.inputs("Outputs", results)
    return results



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lake calibrator')
    parser.add_argument('arg_file', type=verify_file, help='Path to arguments file')
    args = parser.parse_args()
    arg_file = args.arg_file
    try:
        with open(arg_file) as f:
            args = json.load(f)
    except:
        raise ValueError("Failed to parse {}. Verify it is a valid json file.".format(arg_file))
    calibrate(args)

