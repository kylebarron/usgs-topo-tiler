"""
Create mosaic from metadata
"""
import json
from urllib.parse import unquote, urlparse

import click
import requests
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
    preference = kwargs.get('preference', 'latest')
    check_exists = kwargs.get('check_exists', False)

    quad_coords_set = {f['geometry']['coordinates'] for f in intersect_dataset}
    result_dataset = []
    for quad_coords in quad_coords_set:
        quad_features = [
            f for f in intersect_dataset
            if f['geometry']['coordinates'] == quad_coords]

        if preference == 'latest':
            quad_features = sorted(
                quad_features,
                key=lambda x: x['properties']['publicationDate'],
                reverse=True)
        elif preference == 'earliest':
            quad_features = sorted(
                quad_features, key=lambda x: x['properties']['publicationDate'])
        else:
            raise ValueError(f'Invalid preference: {preference}')

        # Check that file actually exists
        if check_exists:
            for item in quad_features:
                url = item['properties']['downloadURL']
                r = requests.head(url)
                if r.status_code == 200:
                    break
        else:
            item = quad_features[0]

        result_dataset.append(item)

    return result_dataset


@click.command()
@click.option(
    '--preference',
    type=click.Choice(['latest', 'earliest'], case_sensitive=False),
    default='latest',
    show_default=True,
    help='Selection preference.')
@click.option(
    '--check-exists/--no-check-exists',
    default=False,
    show_default=True,
    help='Perform HEAD request on every selected image to ensure it exists')
@click.argument('file', type=click.File())
def mosaic(preference, check_exists, file):
    features = load_features(file)
    mosaic = MosaicJSON.from_features(
        features,
        minzoom=11,
        maxzoom=16,
        asset_filter=asset_filter,
        accessor=path_accessor,
        check_exists=check_exists,
        preference=preference)

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
    mosaic()
