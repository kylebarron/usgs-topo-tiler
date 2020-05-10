import json
from urllib.parse import unquote

import click
import geopandas as gpd
import mercantile
import pandas as pd
from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.utils import _intersect_percent
from pygeos import polygons
from rio_tiler.mercator import zoom_for_pixelsize
from shapely.geometry import asShape, box




@click.command()
@click.option(
    '--meta-path',
    type=click.Path(exists=True, readable=True),
    required=True,
    help='Path to csv file of USGS bulk metadata dump from S3')
@click.option(
    '--s3-list-path',
    type=click.Path(exists=True, readable=True),
    required=False,
    default=None,
    show_default=True,
    help='Path to txt file of list of s3 GeoTIFF files')
@click.option(
    '--min-scale',
    type=float,
    required=False,
    default=None,
    show_default=True,
    help='Minimum map scale, inclusive')
@click.option(
    '--max-scale',
    type=float,
    required=False,
    default=None,
    show_default=True,
    help='Maximum map scale, inclusive')
@click.option(
    '--min-year',
    type=float,
    required=False,
    default=None,
    show_default=True,
    help='Minimum map year, inclusive')
@click.option(
    '--max-year',
    type=float,
    required=False,
    default=None,
    show_default=True,
    help='Maximum map year, inclusive')
@click.option(
    '--woodland-tint/--no-woodland-tint',
    is_flag=True,
    default=None,
    required=False,
    help=
    'Filter on woodland tint or no woodland tint. By default no filtering is applied.'
)
@click.option(
    '--allow-orthophoto',
    is_flag=True,
    help='Allow orthophoto',
    default=False,
    show_default=True,
)
@click.option(
    '--bbox',
    type=str,
    default=None,
    show_default=True,
    help='Bounding box for mosaic. Must be of format "minx,miny,maxx,maxy"')
def main(
        meta_path, s3_list_path, min_scale, max_scale, min_year, max_year,
        woodland_tint, allow_orthophoto, bbox):
    df = pd.read_csv(meta_path, low_memory=False)
    # Rename column names to lower case and snake case
    df = df.rename(columns=lambda col: col.lower().replace(' ', '_'))

    # Keep only historical maps
    # Newer maps are only in GeoPDF, and not in GeoTIFF, let alone COG
    df = df[df['series'] == 'HTMC']

    # Create year column as Imprint Year if it exists, otherwise Date On Map
    df['year'] = df['imprint_year'].fillna(df['date_on_map'])

    # Apply filters
    if min_scale:
        df = df[df['scale'] >= min_scale]
    if max_scale:
        df = df[df['scale'] <= max_scale]
    if min_year:
        df = df[df['year'] >= min_year]
    if max_year:
        df = df[df['year'] <= max_year]
    if woodland_tint is not None:
        if woodland_tint:
            df = df[df['woodland_tint'] == 'Y']
        else:
            df = df[df['woodland_tint'] == 'N']
    if not allow_orthophoto:
        df = df[df['orthophoto'].isna()]

    # Create s3 GeoTIFF paths from metadata
    df['s3_tif'] = construct_s3_tif_url(df['download_product_s3'])

    if s3_list_path:
        # Load list of GeoTIFF files
        s3_files_df = load_s3_list(s3_list_path)

        # Keep only files that exist as GeoTIFF
        df = filter_cog_exists(df, s3_files_df)

    df['geometry'] = df.apply(construct_geometry, axis=1)
    gdf = gpd.GeoDataFrame(df)

    # Filter within provided bounding box
    if bbox:
        bbox = box(*map(float, bbox.split(',')))
        gdf = gdf[gdf.geometry.intersects(bbox)]

    maxzoom = gdf.apply(
        lambda row: get_maxzoom(row['scale'], row['scanner_resolution']),
        axis=1)
    maxzoom = round(maxzoom.mean())
    minzoom = maxzoom - 5

    # Convert to features
    cols = ['scale', 'year', 's3_tif', 'geometry', 'cell_id']
    features = gdf[cols].__geo_interface__['features']

    mosaic = MosaicJSON.from_features(
        features,
        minzoom=minzoom,
        maxzoom=maxzoom,
        asset_filter=asset_filter,
        accessor=path_accessor)

    print(json.dumps(mosaic.dict(), separators=(',', ':')))




def path_accessor(feature):
    key = feature['properties']['s3_tif']
    url = f's3://prd-tnm/{key}'
    map_bounds = asShape(feature['geometry']).bounds
    data = {'url': url, 'map_bounds': map_bounds}
    return json.dumps(data, separators=(',', ':'))


def asset_filter(tile, intersect_dataset, intersect_geoms, **kwargs):
    """Custom filter
    """
    # preference = kwargs.get('preference', ['scale', 'latest'])
    sort_by = kwargs.get('sort_by', ['scale', 'year'])
    sort_ascending = kwargs.get('sort_ascending', [True, False])

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(intersect_dataset)
    gdf['intersect_geoms'] = intersect_geoms

    # Sort by preference
    gdf = gdf.sort_values(sort_by, ascending=sort_ascending)

    # Take highest preference within each group formed by cell_id
    gdf = gdf.groupby('cell_id').head(1)

    # Find intersection percent
    tile_geom = polygons(mercantile.feature(tile)['geometry']['coordinates'][0])
    gdf['int_pct'] = _intersect_percent(tile_geom, gdf['intersect_geoms'])

    # Sort on intersection percent
    gdf = gdf.sort_values('int_pct', ascending=False)

    # Return geojson features
    return gdf.__geo_interface__['features']


def load_s3_list(s3_list_path):
    """Filter df using list of COG files
    """
    # Load list of files into DataFrame
    with open(s3_list_path) as f:
        lines = [l.strip() for l in f.readlines()]

    s3_files_df = pd.DataFrame(lines, columns=['path'])

    # Double check that all paths end in .tif
    s3_files_df = s3_files_df[s3_files_df['path'].str.endswith('.tif')]

    return s3_files_df


def construct_geometry(row):
    return box(
        row['w_long'],
        row['s_lat'],
        row['e_long'],
        row['n_lat'],
    )


def construct_s3_tif_url(series: pd.Series) -> pd.Series:
    """Construct S3 GeoTIFF path from HTTP GeoPDF path

    Keep key only, not bucket.

    Args:
        - series: pd.Series of HTTP paths to GeoPDFs

    Returns:
        pd.Series of S3 keys to GeoTIFFs
    """
    parts = series.apply(unquote).str.split('/')

    # Remove bucket
    paths = parts.apply(lambda x: '/'.join(x[3:6]))

    # Add GeoTIFF
    paths += '/GeoTIFF/'

    # Add state
    paths += parts.apply(lambda x: x[7]) + '/'

    # Skip over scale, add filename
    paths += parts.apply(lambda x: x[9].replace('.pdf', '.tif'))

    return paths


def filter_cog_exists(df, s3_files_df):
    """Filter rows to include only GeoTIFF files that exist on S3
    """
    return df.merge(
        s3_files_df, how='inner', left_on='s3_tif', right_on='path').drop(
            'path', axis=1)


def get_maxzoom(scale, dpi, tilesize=512):
    """Get maxzoom for map from scale and dpi

    Ref: https://gis.stackexchange.com/a/85322
    """
    m_per_pixel = 0.0254 / dpi * scale
    return zoom_for_pixelsize(m_per_pixel, tilesize=tilesize)


