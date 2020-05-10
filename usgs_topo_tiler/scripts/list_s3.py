import sys

import boto3
import click


@click.command()
@click.option(
    '-b',
    '--bucket',
    type=str,
    default='prd-tnm',
    show_default=True,
    help='Bucket name')
@click.option(
    '-p',
    '--prefix',
    type=str,
    default='StagedProducts/Maps/HistoricalTopo/GeoTIFF/',
    show_default=True,
    help='Prefix to list within')
@click.option(
    '--ext',
    type=str,
    default='.tif',
    show_default=True,
    help=
    'Suffix/file extension to filter for. To turn off filtering, pass None or an empty string'
)
def list_s3(bucket, prefix, ext):
    """Get listing of files on S3 with prefix and extension
    """
    s3 = boto3.resource('s3')
    s3_bucket = s3.Bucket(bucket)

    if ext:
        ext = '.' + ext.lstrip('.')
    else:
        ext = ''

    counter = 0
    for item in s3_bucket.objects.filter(Prefix=prefix):
        counter += 1
        if counter % 5000 == 0:
            print(f'Found {counter} items so far', file=sys.stderr)

        key = item.key
        if not key.endswith(ext):
            continue

        # Write to stdout
        print(key)


if __name__ == '__main__':
    list_s3()
