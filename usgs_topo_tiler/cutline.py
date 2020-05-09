"""usgs_topo_tiler.cutline: Generate cutline for image."""
import numpy as np
from rasterio.crs import CRS
from rasterio.warp import transform_bounds


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
    left = buffers[0] / crs_width * img_width
    bottom = img_height - buffers[1] / crs_height * img_height
    right = img_width - buffers[2] / crs_width * img_width
    top = buffers[3] / crs_height * img_height

    wkt = f'POLYGON (({left} {top}, {left} {bottom}, {right} {bottom}, {right} {top}))'
    return wkt
