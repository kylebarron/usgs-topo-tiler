"""usgs_topo_tiler.grid: Find bounds of image not including collar."""

import re
from typing import List

# Mapping from image scale to the minimum possible offset
# This is created by looking at the cross tabulation of grid size by scale. For
# each scale, I look at all possible grid offsets and take the smallest one. So
# if some files with a given scale have a 7.5 X 15 Minute grid size, that would
# have an assigned offset of .125, since 7.5' is .125 of a degree.
# Ref table in https://github.com/kylebarron/usgs-topo-tiler/issues/8
SCALE_DEGREE_OFFSET_XW = {
    10000: .0625,
    12000: .0625,
    20000: .125,
    21120: .125,
    24000: .125,
    25000: .125,
    30000: .125,
    31680: .125,
    48000: .125,
    50000: .25,
    62500: .125,
    63360: .25,
    96000: .25,
    100000: .5,
    125000: .5,
    192000: .5,
    250000: .5}


def parse_scale(url: str) -> int:
    """Parse scale from url

    Args
        - url: Asset url
    """
    regex = r'(\d+)\_[a-zA-Z]*\.tif$'
    match = re.search(regex, url)
    return int(match.group(1))


def _get_extent(bounds: List[float], offset: float) -> List[float]:
    """Get extent of image without collar
    """
    minx, miny, maxx, maxy = bounds

    minx = minx + (abs(minx) % offset)
    miny = miny - (miny % offset) + offset
    maxx = maxx + (abs(maxx) % offset) - offset
    maxy = maxy - (maxy % offset)
    return [minx, miny, maxx, maxy]


def get_extent(bounds: List[float], url: str) -> List[float]:
    """Get extent of image without collar

    Args:
        - bounds: opened rasterio dataset
        - url: url to COG on S3
    """
    scale = parse_scale(url)
    offset = SCALE_DEGREE_OFFSET_XW[scale]
    return _get_extent(bounds, offset)
