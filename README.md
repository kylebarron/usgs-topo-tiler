# usgs-topo-tiler
rio-tiler plugin to read mercator tiles from USGS Topo Quads

##

### Download list of COG files:

```bash
python scripts/list_s3.py \
    --bucket 'prd-tnm' \
    --prefix 'StagedProducts/Maps/HistoricalTopo/GeoTIFF/' \
    --ext '.tif' \
    > data/geotiff_files.txt

> wc -l data/geotiff_files.txt
  183112 data/geotiff_files.txt
```
