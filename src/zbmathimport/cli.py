import argparse
from argparse import RawTextHelpFormatter
import sys
import os
import itertools

from zbmathimport.zbmathparse import  import_zblatt
from datetime import date
import requests
import json
import yaml


def populate_ids(dirname):
    authors = dict()
    for author in os.listdir(dirname):
        file = "content/authors/"+author+"/_index.md"
        with open(file, 'r') as fd:
            lines = itertools.takewhile(lambda x: x != "---\n", fd.readlines()[2:-1])
            file = yaml.safe_load('\n'.join(lines))
            if 'zbmath_id' in file:
                for id in file['zbmath_id']:
                    authors[id] = author
    return authors



def main():
    parser = argparse.ArgumentParser(
                        prog='zbMathImport',
                        description='Import recent publications for a list of authors and store them in markdown files.')

    parser.add_argument('progname')
    parser.add_argument('-a', '--authors', default="content/authors", help="Folder containing the list of authors")      # option that takes a value
    parser.add_argument('-o', '--output', default="content/publication/", help="Output path (e.g. `content/publication/`)")      # option that takes a value
    parser.add_argument('--compact', action=argparse.BooleanOptionalAction, help="write compact markdown files")      # option that takes a value
    parser.add_argument('--dry_run', action=argparse.BooleanOptionalAction, help="Test the command, but do not actually produce the files.")      # option that takes a value
    parser.add_argument('--overwrite', action=argparse.BooleanOptionalAction, help="overwrite existing files")      # option that takes a value

    values, unknown = parser.parse_known_args(sys.argv)
    arguments = vars(values)
    zbmath_ids = populate_ids(arguments['authors'])
    pub_dir = arguments['output']
    compact = arguments['compact']
    overwrite = arguments['overwrite']
    dry_run = arguments['dry_run']

    today = date.today()
    year = str(today.year)
    # If in January, include last year
    if today.month < 2:
        year = str(today.year - 1) + "-" + year

    authorquery = 'ia:'+' | ia:'.join(zbmath_ids.keys())
    datequery = f'py:{year}'
    query = f'({authorquery}) %26 {datequery}'

    url = f"https://api.zbmath.org/v1/document/_search?search_string={query}"
    r = requests.get(url)
    if r.status_code == 200:
        root = json.loads(r.text)
        import_zblatt(root["result"], author_ids=zbmath_ids, pub_dir=pub_dir, compact=compact, overwrite=overwrite, dry_run=dry_run)
    else:
        print("Requested authors:", zbmath_ids)
        print("used url:", url)
        print(r)

