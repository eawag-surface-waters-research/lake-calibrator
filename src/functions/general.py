import subprocess
import pandas as pd
from datetime import datetime, timezone

def run_subprocess(command, debug=False):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if debug:
        print(result.stdout)
        print(result.stderr)
    if result.returncode != 0:
        error_message = f"Command failed with return code {result.returncode}\n"
        error_message += f"Command: {command}\n"
        error_message += f"Standard Output: {result.stdout}\n"
        error_message += f"Standard Error: {result.stderr}\n"
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