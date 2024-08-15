import os

def verify_args(args):
    args_properties = {
        "simulation_folder": verify_folder,
        "calibration_folder": verify_folder,
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
    try:
        os.makedirs(value, exist_ok=True)
    except:
        raise ValueError("Failed to create folder {}".format(os.path.abspath(value)))

def verify_bool(value):
    if not isinstance(value, bool):
        raise ValueError("{} is not a valid bool.".format(value))

def no_verify(value):
    x = None
