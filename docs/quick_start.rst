Quick Start 
=================

Installation 
~~~~~~~~~~~~~
First pip install the package:

.. code-block:: bash

    pip install pyobsfind 


How to run 
~~~~~~~~~~~~~~
This package is designed to be run from the command line.
To run the package input ``obsfind.run`` followed by the inputs you want to use.

For example, the most simplistic command to run the package is:

.. code-block:: bash

    python -m obsfind.run 2025-08-07 2025-08-10

This will run the package with the default settings, using the dates 2025-08-07 and 2025-08-10 inclusive, using the target list provided: ``target_list.txt``. 
If you want to use a different target list, you need to have this stored in a txt file and pass the path to the file as an input. 

*List of inputs:*
- ``start_date``: The start date of the search period in the format YYYY-MM-DD, as in example.

- ``end_date``: The end date of the search period in the format YYYY-MM-DD, inclusive, as in example.

- ``-targ --target-file``: The path to the target list file. If not provided, the default file ``target_list.txt`` will be used. 

- ``-v --verbose``: Enable verbose output (sets log level to DEBUG).

- ``-p --plot``: Enable plotting of the results.

- ``-mpc --mpc-code``: Location for observation site: default la Silla. You can find the MPC codes here: `MPC codes <https://www.minorplanetcenter.net/iau/lists/ObsCodes.html>`_

- ``-csv --csv-output``: Name of the output csv file. Default: ``output.csv``

- ``-mag --mag-limit``: Upper limit of magnitude to be classed as visible [float]. Default: 25

- ``-elv --elevation-limit``: Minimum elevation to be observable [float]. Default: 30

- ``-air --airmass-limit``: Maximum airmass to be observable [float]. Use this only if no elevation is specified.

- ``-tvis --time-visible-limit``: Minimum time visible per night to be included in observable list [float]. Default: 1

