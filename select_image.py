import random
import sqlite3
from pathlib import Path

IMG_EXTENSIONS = ('.gif', '.png', '.jpg', '.jpeg', '.jpe', '.bmp')


def filename_to_probability(filename, ratings_map):
    rating = ratings_map.get(str(filename), 3.5)
    return 0 if rating == 1 else 2**rating


def select_random_horse(cursor, source_directory, table_name, *, file_extensions=IMG_EXTENSIONS, max_byte_size=1_000_000, only_unrated=False):
    file_extensions = [e.lower() for e in file_extensions]
    cursor = cursor.execute(f'SELECT file_reference, rating FROM {table_name}')
    ratings_map = {r['file_reference']: r['rating'] for r in cursor}

    image_directory = Path(source_directory)
    images = [f.relative_to(image_directory) for f in image_directory.rglob('*') if f.suffix.lower() in file_extensions and f.stat().st_size <= max_byte_size]
    if only_unrated:
        unrated_images = [f for f in images if str(f) not in ratings_map]
        if len(unrated_images):
            images = unrated_images
    ratings = [filename_to_probability(f, ratings_map) for f in images]
    total_rating = sum(ratings)
    ratings_distr = [r / total_rating for r in ratings]

    image = random.choices(images, weights=ratings_distr)[0]
    return image, ratings_map.get(str(image), 0)


def record_rating(cursor, file_reference, rating, table_name):
    try:
        cursor.execute(f'INSERT INTO {table_name} (file_reference, rating) '
                       'VALUES (?, ?) '
                       'ON CONFLICT(file_reference) '
                       'DO UPDATE SET rating=excluded.rating',
                       (file_reference, rating)
                       )
    except sqlite3.OperationalError as op_err:
        print(f'Encountered OperationalError while recording rating for {file_reference}: {op_err}')
        try:
            cursor.execute(f'INSERT INTO {table_name} (file_reference, rating) '
                           'VALUES (?, ?)',
                           (file_reference, rating)
                           )
            print(f'Successfully recorded rating for {file_reference} after encountering OperationalError')
        except sqlite3.IntegrityError as int_err:
            print(f'Encountered IntegrityError while recording rating for {file_reference}: {int_err}')
            cursor.execute(f'UPDATE {table_name} SET rating=? WHERE file_reference=?',
                           (rating, file_reference)
                           )
            print(f'Successfully recorded rating for {file_reference} after encountering IntegrityError')
    cursor.commit()
    return True

