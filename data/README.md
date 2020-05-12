# Prebuilt data files

The files in this directory were created with the following:

```bash
usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 250000 \
    > mosaic_low_newest.json

usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 250000 \
    --sort-preference oldest \
    > mosaic_low_oldest.json

usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 62500 \
    > mosaic_medium_newest.json

usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 62500 \
    --sort-preference oldest \
    > mosaic_medium_oldest.json

usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 24000 \
    --max-scale 63359 \
    `# Lower 48 states only` \
    --bounds '-161.96,12.85,-55.01,50.53' \
    > mosaic_high_newest.json

usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 24000 \
    --max-scale 63359 \
    --sort-preference oldest \
    `# Lower 48 states only` \
    --bounds '-161.96,12.85,-55.01,50.53' \
    > mosaic_high_oldest.json
```
