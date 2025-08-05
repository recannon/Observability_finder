# READ ME

[![Made at Code Astro](https://img.shields.io/badge/Made%20at-Code/Astro-blueviolet.svg)](https://semaphorep.github.io/codeastro/)


## Purpose:

The purpose of this code is to find when a list of solar system objects are observable from a given observatory on Earth in order to aid proposal writing.

It will create:
* A csv of the JPL Horizons call for all the objects across the semester
* A csv summary of the median value for each night (to do)
* A pdf of nightly elevation charts and summary tables for all objects visible (to do)
* A pdf with summary charts to show how the observability and target properties change over the course of the full semester (to do)


## Dependencies:

* numpy
* matplotlib
* astropy
* pandas
* astroquery
* rich
* pylatex
* ephem
