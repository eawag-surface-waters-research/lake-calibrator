import os
import shutil
from .general import run_subprocess

def pest_calibrate(args, log):
    log.info("Calibrating {} with PEST".format(args["simulation"]))

    # Create PEST input files
        # .sh file for running
    """
    #!/bin/bash
    dir="$(dirname "$(realpath "$0")")"
    folder=$(basename "$(dirname "$(realpath "$0")")")
    cp "/pest/calibrate/inputs"/* "$dir"/
    docker run -v "/home/runnalja/git/Simstrat/Simstrat-Operational/calibration/LakeAegeri/$folder:/simstrat/run" eawag/simstrat:3.0.3 simstrat_PEST.par
    """
    # Run PEST
    # docker run -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd):/pest/calibrate --rm eawag/pest_hp:18.0.0 -f simstrat_calib -a 2 -p 4005

    # Collect results from PEST


    return {
        "parameters": {"a_seiche": 1, "f_wind": 2},
        "error": 2
    }