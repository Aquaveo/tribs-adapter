import os
import re
from datetime import datetime
from pathlib import Path

IN_CARD_PATTERN = "^(?![#]+)(?P<card>[A-Z0-9]+):?.*$"
IN_CARD_PROG = re.compile(IN_CARD_PATTERN)


def datetime_from_str(s: str) -> datetime | str:
    """Parse tRIBS datetime strings into datetime object."""
    if not isinstance(s, str):
        return s

    c = s.count("/")
    if c <= 1:
        return s
    elif c == 2:
        return datetime.strptime(s, "%m/%d/%Y")
    elif c == 3:
        return datetime.strptime(s, "%m/%d/%Y/%H")
    else:
        return datetime.strptime(s, "%m/%d/%Y/%H/%M")


def parse_in_file(path: Path | str) -> dict[str, str]:
    """Parse .in file into flat dictionary."""
    with open(path, 'r') as f:
        lines = f.readlines()

    d = dict()
    for i, line in enumerate(lines):
        m = IN_CARD_PROG.match(line)
        if not m:
            continue
        card = m.group('card')
        value = lines[i + 1].strip()
        if value:
            d.update({card: value})

    return d


def check_files_and_folders_for_filetype(path, filetype):
    """Check through files and folders and search for the first file with the given filetype.

    Args:
        path (str): The selected path to begin the search
        filetype (str): the extension or suffix of the filetype

    Return:
        file (str): The full path to the found file or None if not found

    """
    file = None
    for filename in os.listdir(path):
        full_filename = os.path.join(path, filename)
        if os.path.isdir(full_filename):
            result = check_files_and_folders_for_filetype(full_filename, filetype)
            if result is not None:
                return result
        elif os.path.isfile(full_filename):
            if Path(filename).suffix == filetype:
                file = full_filename
                return file
