# Observations

Observation files should be csv files with the following structure:

| time                      | depth | latitude | longitude | value | weight |
|---------------------------|-------|----------|-----------|-------|--------|
| 2024-08-12T22:27:54+00:00 | 1.6   | 46.5     | 6.67      | 18.3  | 1      |
| 2024-08-12T23:27:54+00:00 | 8.4   | 46.5     | 6.67      | 8.5   | 1      |

There should be one file per lake and per parameter

e.g. lake_name/temperature.csv, lake_name/secchi.csv, lake_name/ice.csv

The values should all have the same units. 