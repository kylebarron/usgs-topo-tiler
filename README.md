# usgs-topo-tiler

Python package to read Web Mercator map tiles from USGS Historical Topographic
Maps, and utilities to create a [MosaicJSON][mosaicjson] collection from these
maps.

[mosaicjson]: https://github.com/developmentseed/mosaicjson-spec/

![Grand Canyon Historical Mosaic][grca_mosaic]

[grca_mosaic]: https://raw.githubusercontent.com/kylebarron/usgs-topo-tiler/master/assets/grca_mosaic.jpg

A mosaic of USGS historical maps around the Grand Canyon, with added relief
shading.

## Overview

I stumbled upon a hidden gem: the entire USGS historical topographic map
archive, consisting of 183,112 digitized maps created between 1884 and 2006, is
stored in Cloud-Optimized GeoTIFF (COG) format on AWS S3.

The fact that maps are accessible publicly and stored in COG format means that
you can easily and cheaply set up a serverless function on AWS Lambda to serve
map tiles on the fly.

The [COG format][cogeo] is a backwards-compatible, cloud-native storage format
for raster files that allow selected portions of the file to be read over the
network without needing to download and parse the entire file. This fast random
read access allows for dynamic tiling of map tiles on demand, without needing to
preprocess and store any map data.

[cogeo]: https://www.cogeo.org/

There are three parts to serving your own tiles:

- `usgs-topo-tiler`: a library to extract a _single_ Web Mercator tile from _one_ source historical map.
- `usgs-topo-tiler`'s CLI, which helps to construct MosaicJSON files. These files tell `usgs-topo-mosaic` what source files should be combined to create a single Web Mercator tile.
- [`usgs-topo-mosaic`][usgs-topo-mosaic]: a library to use a MosaicJSON file created above to create a seamless mosaic of tiles. This is designed to be deployed with AWS Lambda and AWS API Gateway as a serverless tile endpoint.

[usgs-topo-mosaic]: https://github.com/kylebarron/usgs-topo-mosaic

## Generate a Web Mercator tile

### Install

```bash
pip install usgs-topo-tiler 'rio-tiler>=2.0a6'
```

### Usage

Here I'll show a quick overview of reading a single mercator tile from a single
USGS historical map. If you're looking for a specific map, the simplest way is
probably to use the [National Map Viewer][nationalmap]. Check the box for
"Historical Topographic Maps", make sure the file format is "GeoTIFF". Click
"Find Products", and then right click "Download" to get the HTTPS url to the
GeoTIFF on S3.

[nationalmap]: https://viewer.nationalmap.gov/basic/

For this demo, I'll make a mercator tile from an 1897 topographic map of
Yosemite Valley.

**Read a tile from a file over the internet**

```py
from usgs_topo_tiler import tile

url = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CA/CA_Yosemite_299696_1897_125000_geo.tif'
# Mercator tile
x, y, z = 687, 1583, 12

tile, mask = tile(url, x, y, z, tilesize=512)
print(tile.shape)
# (3, 512, 512)
print(mask.shape)
# (512, 512)
```

**Create image from tile**

Note that if you're using `rio-tiler` v1, you should replace `render` with
`array_to_image`.

```py
from rio_tiler.utils import render

buffer = render(tile, mask, img_format='png')
```

**Write image to file**

```py
with open('yose_1897.png', 'wb') as f:
    f.write(buffer)
```

You now have a 512x512 png image aligned with the Web Mercator grid, and because
the source is a _Cloud-optimized_ GeoTIFF, the image was made with a minimal
number of requests to the source, and without reading the entire GeoTIF.

![Yosemite, 1897 Web Mercator tile][yose_1897]

[yose_1897]: https://github.com/kylebarron/usgs-topo-tiler/blob/master/assets/yose_1897.png?raw=true

## Create a MosaicJSON

The process described above is for create _one_ tile. But often we want to join
many mercator tiles to make a seamless web map. This is where
[MosaicJSON][mosaicjson] comes in. It describes how to join sources and where to
place them.

This section outlines how to create a MosaicJSON from USGS historical topo
assets. This MosaicJSON can then be used with `usgs-topo-mosaic` to serve a web
map of tiles with AWS Lambda.

### Install

When you install `usgs-topo-tiler`, it doesn't include dependencies necessary
for the CLI commands so as to keep the deployment size small when used with
[`usgs-topo-mosaic`][usgs-topo-mosaic].

To install the additional CLI dependencies, run:

```bash
pip install 'usgs-topo-tiler[cli]'
```

### Download bulk metadata

First you need to download metadata including at least the geospatial bounds of
each map, and the URL of each map. It's possible to use the [National Map
API][nationalmap_api] to retrieve such metadata, however I prefer to download a
CSV of bulk metadata from S3. This file includes metadata on every image in
their collection.

[nationalmap_api]: https://viewer.nationalmap.gov/tnmaccess/api/index

```bash
mkdir -p data
wget https://prd-tnm.s3-us-west-2.amazonaws.com/StagedProducts/Maps/Metadata/topomaps_all.zip -P data/
unzip topomaps_all.zip
```

`data/topomaps_all.csv` is the extracted bulk metadata file. `data/readme.txt`
has helpful information about what fields are in the bulk metadata file.

### Download list of COG files:

Occasionally there are some files listed in the metadata that don't exist as
GeoTIFF. I download a list of the `.tif` files on S3 so that I can
cross-reference against the metadata and ensure that only files that exist are
included in the MosaicJSON.

This step is optional, but recommended.

