from urllib.parse import unquote

import click
import geopandas as gpd
import pandas as pd
from shapely.geometry import box

path = '../data/topomaps_all/topomaps_all.csv'
s3_list_path = '../data/geotiff_files.txt'

# TODO: option for high scale, medium scale, low scale
# High scale: 24k, Medium scale: 63k, low scale: 250k


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
def main(
        meta_path, s3_list_path, min_scale, max_scale, min_year, max_year,
        woodland_tint, allow_orthophoto):
    df = pd.read_csv(path, low_memory=False)

    # Keep only historical maps
    # Newer maps are only in GeoPDF, and not in GeoTIFF, let alone COG
    df = df[df['Series'] == 'HTMC']

    # Create year column as Imprint Year if it exists, otherwise Date On Map
    df['year'] = df['Imprint Year'].fillna(df['Date On Map'])

    # Apply filters
    if min_scale:
        df = df[df['Scale'] >= min_scale]
    if max_scale:
        df = df[df['Scale'] <= max_scale]
    if min_year:
        df = df[df['Year'] >= min_year]
    if max_year:
        df = df[df['Year'] <= max_year]
    if woodland_tint is not None:
        if woodland_tint:
            df = df[df['Woodland Tint'] == 'Y']
        else:
            df = df[df['Woodland Tint'] == 'N']
    if not allow_orthophoto:
        df = df[df['Orthophoto'].isna()]

    # Create s3 GeoTIFF paths from metadata
    df['s3_tif'] = construct_s3_tif_url(df['Download Product S3'])

    if s3_list_path:
        # Load list of GeoTIFF files
        s3_files_df = load_s3_list(s3_list_path)

        # Keep only files that exist as GeoTIFF
        df = filter_cog_exists(df, s3_files_df)

    df['geometry'] = df.apply(construct_geometry, axis=1)
    gdf = gpd.GeoDataFrame(df)

    # Filter (sort) by desired scale
    # What to do when assets don't exist for a given scale?
    # Maybe decide on bins for high/medium/low scale and then plot footprints?

    # Zoom ranges for high/medium/low?

    # Separate mosaics for continental U.S. and Alaska? Might have different
    # zoom ranges?


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
        row['W Long'],
        row['S Lat'],
        row['E Long'],
        row['N Lat'],
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


