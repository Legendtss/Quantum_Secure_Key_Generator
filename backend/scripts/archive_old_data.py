"""Archive oversized training and AB test CSV datasets.
Keeps only the latest rows for operational footprint control.
"""

import os
import shutil
from datetime import datetime

import pandas as pd


DATA_DIR = os.path.join('backend', 'data')
ARCHIVE_DIR = os.path.join('backend', 'data', 'archive')

FILES = [
    ('training_data.csv', 10000),
    ('ab_test_log.csv', 20000),
]


def archive_file(filename, keep_rows):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {'file': filename, 'status': 'missing'}

    df = pd.read_csv(path)
    row_count = len(df)
    if row_count <= keep_rows:
        return {'file': filename, 'status': 'unchanged', 'rows': row_count}

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    stamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    archive_path = os.path.join(ARCHIVE_DIR, f"{filename}.{stamp}.bak")
    shutil.copy(path, archive_path)

    df.tail(keep_rows).to_csv(path, index=False, encoding='utf-8-sig')
    return {
        'file': filename,
        'status': 'archived',
        'original_rows': row_count,
        'kept_rows': keep_rows,
        'archive_path': archive_path,
    }


def main():
    results = [archive_file(name, keep) for name, keep in FILES]
    for r in results:
        print(r)


if __name__ == '__main__':
    main()
