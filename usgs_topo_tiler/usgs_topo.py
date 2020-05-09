"""usgs_topo_tiler.usgs_topo: USGS Historical topo processing."""

import json
from typing import Any, List, Tuple

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import transform_bounds
from rio_tiler import reader

from usgs_topo_tiler.cutline import get_cutline
from usgs_topo_tiler.extent import estimate_extent


def tile(
        address: str,
        tile_x: int,
        tile_y: int,
        tile_z: int,
        tilesize: int = 256,
        map_bounds: List[float] = None,
        parse_asset_as_json: bool = True,
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
        map_bounds : List[float], optional (default: inferred)
            Bounds of map excluding border in WGS84
            Normal order: (minx, miny, maxx, maxy)
        parse_asset_as_json : bool, optional (default: True)
            Whether to attempt to parse address as a JSON object with "url" and
            "map_bounds keys"
        kwargs: dict, optional
            These will be passed to the 'rio_tiler.reader.tile' function.
    Returns
    -------
        data : np ndarray
        mask : np array
    """
    # Custom hack that encodes url and map_bounds into address string
    if parse_asset_as_json:
        try:
            asset_dict = json.loads(address)
            address = asset_dict['url']
            map_bounds = asset_dict['map_bounds']
        except json.JSONDecodeError:
            pass

    with rasterio.open(address) as src_dst:
        # Convert image bounds to wgs84
        image_wgs_bounds = transform_bounds(
            src_dst.crs, CRS.from_epsg(4326), *src_dst.bounds)

        # Get extent and cutline
        if not map_bounds:
            map_bounds = estimate_extent(image_wgs_bounds, address)
        cutline = get_cutline(src_dst, map_bounds)

        return reader.tile(
            src_dst,
            tile_x,
            tile_y,
            tile_z,
            tilesize,
            warp_vrt_option={'cutline': cutline},
            **kwargs)
