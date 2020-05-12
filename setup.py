"""Setup for usgs-topo-tiler."""

from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

# Runtime requirements.
inst_reqs = ["numpy", "rasterio", "rio-tiler>=2.0a6"]

extra_reqs = {
    "cli": [
        "boto3", "click", "cogeo_mosaic", "geopandas", "mercantile", "pandas",
        "python-dateutil", "requests", "shapely"]}

setup(
    name="usgs-topo-tiler",
    version="0.2.0",
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
        "Topic :: Scientific/Engineering :: GIS"],
    keywords="COG cogeo usgs topo raster map tiler gdal rasterio",
    author="Kyle Barron",
    author_email="kylebarron2@gmail.com",
    url="https://github.com/kylebarron/usgs-topo-tiler",
    license="MIT",
    entry_points={
        'console_scripts': ['usgs-topo-tiler=usgs_topo_tiler.cli:main', ], },
    packages=find_packages(
        exclude=["ez_setup", "scripts", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
