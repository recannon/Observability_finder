# READ ME

## Purpose:

The purpose of this code is to find when a list of solar system objects are observable from a given observatory on Earth in order to aid proposal writing.

It will create:
* A csv of the JPL Horizons call for all the objects across the semester
* A csv summary of the median value for each night
* A pdf of nightly elevation charts and summary tables for all objects visible
* A pdf with summary charts to show how the observability and target properties change over the course of the full semester 

The documentation can be found at [pyObsFind documentation](https://pyobsfind.readthedocs.io/en/latest/index.html).


## Installation

First, install the package with pip:

```bash
pip install pyobsfind
```

## How to run

This package is designed to be run from the command line.

To run the package use ``python -m obsfind.run [target_list] [start_date] [end_date] [optional args]``

For example, the most simplistic command to run the package is:

```bash
python -m obsfind.run path/to/example_targets.txt 2025-08-07 2025-08-10
```
altering the path to ``example_targets.txt`` as necessary



[![Made at Code Astro](https://img.shields.io/badge/Made%20at-Code/Astro-blueviolet.svg)](https://semaphorep.github.io/codeastro/)
[![DOI](https://zenodo.org/badge/1031821874.svg)](https://doi.org/10.5281/zenodo.16754829)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
