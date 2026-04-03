# tRIBS Data Model
This directory contains a simplified representation of how the model files would be stored in the ATCore `Resources` and `FileCollections`. The first level UUID folder represents a `Resource` while the second level UUID folders represent the `FileCollection` associated with that `Resource`. The `salas.json` file at the root of the directory is the JSON version of the salas.in model input file.

NOTES:
* In the full implementation the `Resources` will not be folders, but ATCore `Resource` database objects with metadata in the `__resource__.json` stored as attributes on the `Resource` object. 
* The `FileCollection` folders would be stored in the `FileDatabase` for the Project `Resource`.