## Dependencies
* [numpy][]
* [scipy][]
* [matplotlib][]

## Usage
The script assumes that `store.tgs` files have a number in their filename 
(e.g. `store47.tgs`. It will immediately abort if this is not the case.

### Linux/Mac
We assume that the parser is not in your `$PATH`.

* `chmod + x analyze_artifacts_tagstore.py`
* `./analyze_artifacts_tagstore.py FILE` 
    Parsing multiple files in batch is possible and recommended.  
    (e.g. `./analyze_artifacts_tagstore.py FILE_1 FILE_2` etc.)

### Windows
Use CMD or preferably PowerShell. This assumes that the Python installation is
in your `$PATH`.

* `python analyze_artifacts_tagstore.py FILE`
    Parsing multiple files in batch is possible and recommended.  
    (e.g. `./analyze_artifacts_tagstore.py FILE_1 FILE_2` etc.)

#### Selecting multiple files
To easily parse the whole current directory use `*` as a wildcard:

* `./analyze_artifacts_tagstore.py *`

To use only files in the current directory that have a specific file extension
(e.g. `.tgs`) use the wildcard in that context:

* `./analyze_artifacts_tagstore.py *.tgs`

The `.tgs` files don't have to be in the current directory. Absolute paths may
be used. Stores must still provide numbers in their filenames in order to be
processed.

* `./analyze_artifacts_tagstore.py ~/tests/run_01/store02.tgs ~/tests/run_02/store45.tgs`
* `./analyze_artifacts_tagstore.py ~/tests/run_01/*`

#### Additional parameters

This script takes two additional parameters signaling which logging output to
display. You may choose `-v` for verbose mode or `-q` for quiet mode.

* `./analyze_artifacts_tagstore.py -v FILE`

<!-- data -->

[numpy]: http://sourceforge.net/projects/numpy/files/
[scipy]: http://sourceforge.net/projects/scipy/files/
[matplotlib]: http://matplotlib.org
