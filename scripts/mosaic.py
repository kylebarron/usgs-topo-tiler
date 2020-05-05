"""
Create mosaic from metadata
"""
import json
from urllib.parse import urlparse

import click
from cogeo_mosaic.mosaic import MosaicJSON
from dateutil.parser import parse as date_parse
from rtree import index
from shapely.geometry import asShape, box, mapping


def path_accessor(feature):
    url = feature['properties']['downloadURL']
    parsed = urlparse(url)
    bucket = parsed.netloc.split('.')[0]
    key = parsed.path
    return f's3://{bucket}{key}'


def asset_filter(tile, intersect_dataset, intersect_geoms, **kwargs):
    """Custom filter
    """
    preference = kwargs.get('filter_preference', 'latest')

    all_bounds = set()
    tree = index.Index()
    for idx, obj in enumerate(intersect_dataset):
        bounds = asShape(obj['geometry']).bounds
        all_bounds.add(bounds)
        tree.insert(idx, bounds)

    result_dataset = []
    for bd in all_bounds:
        items = [intersect_dataset[i] for i in tree.intersection(bd)]

        # Keep one:
        if preference == 'latest':
            item = max(items, key=lambda x: x['properties']['publicationDate'])
            result_dataset.append(item)

    return result_dataset


@click.command()
@click.argument('file', type=click.File())
def main(file):
    filter_preference = 'latest'
    features = load_features(file)
    mosaic = MosaicJSON.from_features(
        features,
        minzoom=11,
        maxzoom=16,
        asset_filter=asset_filter,
        accessor=path_accessor,
        filter_preference=filter_preference)

    print(json.dumps(mosaic.dict(), separators=(',', ':')))


def load_features(file):
    features = []
    for line in file:
        record = json.loads(line)
        # Coerce publicationDate to datetime
        record['publicationDate'] = date_parse(record['publicationDate'])

        bbox = record['boundingBox']
        geom = box(bbox['minX'], bbox['minY'], bbox['maxX'], bbox['maxY'])
        features.append({'properties': record, 'geometry': mapping(geom)})

    return features


if __name__ == '__main__':
    main()
