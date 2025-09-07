import argparse
from argparse import RawTextHelpFormatter
import sys

from zbmathimport.zbmathparse import  import_zblatt
from datetime import date
import requests
import json
import yaml

def populate_ids(fname):
    with open(fname,'r') as fp:
        authors = yaml.safe_load(fp)

    return authors['authors']



def main():
    parser = argparse.ArgumentParser(
                        prog='zbMathImport',
                        description='Import recent publications for a list of authors and store them in markdown files.')

    parser.add_argument('progname')
    parser.add_argument('-c', '--config', default="authors.yaml", help="Configuration file containing the list of authors to query")      # option that takes a value
    parser.add_argument('-o', '--output', default="content/publication/", help="Output path (e.g. `content/publication/`)")      # option that takes a value

    values, unknown = parser.parse_known_args(sys.argv)
    arguments = vars(values)
    zbmath_ids = populate_ids(arguments['config'])
    pub_dir = arguments['output']

    today = date.today()
    year = str(today.year)
    # If in January, include last year
    if today.month < 2:
        year = str(today.year - 1) + "-" + year

    authorquery = 'ia:'+' | ia:'.join(zbmath_ids)
    datequery = f'py:{year}'
    query = f'({authorquery}) %26 {datequery}'
    #url = f"https://api.zbmath.org/v1/document/_search"
    #r = requests.get(url, data={'search_string': query})


    url = f"https://api.zbmath.org/v1/document/_search?search_string={query}"
    r = requests.get(url)
    if r.status_code == 200:
        root = json.loads(r.text)
        import_zblatt(root["result"], pub_dir=pub_dir)
    else:
        print(r)

