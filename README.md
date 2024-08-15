# Lake Calibrator

[![License: MIT][mit-by-shield]][mit-by] ![Python][python-by-shield]

Lake calibrator is a tool designed for automating the calibration of hydrodynamic lake models. The goal is to provide a consistent interface for a range of models and calibration frameworks.

#### Supported simulations

| Simulations          | Calibration Frameworks                             |
|----------------------|----------------------------------------------------|
| [Simstrat][simstrat] | [scipy.optimize.minimize][scipy] <br> [PEST][pest] |

## Installation
Clone the repository and install it manually:
```commandline
git clone git@github.com:eawag-surface-waters-research/lake-calibrator.git
cd lake-calibrator
pip install requirements.txt
```

## Usage

### Command line

```commandline
python src/main.py <path>
```
Where **path** is the path of the input arguments file.

### Script

```python
from main import calibrate

arguments = {...}

results = calibrate(arguments)
```
### Arguments

Example argument dictionary's can be seen in the `args` folder.

| Argument              | Description                                                                                        | Example                                                                                                                                                                      |
|-----------------------|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| simulation_folder     | Path to simulation folder that contains the input files for running the simulation                 | ```/path/lake_name ```                                                                                                                                                       |
| calibration_folder    | Path to location for calibration file generation                                                   | ```runs/lake_name```                                                                                                                                                         |
| observations          | List of dictionaries describing observation files (see below for more info on files)               | ```[{"file": "observations/lake_name/temperature.csv","parameter": "temperature","unit": "degC","start": "1982-01-01T01:00:00+00:00","end": "2022-01-01T01:00:00+00:00"}]``` |
| simulation            | Simulation software name                                                                           | ```simstrat```                                                                                                                                                               |
| execute               | Simulation execution command where {calibration_folder} will be replaced by the calibration folder | ```docker run --rm --user $(id -u):$(id -g) -v {calibration_folder}:/simstrat/run eawag/simstrat:3.0.4 Settings.par```                                                       |
| parameters            | List of dictionaries describing parameters to optimize                                             | ```[{"name": "a_seiche", "initial":  2.0e-5, "min": 1e-5, "max": 0.5}, {"name": "p_absorb", "initial":  1.49916053, "min": 0.5, "max": 1.5}]```                              |
| calibration_framework | Calibration framework name                                                                         | ```scipy```                                                                                                                                                                  |
| calibration_options   | Parameters for the calibration                                                                     | See example argument files                                                                                                                                                   |

### Observations

Observation files should be csv files with the following structure:

| time                      | depth | latitude | longitude | value | weight |
|---------------------------|-------|----------|-----------|-------|--------|
| 2024-08-12T22:27:54+00:00 | 1.6   | 46.5     | 6.67      | 18.3  | 1      |
| 2024-08-12T23:27:54+00:00 | 8.4   | 46.5     | 6.67      | 8.5   | 1      |

- Time values should be ISO 8601 with timezone information.
- The values should all have the same units. 
- There should be one file per lake and per parameter, e.g. lake_name/temperature.csv, lake_name/secchi.csv




## License
This package is licensed under the MIT License.

## Acknowledgments
This package is based on existing projects for calibrating 1D lake models from the Applied System Analysis group at Eawag.


[mit-by]: https://opensource.org/licenses/MIT
[mit-by-shield]: https://img.shields.io/badge/License-MIT-g.svg
[python-by-shield]: https://img.shields.io/badge/Python-3.9-g
[simstrat]: https://github.com/Eawag-AppliedSystemAnalysis/Simstrat
[scipy]: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
[pest]: https://pesthomepage.org/