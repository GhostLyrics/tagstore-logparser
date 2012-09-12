How to:  
The script assumes that `store.tgs` files have a number in their filename 
(e.g. `store47.tgs`. It will immediately abort if this is not the case.

Linux/Mac:  
We assume that the parser is not in your `$PATH`.

* `chmod + x SCRIPTNAME`
* `./SCRIPTNAME FILE_TO_PARSE` 
    Parsing multiple files in batch is possible and recommended.  
    (e.g. `./SCRIPTNAME FILE_TO_PARSE_1 FILE_TO_PARSE_2` etc.)

Windows:  
Use CMD or preferably PowerShell.

* `python SCRIPTNAME FILE_TO_PARSE`
    Parsing multiple files in batch is possible and recommended.  
    (e.g. `./SCRIPTNAME FILE_TO_PARSE_1 FILE_TO_PARSE_2` etc.)

---
Additional hints:
To easily parse the whole current directory use `*` as a wildcard:

* `./SCRIPTNAME *`

The `.tgs` files don't have to be in the current directory. Absolute paths may
be used. Stores must still provide numbers in their filenames in order to be
processed.

* `./SCRIPTNAME ~/tests/run_01/store02.tgs ~/tests/run_02/store45.tgs`
* `./SCRIPTNAME ~/tests/run_01/*`
