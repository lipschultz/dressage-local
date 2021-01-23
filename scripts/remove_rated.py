import argparse
import sqlite3
from pathlib import Path


def remove_files(cursor, table, location: Path, *, verbose=False):
    for file_reference, in cursor.execute(f'SELECT file_reference FROM {table}'):
        file = location / file_reference
        if file.exists():
            if verbose:
                print(f'Deleting {file}')
            file.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update the display directory with unrated files')
    parser.add_argument('db', type=sqlite3.connect, help='SQLite Database of ratings')
    parser.add_argument('location', type=Path, help='Directory where images are stored')
    parser.add_argument('--table', default='ratings', help='Database table storing the ratings')
    parser.add_argument('--verbose', action='store_true', help='Display verbose output')

    args = parser.parse_args()

    with args.db as cursor:
        remove_files(cursor, args.table, args.location, verbose=args.verbose)

    args.db.close()
