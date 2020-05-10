"""
Entry point for CLI. CLI code is in the scripts/ folder.

See

https://stackoverflow.com/a/39228156
https://github.com/drorata/mwe-subcommands-click

for how to separate a click CLI into subfiles
"""
import click

import usgs_topo_tiler.scripts as scripts


@click.group()
def main():
    pass


@main.group()
def list_s3():
    pass


list_s3.add_command(scripts.list_s3.main)


@main.group()
def metadata():
    pass


metadata.add_command(scripts.metadata.main)


@main.group()
def mosaic():
    pass


mosaic.add_command(scripts.mosaic.main)


@main.group()
def mosaic_bulk():
    pass


mosaic_bulk.add_command(scripts.mosaic_bulk.main)

if __name__ == '__main__':
    main()
