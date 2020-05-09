"""usgs_topo_tiler.grid: Find bounds of image not including collar."""

import re
from typing import Dict, List
from urllib.parse import unquote

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
    96000: .25,
    100000: .5,
    125000: .5,
    192000: .5}


def parse_url(url: str) -> int:
    """Parse metadata from url

    Args
        - url: Asset url
    """
    fname = unquote(url).split('/')[-1]

    regex = (
        r'^(?P<state>[A-Z]{2})_'
        r'(?P<map_name>.*)_'
        r'(?P<map_id>\d+)_'
        r'(?P<year>\d{4})_'
        r'(?P<scale>\d+)'
        r'\_[a-zA-Z]*\.tif$')

    match = re.search(regex, fname)

    map_name = match.group('map_name').lower().replace(' ', '')
    map_id = int(match.group('map_id'))
    state = match.group('state').lower()
    year = int(match.group('year'))
    scale = int(match.group('scale'))
    return {
        'scale': scale,
        'year': year,
        'state': state,
        'map_id': map_id,
        'map_name': map_name}


def _get_extent(bounds: List[float], offset_x: float,
                offset_y: float) -> List[float]:
    """Get extent of image without collar
    """
    minx, miny, maxx, maxy = bounds

    minx = minx + (abs(minx) % offset_x)
    miny = miny - (miny % offset_y) + offset_y
    maxx = maxx + (abs(maxx) % offset_x) - offset_x
    maxy = maxy - (maxy % offset_y)
    return [minx, miny, maxx, maxy]


def estimate_extent(bounds: List[float], url: str) -> List[float]:
    """Get extent of image without collar

    Args:
        - bounds: opened rasterio dataset
        - url: url to COG on S3
    """
    meta = parse_url(url)
    offset_x, offset_y = get_offsets(bounds, meta)
    return _get_extent(bounds, offset_x, offset_y)


def get_offsets(bounds: List[float], meta: Dict) -> List[float]:
    scale = meta['scale']
    easy_offset = SCALE_DEGREE_OFFSET_XW.get(scale)
    if easy_offset:
        return [easy_offset, easy_offset]

    # Custom cases
    if scale == 63360:
        return _get_offset_63360(bounds)

    if scale == 250000:
        return _get_offset_250000(bounds, meta)


def _get_offset_63360(bounds: List[float]) -> List[float]:
    """Custom cases for scale==63360"""
    maxy = bounds[3]

    # Lower 48
    if maxy < 49.25:
        return [.25, .25]

    # Sections of Alaska
    if maxy < 59.25:
        return [1 / 3, .25]

    if maxy < 62.25:
        return [.375, .25]

    if maxy < 68.25:
        return [.5, .25]

    # Each map has a width of .6
    return [.2, .25]


def _get_offset_250000(bounds: List[float], meta: Dict) -> List[float]:
    offset_x, offset_y = .5, .5
    minx, miny, maxx, maxy = bounds

    # Alaska
    if miny > 49:
        if maxy < 59.5:
            offset_x, offset_y = .5, .25
        else:
            offset_x, offset_y = 1, 1


    map_name = meta['map_name']
    state = meta['state']
    if state == 'ca' and map_name == 'santacruz':
        offset_x = .2
    elif state == 'wa' and map_name == 'vancouver':
        # west long is -124.0833
        offset_x = .1
    elif state == 'or' and map_name == 'salem':
        # west long is -124.1833
        offset_x = .18
    elif state == 'sc' and map_name == 'georgetown':
        # east long is -77.8833333
        offset_x = .12
    elif state == 'ri' and map_name == 'providence':
        # east long is -69.8833333
        offset_x = .12

    return [offset_x, offset_y]
