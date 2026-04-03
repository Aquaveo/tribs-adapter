# tRIBS Adapter

Adapts tRIBS hydrolgic modeling data and workflows for Python applications.

## Dev Installation

1. Install ATCore:
    
    ```bash
    git clone https://github.com/Aquaveo/tethysext-atcore.git
    cd tethysext-atcore
    tethys install -d
    ```

2. Install the [PDM dependency manager](https://pdm.fming.dev/latest/):

```bash
pip install pdm
```

3. Change into the `tribs-adapter` and run `pdm install`:

If installing into an environment that has gdal already installed (e.g., conda environment with gdal from conda-forge):

```bash
pdm install
```

Otherwise, you can include the optional gdal dependency when installing pdm:

```bash
pdm install -G gdal
```

> **Note**
> `pdm install` installs the package as an editable package and installs dependencies AND dev dependencies but NOT optional dependencies.

4. Set GEOSERVER_CLUSTER_PORTS environment variable.

If using a GeoServer setup different than the tethysplatform/geoserver Docker image, or using the tethysplatform/geoserver with less than 4 nodes, need to set GEOSERVER_CLUSTER_PORTS the port(s) of your GEOSERVER setup:

```bash
# Default ports
export GEOSERVER_CLUSTER_PORTS="[8081,8082,8083,8084]"

# Note: No trailing commas
export GEOSERVER_CLUSTER_PORTS="[8080]"
```

5. Set the FDB_ROOT_DIR environment variable(s).

Set the FDB_ROOT_DIR environment variable to the root directory where you want the file databases for projects to be stored. Ensure the app has read and write permissions to this directory.

```bash
export FDB_ROOT_DIR="/path/to/fdb_root_dir"
```

If you need to specify a different path for the condor worker, set the CONDOR_FDB_ROOT_DIR environment variable. This is usually only necessary for production deployment where condor and the app are running in separate environments.

```bash
export CONDOR_FDB_ROOT_DIR="/path/to/condor_fdb_root_dir"
```

### Install only dev dependencies

* Install only test dependencies

```bash
pdm install -G test
```
* Install only lint dependencies
```bash
pdm install -G lint
```

* Install all dev dependencies (test & lint)

```bash
pdm install -G:all
```

### Managing dependencies

* Add a new dependency:

```bash
pdm add <package-name>
```

* Add a new dev dependency:

```bash
pdm add -dG test <package-name>
pdm add -dG lint <package-name>
```

* Add a new optional dependeny:

```bash
pdm add -G <group-name> <package-name>
```

> **Important**
> DO NOT REMOVE DEPENDENCIES USING `pdm remove` WHEN IN A CONDA ENVIRONMENT. IT WILL ATTEMPT TO REMOVE ALL PACKAGES NOT LISTED AS DEPENDENCIES.

3. Download the pyproj transformation grids:

See: https://pyproj4.github.io/pyproj/stable/transformation_grids.html

```bash
export PROJ_DOWNLOAD_DIR=$(python -c "import pyproj; print(pyproj.datadir.get_data_dir())")
wget --mirror https://cdn.proj.org/ -P ${PROJ_DOWNLOAD_DIR}
```

## PDM Scripts

The project is configured with several PDM convenience scripts:

```bash
# Run linter
pdm run lint

# Run formatter
pdm run format

# Run tests
pdm run test

# Run all checks
pdm run all
```

## Formatting and Linting Manually

This package is configured to use yapf code formatting

1. Install lint dependencies:

```bash
pdm install -G lint
```

2. Run code formatting from the project directory:

```bash
yapf --in-place --recursive --verbose .

# Short version
yapf -ir -vv .
```

3. Run linter from the project directory:

```bash
flake8 .
```

> **NOTE**
> The configuration for yapf and flake8 is in the `pyproject.toml`.

## Testing Manually

This package is configured to use pytest for testing

1. Install test dependencies:

```bash
pdm install -G test
```

2. Run tests from the project directory:

```bash
pytest
```

> **NOTE**
> The configuration for pytest and coverage is in the `pyproject.toml`.
