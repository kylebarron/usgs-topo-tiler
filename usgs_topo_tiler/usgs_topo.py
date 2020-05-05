"""usgs_topo_tiler.usgs_topo: USGS Historical topo processing."""

from typing import Any, Tuple

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import transform_bounds
from rio_tiler import reader


def get_containing_quad(minx, miny, maxx, maxy):
    """Get Quadrangle within image bounds
    """
    minx = minx + (abs(minx) % .125)
    miny = miny - (miny % .125) + .125
    maxx = maxx + (abs(maxx) % .125) - .125
    maxy = maxy - (maxy % .125)
    return [minx, miny, maxx, maxy]


def get_cutline(r):
    """Get cutline to remove collar from image

    Cutline is in _image_ coordinates.

    Args:
        - r: opened rasterio dataset
    """
    # Convert image bounds to wgs84
    image_wgs_bounds = transform_bounds(r.crs, CRS.from_epsg(4326), *r.bounds)

    # Get containing quad
    quad_wgs_bounds = get_containing_quad(*image_wgs_bounds)

    # Convert back to source CRS
    image_bounds = r.bounds
    quad_bounds = transform_bounds(CRS.from_epsg(4326), r.crs, *quad_wgs_bounds)

    # Buffers in wgs84
    buffers = np.abs(np.array(quad_bounds) - np.array(image_bounds))

    crs_width = image_bounds[2] - image_bounds[0]
    img_width = r.width
    crs_height = image_bounds[3] - image_bounds[1]
    img_height = r.height

    # Origin is in the top left
    left = round(buffers[0] / crs_width * img_width)
    bottom = img_height - round(buffers[1] / crs_height * img_height)
    right = img_width - round(buffers[2] / crs_width * img_width)
    top = round(buffers[3] / crs_height * img_height)

    wkt = f'POLYGON (({left} {top}, {left} {bottom}, {right} {bottom}, {right} {top}))'
    return wkt


def tile(
        address: str,
        tile_x: int,
        tile_y: int,
        tile_z: int,
        tilesize: int = 256,
        **kwargs: Any,
) -> Tuple[np.ndarray, np.array]:
    """
    Create mercator tile from any images.
    Attributes
    ----------
        address : str
            file url.
        tile_x : int
            Mercator tile X index.
        tile_y : int
            Mercator tile Y index.
        tile_z : int
            Mercator tile ZOOM level.
        tilesize : int, optional (default: 256)
            Output image size.
        kwargs: dict, optional
            These will be passed to the 'rio_tiler.reader.tile' function.
    Returns
    -------
        data : np ndarray
        mask : np array
    """
    with rasterio.open(address) as src_dst:
        cutline = get_cutline(src_dst)
        return reader.tile(
            src_dst,
            tile_x,
            tile_y,
            tile_z,
            tilesize,
            warp_vrt_option={'cutline': cutline},
            **kwargs)
