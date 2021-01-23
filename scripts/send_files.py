import argparse
import os
import shutil
from pathlib import Path
from typing import Iterable, Union

ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.jpe', '.png', '.bmp')


def get_files_in(directory, recursive=False):
    for root, dirs, files in os.walk(directory):
        root = Path(root)
        for file in files:
            yield root / file

        if not recursive:
            break


def send_files(source_directory, destination_directory, allowed_extensions: Union[bool, Iterable[str]] = True, replace_existing=False, *, verbose=False):
    for filepath in get_files_in(source_directory, True):
        if allowed_extensions is True or filepath.suffix.lower() in allowed_extensions:
            destination_filepath = destination_directory / (filepath.relative_to(source_directory))
            if not replace_existing and destination_filepath.exists():
                continue

            if verbose:
                print(f'Copying {filepath} to {destination_filepath}')
            destination_filepath.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(filepath, destination_filepath)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update the display directory with unrated files')
    parser.add_argument('source', type=Path, help='Directory root where source images are stored')
    parser.add_argument('destination', type=Path, help='Directory root where files will be transferred')
    parser.add_argument('--allowed-extensions', default='.jpg,.jpeg,.jpe,.png,.bmp', help='Comma-delimited list of extensions to transfer')
    parser.add_argument('--replace-existing', action='store_true', help='If destination already contains a file of the same name, replace it')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose output')

    args = parser.parse_args()

    allowed_extensions = [ext.lower() for ext in args.allowed_extensions.split(',')]
    send_files(args.source, args.destination, allowed_extensions=allowed_extensions, replace_existing=args.replace_existing, verbose=args.verbose)
