import os
import traceback
import subprocess
import pandas as pd
from datetime import datetime, timezone


def run_subprocess(command, debug=False):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output and debug:
            print(output.strip())
    stderr = process.communicate()[1]
    if stderr and debug:
        print(stderr.strip())
    if process.returncode != 0:
        error_message = f"Command failed with return code {process.returncode}\n"
        error_message += f"Command: {command}\n"
        error_message += f"Standard Error: {stderr}\n"
        raise RuntimeError(error_message)

def parse_observation_file(file, start, end):
    df = pd.read_csv(file)
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    df = df.sort_index()
    df = df.loc[start:end]
    return df


def days_since_year(date, year):
    reference_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    delta = date - reference_date
    return delta.total_seconds() / 86400.0

class Logger(object):
    def __init__(self, path=False, time=True):
        if path != False:
            if os.path.exists(os.path.dirname(path)):
                if time:
                    self.path = "{}/{}.log".format(path.split(".")[0], datetime.now().strftime("%Y%m%d_%H%M%S"))
                else:
                    self.path = "{}/log.log".format(path.split(".")[0])
            else:
                print("\033[93mUnable to find log folder: {}. Logs will be printed but not saved.\033[0m".format(
                    os.path.dirname(path)))
                self.path = False
        else:
            self.path = False
        self.stage = 1

    def info(self, string, indent=0, time=True):
        if time:
            out = datetime.now().strftime("%H:%M:%S") + (" " * 3 * (indent + 1)) + string
        else:
            out = (" " * 3 * (indent)) + string
        print(out)
        if self.path:
            with open(self.path, "a") as file:
                file.write(out + "\n")

    def initialise(self, string):
        out = "****** " + string + " " + datetime.now().strftime("%H:%M:%S %d.%m.%Y") + " ******"
        print('\033[1m' + out + '\033[0m')
        if self.path:
            with open(self.path, "a") as file:
                file.write(out + "\n")

    def inputs(self, title, args):
        self.info("______ {} ______".format(title), time=False)
        for key in args.keys():
            if "password" not in key:
                self.info("{}: {}".format(key, args[key]), time=False)
            else:
                self.info("{}: {}".format(key, "*************"), time=False)
        self.info("_______{}_______".format("_" * len(title)), time=False)

    def begin_stage(self, string):
        self.newline()
        out = datetime.now().strftime("%H:%M:%S") + "   Stage {}: ".format(self.stage) + string
        self.stage = self.stage + 1
        print(out)
        if self.path:
            with open(self.path, "a") as file:
                file.write(out + "\n")
        return self.stage - 1

    def end_stage(self):
        out = datetime.now().strftime("%H:%M:%S") + "   Stage {}: Completed.".format(self.stage - 1)
        print(out)
        if self.path:
            with open(self.path, "a") as file:
                file.write(out + "\n")

    def warning(self, string, indent=0):
        out = datetime.now().strftime("%H:%M:%S") + (" " * 3 * (indent + 1)) + "WARNING: " + string
        print('\033[93m' + out + '\033[0m')
        if self.path:
            with open(self.path, "a") as file:
                file.write(out + "\n")

    def error(self):
        out = datetime.now().strftime("%H:%M:%S") + "   ERROR: Script failed on stage {}".format(self.stage - 1)
        print('\033[91m' + out + '\033[0m')
        if self.path:
            with open(self.path, "a") as file:
                file.write(out + "\n")
                file.write("\n")
                traceback.print_exc(file=file)

    def end(self, string):
        out = "****** " + string + " ******"
        print('\033[92m' + out + '\033[0m')
        if self.path:
            with open(self.path, "a") as file:
                file.write(out + "\n")

    def subprocess(self, process, error=""):
        failed = False
        while True:
            output = process.stdout.readline()
            out = output.strip()
            print(out)
            if error != "" and error in out:
                failed = True
            if self.path:
                with open(self.path, "a") as file:
                    file.write(out + "\n")
            return_code = process.poll()
            if return_code is not None:
                for output in process.stdout.readlines():
                    out = output.strip()
                    print(out)
                    if self.path:
                        with open(self.path, "a") as file:
                            file.write(out + "\n")
                break
        return failed

    def newline(self):
        print("")
        if self.path:
            with open(self.path, "a") as file:
                file.write("\n")


def verify_args(args):
    args_properties = {
        "simulation_folder": verify_folder,
        "calibration_folder": no_verify,
        "observations": no_verify,
        "simulation": no_verify,
        "execute": no_verify,
        "parameters": no_verify,
        "calibration_framework": no_verify,
        "calibration_options": no_verify
    }
    for arg in args_properties.keys():
        if arg not in args:
            raise ValueError("Argument {} required in arguments file.")
        try:
            args_properties[arg](args[arg])
        except Exception as e:
            raise ValueError("Invalid argument for {}, {}".format(arg, e))

def verify_file(value):
    if os.path.isfile(value):
        return os.path.abspath(value)
    else:
        raise ValueError("Argument file not found at {}".format(os.path.abspath(value)))

def verify_folder(value):
    if not (os.path.exists(value) and os.path.isdir(value)):
        raise ValueError("Folder doesnt exist".format(os.path.abspath(value)))

def verify_bool(value):
    if not isinstance(value, bool):
        raise ValueError("{} is not a valid bool.".format(value))

def no_verify(value):
    x = None