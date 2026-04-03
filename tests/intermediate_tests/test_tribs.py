import subprocess
import pytest
from tribs_adapter.tribs import get_tribs_path


def test_tribs_version():
    """Test that tRIBS executable exists and returns version information."""
    # Get the path to the tRIBS executable
    tribs_executable = get_tribs_path(parallel=False)
    if not tribs_executable.exists():
        pytest.skip(f"tRIBS executable not found at {tribs_executable}")

    # Run tRIBS without arguments to get version information
    try:
        result = subprocess.run([str(tribs_executable)], capture_output=True, text=True, timeout=30)

        # tRIBS exits with code 1 when no input file is provided, but still shows version info
        # Check that version information is present in stdout or stderr
        version_output = result.stdout + result.stderr
        assert len(version_output.strip()) > 0, "No version information returned"

        # Check for specific version information
        assert 'tRIBS Version 5.3.0, Summer 2025' in version_output, "Version string not found in output"
        assert 'tRIBS Distributed Hydrologic Model' in version_output, "Program title not found in output"

        print(f"tRIBS version output: {version_output}")

    except subprocess.TimeoutExpired:
        pytest.fail("tRIBS command timed out")
    except Exception as e:
        pytest.fail(f"Failed to run tRIBS: {e}")


def test_tribspar_version():
    """Test that tRIBSpar executable exists and returns version information."""
    # Get the path to the tRIBSpar executable
    tribspar_executable = get_tribs_path(parallel=True)
    if not tribspar_executable.exists():
        pytest.skip(f"tRIBSpar executable not found at {tribspar_executable}")

    # Run tRIBSpar without arguments to get version information
    try:
        result = subprocess.run([str(tribspar_executable)], capture_output=True, text=True, timeout=30)

        # tRIBSpar exits with code 1 when no input file is provided, but still shows version info
        # Check that version information is present in stdout or stderr
        version_output = result.stdout + result.stderr
        assert len(version_output.strip()) > 0, "No version information returned"

        # Check for specific version information
        assert 'tRIBS Version 5.3.0, Summer 2025' in version_output, "Version string not found in output"
        assert 'tRIBS Distributed Hydrologic Model' in version_output, "Program title not found in output"

        print(f"tRIBSpar version output: {version_output}")

    except subprocess.TimeoutExpired:
        pytest.fail("tRIBSpar command timed out")
    except Exception as e:
        pytest.fail(f"Failed to run tRIBSpar: {e}")
