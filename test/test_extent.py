import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.warp import transform_bounds
from usgs_topo_tiler.extent import get_extent

TEST_CASES = [(
    'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/AK/AK_Ruby_361345_1951_250000_geo.tif',
    [-156, 64, -153, 65])]


@pytest.mark.parametrize("url,map_bounds", TEST_CASES)
def test_extent(url, map_bounds):
    with rasterio.open(url) as r:
        # Convert image bounds to wgs84
        image_wgs_bounds = transform_bounds(
            r.crs, CRS.from_epsg(4326), *r.bounds)

        extent = get_extent(image_wgs_bounds, url)
        for x, y in zip(extent, map_bounds):
            msg = f'{extent}, {map_bounds} not approx equal'
            assert x == pytest.approx(y), msg
