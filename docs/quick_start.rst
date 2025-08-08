Quick Start 
=================

Installation 
~~~~~~~~~~~~~
First pip install the package:

.. code-block:: bash

    pip install pyobsfind=0.4.0


How to run 
~~~~~~~~~~~~~~
This package is designed to be run from the command line.
To run the package input ``obsfind.run`` followed by the inputs you want to use.

For example, the most simplistic command to run the package is:

.. code-block:: bash

    python -m obsfind.run path/to/example_targets.txt 2025-08-07 2025-08-10

Alter the file path to the location of the ``example_targets.txt`` file.

An example target list file is available here: 
:download:`example_targets.txt <_static/example_targets.txt>`

This will run the package with the default settings, checking the visibility of targets in the input file using the dates 2025-08-07 and 2025-08-10 inclusive. 

**Warning:** to run this package you need internet access.


**List of inputs:**

- ``target_file``: The path to the target list file. Targets can be provisional or formal MPC designations on a line each.

- ``start_date``: The start date of the search period in the format YYYY-MM-DD, as in example. It is advised to use dats within 10 years to the present date.

- ``end_date``: The end date of the search period in the format YYYY-MM-DD, inclusive, as in example.

- ``-v --verbose``: Enable verbose output (sets log level to DEBUG).

- ``-p --plot``: Enable plotting of the results.

- ``-mpc --mpc-code``: Location for observation site: default la Silla. You can find the MPC codes here: `MPC codes <https://www.minorplanetcenter.net/iau/lists/ObsCodes.html>`_

- ``-csv --csv-output``: Name of the output csv file. Default: ``output.csv``

- ``-mag --mag-limit``: Upper limit of magnitude to be classed as visible [float]. Default: 25

- ``-elv --elevation-limit``: Minimum elevation to be observable [float]. Default: 30

- ``-air --airmass-limit``: Maximum airmass to be observable [float]. Use this only if no elevation is specified.

- ``-tvis --time-visible-limit``: Minimum time visible per night to be included in observable list [float]. Default: 1

