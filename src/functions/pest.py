import os
import shutil
from .general import run_subprocess

def pest_calibrate(args, log):
    log.info("Calibrating {} with PEST".format(args["simulation"]))

    return {
        "parameters": {"a_seiche": 1, "f_wind": 2},
        "error": 2
    }