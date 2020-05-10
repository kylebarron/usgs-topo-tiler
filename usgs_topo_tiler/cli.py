"""
Entry point for CLI. CLI code is in the scripts/ folder.

See

https://stackoverflow.com/a/39228156
https://github.com/drorata/mwe-subcommands-click

for how to separate a click CLI into subfiles
"""
import click

from usgs_topo_tiler.scripts import list_s3, metadata, mosaic, mosaic_bulk


@click.group()
def main():
    pass

main.add_command(list_s3)
main.add_command(metadata)
main.add_command(mosaic)
main.add_command(mosaic_bulk)

if __name__ == '__main__':
    main()
