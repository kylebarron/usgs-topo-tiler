from urllib.parse import unquote

import geopandas as gpd
import pandas as pd
from keplergl_cli import Visualize
from shapely.geometry import box

path = '../data/topomaps_all/topomaps_all.csv'
s3_list_path = '../data/geotiff_files.txt'



# TODO: Add filters for topographic, woodland tint. Some maps made at the same time with neighboring ids are quite different, e.g.
# CA_Acton_302201_1959_24000_geo.tif
# CA_Acton_302202_1959_24000_geo.tif

# TODO: option for high scale, medium scale, low scale
# High scale: 24k, Medium scale: 63k, low scale: 250k
def main(meta_path, s3_list_path):
    df = pd.read_csv(path, low_memory=False)

    # Keep only historical maps
    # Newer maps are only in GeoPDF, and not in GeoTIFF, let alone COG
    df = df[df['Series'] == 'HTMC']

    df['geometry'] = df.apply(construct_geometry, axis=1)
    gdf = gpd.GeoDataFrame(df)

    # Load list of GeoTIFF files
    s3_files_df = load_s3_list(s3_list_path)

    # Create s3 GeoTIFF paths from metadata
    gdf['s3_tif'] = construct_s3_tif_url(gdf['Download Product S3'])

    filter_cog_exists

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

