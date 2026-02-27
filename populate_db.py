from sqlmodel import Session
from models import engine, Bio, Stats
import csv


def load_bio():
    """Read browns_roster.csv and insert rows into the bio table."""
    with open('browns_roster.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        with Session(engine) as sess:
            for row in reader:
                # cast numeric columns where appropriate
                def maybe_int(val):
                    return int(val) if val and val.isdigit() else None

                bio = Bio(
                    first_name=row.get('first_name', '').strip(),
                    last_name=row.get('last_name', '').strip(),
                    number=maybe_int(row.get('Number', '')),
                    position=row.get('Position') or None,
                    height=row.get('Height') or None,
                    weight=maybe_int(row.get('Weight', '')),
                    age=maybe_int(row.get('Age', '')),
                    exp=maybe_int(row.get('Exp', '')),
                    college=row.get('College') or None,
                )
                sess.add(bio)
            sess.commit()
    print('bio table populated from browns_roster.csv')


def load_stats():
    """Read browns_stats_detailed.csv and insert rows into the stats table."""
    with open('browns_stats_detailed.csv', newline='', encoding='utf-8') as f:
        lines = f.readlines()

    # The header in the CSV may be split across two lines (see earlier scraping).
    # If the first line contains "first_name" but not the "SCK LOST" field,
    # and the second line begins with "K," then it is the continuation of the
    # header. Join them so DictReader sees one header row.
    if lines:
        first = lines[0]
        if 'first_name' in first and 'SCK LOST' not in first and len(lines) > 1:
            second = lines[1].lstrip()
            if second.startswith('K,') or second.startswith('K,'):
                lines[0] = first.strip() + second
                del lines[1]

    reader = csv.DictReader(lines)

    def norm_key(k: str) -> str:
        # transform header names like "COMP PER" -> "COMP_PER" and
        # "YDS/ATT" -> "YDS_ATT" so they match our attribute names.
        return k.strip().replace(' ', '_').replace('/', '_')

    with Session(engine) as sess:
        seen = set()
        for row in reader:
            # Build a normalized dict of values
            data = {norm_key(k): v for k, v in row.items() if k}
            first = data.get('first_name', '').strip()
            last = data.get('last_name', '').strip()
            if not first and not last:
                continue
            key = (first, last)
            if key in seen:
                # skip duplicate record
                continue
            seen.add(key)
            stats = Stats(first_name=first, last_name=last)
            # set the rest of the fields dynamically
            for field in (
                'ATT', 'COMP', 'YDS', 'COMP_PER', 'YDS_ATT',
                'TD', 'TD_Per', 'INT', 'INT_Per', 'LONG', 'SCK',
                'SCK_LOST', 'RATE', 'REC', 'ASSIST', 'SFTY', 'F',
            ):
                val = data.get(field)
                if val and val.strip() != '':
                    try:
                        # treat decimals as float, else int
                        cast = float(val) if '.' in val else int(val)
                    except ValueError:
                        cast = None
                    setattr(stats, field, cast)
            sess.add(stats)
        sess.commit()
    print('stats table populated from browns_stats_detailed.csv')


if __name__ == '__main__':
    load_bio()
    load_stats()
