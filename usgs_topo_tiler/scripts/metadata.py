import json
import math
import sys

import click
import requests


@click.command()
@click.option(
    '-b',
    '--bbox',
    default=None,
    show_default=True,
    type=str,
    help='Bounding box. Must be provided in a string as "minx,miny,maxx,maxy"')
def metadata(bbox):
    """Download Topo metadata
    """
    url = 'http://viewer.nationalmap.gov/tnmaccess/api/products'
    params = {
        'datasets': 'Historical Topographic Maps',
        'prodFormats': 'GeoTIFF',
        'prodExtents': '7.5 x 7.5 minute',
        'max': 1}

    if bbox:
        params['bbox'] = bbox

    # Initial request to get total number of results
    r = requests.get(url, params=params)
    total = r.json()['total']

    params['max'] = 1000
    n_requests = math.ceil(total / 1000)
    for i in range(n_requests):
        print(f'{i + 1}/{n_requests}', file=sys.stderr)

        params['offset'] = i * 1000

        r = requests.get(url, params=params)

        # Print to stdout
        for item in r.json()['items']:
            print(json.dumps(item, separators=(',', ':')))


if __name__ == '__main__':
    metadata()
