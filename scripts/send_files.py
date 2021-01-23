import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, Union

ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.jpe', '.png', '.bmp')


def copy(from_location, to_location, make_parents=False):
    if make_parents:
        to_location.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(from_location, to_location)


def get_files_in(directory, recursive=False):
    for root, dirs, files in os.walk(directory):
        root = Path(root)
        for file in files:
            yield root / file

        if not recursive:
            break


def resize(filepath, max_size):
    MAX_DISPLAY_WIDTH, MAX_DISPLAY_HEIGHT = 800, 480

    width, height = [int(v) for v in subprocess.run(['identify', '-format', '%wx%h', str(filepath)], stdout=subprocess.PIPE, check=True).stdout.decode('utf-8').split('x')]

    width_factor = MAX_DISPLAY_WIDTH / width
    height_factor = MAX_DISPLAY_HEIGHT / height
    factor = min(width_factor, height_factor)

    resized_filepath = filepath.parent / (filepath.stem + '-resized' + filepath.suffix)
    try:
        subprocess.run(['convert', str(filepath), '-resize', f'{int(factor * 100)}%', str(resized_filepath)], check=True)
        if resized_filepath.stat().st_size <= max_size:
            copy(resized_filepath, filepath)
            return
    except subprocess.CalledProcessError:
        pass

    file_size = resized_filepath.stat().st_size
    low_quality_filepath = filepath.parent / (filepath.stem + '-quality' + filepath.suffix)
    quality = 95
    while file_size > max_size and quality > 0:
        try:
            subprocess.run(['convert', str(resized_filepath), '-quality', f'{quality}', str(low_quality_filepath)], check=True)
            file_size = low_quality_filepath.stat().st_size
            if file_size <= max_size:
                copy(low_quality_filepath, filepath)
                return
        except subprocess.CalledProcessError:
            pass
        quality -= 5


def send_files(source_directory, destination_directory, allowed_extensions: Union[bool, Iterable[str]] = True, replace_existing=False, resize_over=False, *, verbose=False):
    with tempfile.TemporaryDirectory() as tmp_dir:
        for filepath in get_files_in(source_directory, True):
            if allowed_extensions is True or filepath.suffix.lower() in allowed_extensions:
                destination_filepath = destination_directory / (filepath.relative_to(source_directory))
                if not replace_existing and destination_filepath.exists():
                    continue

                if verbose:
                    print(f'Copying {filepath} to {destination_filepath}')

                if resize_over and filepath.stat().st_size > resize_over:
                    if verbose:
                        print(f'Resizing {filepath} from {filepath.stat().st_size}')
                    copied_location = Path(tmp_dir) / filepath.name
                    copy(filepath, copied_location)
                    resize(copied_location, resize_over)
                    filepath = copied_location

                copy(filepath, destination_filepath, True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update the display directory with unrated files')
    parser.add_argument('source', type=Path, help='Directory root where source images are stored')
    parser.add_argument('destination', type=Path, help='Directory root where files will be transferred')
    parser.add_argument('--allowed-extensions', default='.jpg,.jpeg,.jpe,.png,.bmp', help='Comma-delimited list of extensions to transfer')
    parser.add_argument('--replace-existing', action='store_true', help='If destination already contains a file of the same name, replace it')
    parser.add_argument('--resize-over', help='Number of bytes over which files will be resized before transferring (original will be unmodified)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose output')

    args = parser.parse_args()

    allowed_extensions = [ext.lower() for ext in args.allowed_extensions.split(',')]
    resize_over = int(args.resize_over) if args.resize_over is not None else None
    send_files(args.source, args.destination, allowed_extensions=allowed_extensions, replace_existing=args.replace_existing, resize_over=resize_over, verbose=args.verbose)