```bash
mkdir -p data/
usgs-topo-tiler list-s3 \
    --bucket 'prd-tnm' \
    --prefix 'StagedProducts/Maps/HistoricalTopo/GeoTIFF/' \
    --ext '.tif' \
    > data/geotiff_files.txt

> wc -l data/geotiff_files.txt
    183112 data/geotiff_files.txt
```

_183112_ COG files!

### Create MosaicJSON

Now you're ready to start creating mosaics. This isn't entirely straightforward
because maps were created at different times and at different scales in
different regions of the U.S. So it's not usually as simple as creating a mosaic
of all maps of a single scale, unless you're ok with having gaps in the mosaic
spatially, where tiles might return empty data.

#### Footprints

One of the best way to visually see the results of a filtering query on the
metadata is to generate _footprints_ and then display them on a map.

Lets say we want to create a mosaic of mid-scale maps. We can use the
`--filter-only` cli flag to export newline-delimited GeoJSON of the query.

```bash
usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 63360 \
    --max-scale 249000 \
    --filter-only \
    > mid_scale_footprints.geojsonl
```

Then we can visualize this data, e.g. with [my CLI][keplergl_cli] for
[kepler.gl][keplergl].

[keplergl]: https://kepler.gl/
[keplergl_cli]: https://github.com/kylebarron/keplergl_cli

```bash
kepler mid_scale_footprints.geojsonl
```

This illustrates the core problem of these historical maps when making a
MosaicJSON. Some areas have been mapped more than others, and some have never
been mapped at this scale range. If you were to create a MosaicJSON from these
parameters, you'd get empty images when requesting data over Northern Montana
and Western Texas.

![][mid_scale_footprints]

[mid_scale_footprints]: https://github.com/kylebarron/usgs-topo-tiler/blob/master/assets/mid_scale_footprints.png?raw=true

#### Generate MosaicJSON

Once you know the desired parameters of your query, remove the `--filter-only`
flag to generate the MosaicJSON. For example:

```bash
usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 63360 \
    --max-scale 249000 \
    > mid_scale_mosaic.json
```

`mid_scale_mosaic.json` is now a MosaicJSON file that can be used with
`usgs-topo-mosaic` to render a web map. Note, however that this uses a custom
asset string format, as described in [Removing Map
Collars](#removing-map-collars), and won't necessarily work with all other
MosaicJSON tools.

#### Examples

**Low zoom, newest available**

```bash
usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 250000 \
    > mosaic_low.json
```

**Medium zoom, newest available, filling in with lower-resolution maps where necessary**

```bash
usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 63360 \
    > mosaic_medium.json
```

**Medium zoom, oldest available, filling in with lower-resolution maps where necessary**

```bash
usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 63360 \
    --sort-preference oldest \
    > mosaic_medium_oldest.json
```

**High zoom, newest available, continental U.S. only**

```bash
usgs-topo-tiler mosaic-bulk \
    --meta-path data/topomaps_all.csv \
    --s3-list-path data/geotiff_files.txt \
    --min-scale 24000 \
    --max-scale 63359 \
    `# Lower 48 states only` \
    --bounds '-161.96,12.85,-55.01,50.53' \
    > mosaic_high.json
```

#### API

```
Usage: usgs-topo-tiler mosaic-bulk [OPTIONS]

  Create MosaicJSON from CSV of bulk metadata

Options:
  --meta-path PATH                Path to csv file of USGS bulk metadata dump
                                  from S3  [required]

  --s3-list-path PATH             Path to txt file of list of s3 GeoTIFF files
  --min-scale FLOAT               Minimum map scale, inclusive
  --max-scale FLOAT               Maximum map scale, inclusive
  --min-year FLOAT                Minimum map year, inclusive
  --max-year FLOAT                Maximum map year, inclusive
  --woodland-tint / --no-woodland-tint
                                  Filter on woodland tint or no woodland tint.
                                  By default no filtering is applied.

  --allow-orthophoto              Allow orthophoto  [default: False]
  --bounds TEXT                   Bounding box for mosaic. Must be of format
                                  "minx,miny,maxx,maxy"

  -z, --minzoom INTEGER           Force mosaic minzoom
  -Z, --maxzoom INTEGER           Force mosaic maxzoom
  --quadkey-zoom INTEGER          Force mosaic quadkey zoom
  --sort-preference [newest|oldest|closest-to-year]
                                  Method for choosing assets within a given
                                  mercator tile at the quadkey zoom.
                                  [default: newest]

  --closest-to-year INTEGER       Year used for comparisons when preference is
                                  closest-to-year.

  --filter-only                   Output filtered GeoJSON features, without
                                  creating the MosaicJSON. Useful for
                                  inspecting the footprints   [default: False]

  --help                          Show this message and exit.
```

## Addendum

### Removing map collars

All of the USGS historical maps have _collars_, regions of space around the map
where metadata is printed. In order to create continuous map tiles from a
collection of these maps, these collars have to be clipped, so that only the map
is showing.

![Ruby, AK][ruby_ak]

[ruby_ak]: https://github.com/kylebarron/usgs-topo-tiler/blob/master/assets/ruby_ak.jpg?raw=true

These maps are georeferenced, which means that it's straightforward to remove
the collar when you know the actual bounds contained in the map. However, I've
found that there's no reliable way to determine the bounds on the fly with just
the image and its filename.

While building the mosaic ahead of time, you have access to this information,
but with the usual tiling setup, you'd only have access to the URL and image
while tiling.

To get around this, I apply a "hack" to the MosaicJSON format. Instead of just
encoding a URL string, I encode the url _and_ the bounds of the map as a JSON
string.

**Summary**: when you build a mosaic using the cli in this library, it encodes a
non-standard MosaicJSON that works well with the `usgs-mosaic-tiler` tiler, but
isn't necessarily readable by other MosaicJSON tools
