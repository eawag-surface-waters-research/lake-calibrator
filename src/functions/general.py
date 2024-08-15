import subprocess

def run_subprocess(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        error_message = f"Command failed with return code {result.returncode}\n"
        error_message += f"Command: {command}\n"
        error_message += f"Standard Output: {result.stdout}\n"
        error_message += f"Standard Error: {result.stderr}\n"
        raise RuntimeError(error_message)