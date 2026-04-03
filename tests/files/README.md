# Files

Use this directory to store files used in tests. These files should be used in a read-only mode. 

PLEASE DO NOT MODFIY FILES IN THIS DIRECOTRY DURING TESTS OR WRITE OUTPUT FROM TESTS TO THIS DIRECTORY!

Use a temporary directory for the system to write output from tests. PyTest provides a fixture for this: [PyTest: How to use temporary directories and files in tests](https://docs.pytest.org/en/7.1.x/how-to/tmp_path.html).

