"""Setup for usgs-topo-tiler."""

from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

# Runtime requirements.
inst_reqs = ["numpy", "rasterio", "rio-tiler>=2.0a5"]

extra_reqs = {
    "scripts": [
        "click",
        "cogeo_mosaic",
        "python-dateutil",
        "requests",
        "rtree",
        "shapely", ]}

setup(
    name="usgs-topo-tiler",
    version="0.1.0",
    description="rio-tiler plugin to read mercator tiles from USGS Topo Quads",
    long_description=readme,
    long_description_content_type="text/markdown",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering :: GIS", ],
    keywords="COG cogeo usgs topo raster map tiler gdal rasterio",
    author="Kyle Barron",
    author_email="kylebarron2@gmail.com",
    url="https://github.com/kylebarron/usgs-topo-tiler",
    license="MIT",
    packages=find_packages(
        exclude=["ez_setup", "scripts", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
