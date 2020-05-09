"""usgs_topo_tiler.cutline: Generate cutline for image."""
from typing import List

import numpy as np
from rasterio.crs import CRS
from rasterio.warp import transform_bounds


def get_cutline(r, quad_wgs_bounds: List[float]):
    """Get cutline to remove collar from image

    Cutline is in _image_ coordinates.

    Args:
        - r: opened rasterio dataset
        - quad_wgs_bounds: [minx, miny, maxx, maxy] in WGS84 of the image
          without the collar
    """
    # Convert back to source CRS
    image_bounds = r.bounds
    quad_bounds = transform_bounds(CRS.from_epsg(4326), r.crs, *quad_wgs_bounds)

    # Buffers for each side of the image in wgs84
    buffers = np.abs(np.array(quad_bounds) - np.array(image_bounds))

    crs_width = image_bounds[2] - image_bounds[0]
    img_width = r.width
    crs_height = image_bounds[3] - image_bounds[1]
    img_height = r.height

    # Origin is in the top left
    left = buffers[0] / crs_width * img_width
    bottom = img_height - buffers[1] / crs_height * img_height
    right = img_width - buffers[2] / crs_width * img_width
    top = buffers[3] / crs_height * img_height

    wkt = f'POLYGON (({left} {top}, {left} {bottom}, {right} {bottom}, {right} {top}))'
    return wkt
