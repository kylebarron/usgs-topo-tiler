"""
Create mosaic from metadata
"""
import json
from urllib.parse import unquote, urlparse

import click
from cogeo_mosaic.mosaic import MosaicJSON
from dateutil.parser import parse as date_parse
from shapely.geometry import box, mapping


def path_accessor(feature):
    url = feature['properties']['downloadURL']
    parsed = urlparse(url)
    bucket = parsed.netloc.split('.')[0]
    key = unquote(parsed.path)
    return f's3://{bucket}{key}'


def asset_filter(tile, intersect_dataset, intersect_geoms, **kwargs):
    """Custom filter
    """
    preference = kwargs.get('filter_preference', 'latest')

    quad_coords_set = {f['geometry']['coordinates'] for f in intersect_dataset}
    result_dataset = []
    for quad_coords in quad_coords_set:
        quad_features = [
            f for f in intersect_dataset
            if f['geometry']['coordinates'] == quad_coords]

        if preference == 'latest':
            item = max(
                quad_features, key=lambda x: x['properties']['publicationDate'])
            result_dataset.append(item)
        elif preference == 'earliest':
            item = min(
                quad_features, key=lambda x: x['properties']['publicationDate'])
            result_dataset.append(item)

    return result_dataset


@click.command()
@click.option(
    '--preference',
    type=click.Choice(['latest', 'earliest'], case_sensitive=False),
    default='latest',
    help='Selection preference.')
@click.argument('file', type=click.File())
def main(preference, file):
    features = load_features(file)
    mosaic = MosaicJSON.from_features(
        features,
        minzoom=11,
        maxzoom=16,
        asset_filter=asset_filter,
        accessor=path_accessor,
        filter_preference=preference,
    )

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
