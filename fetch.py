#!/usr/bin/env python

# Script that downloads documents from indigo.openbylaws.org.za
# and stores them for use with the SAFLII content system.

import os
import requests
import errno
import codecs
import urlparse
import click


API_ENDPOINT = os.environ.get('INDIGO_API_URL', "http://indigo.openbylaws.org.za/api")
BASE_DIR = os.getcwd()
REGIONS = {
    'za-cpt': "City of Cape Town",
    'za-eth': "eThekwini",
    'za-jhb': "City of Johannesburg",
}

session = requests.Session()
session.verify = False


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e
        pass


def download_doc(uri, doc, target):
    """ Download this document.
    """
    path = os.path.join(target, "Data")
    click.echo("Fetching: %s -> %s" % (uri, path))
    mkdir_p(path)

    doc['base_filename'] = base_filename(doc)
    base_fname = os.path.join(path, doc['base_filename'])

    # add alternate forms
    for title in ['Standalone HTML']:  # PDF? ePUB?
        link = [link for link in doc['links'] if link['title'] == title]
        if link:
            link = link[0]

            resp = session.get(link['href'])
            resp.raise_for_status()

            fname = urlparse.urlsplit(link['href']).path
            _, ext = os.path.splitext(fname)

            fname = base_fname + ext
            click.echo(fname)
            with open(fname, 'wb') as f:
                f.write(resp.content)


def base_filename(doc):
    # the filename to use for this doc
    return doc['frbr_uri'][1:].replace('/', '-')


def write_registry(docs, target):
    fname = os.path.join(target, 'Registry.txt')
    click.echo("Writing registry to %s" % fname)

    with codecs.open(fname, 'w', 'utf-8') as f:
        for doc in docs:
            region = '%s-%s' % (doc['country'], doc['locality'])

            title = doc['title']
            if not title.startswith(REGIONS[region]):
                title = REGIONS[region] + ": " + title

            f.write("\"%s.html\" (%s) %s\n" % (doc['base_filename'], doc['publication_date'], title))


def get_remote_documents(url):
    resp = session.get(url + '.json')
    resp.raise_for_status()
    docs = resp.json()['results']
    # only published docs
    return docs[:10]


def expression_uri(doc):
    return '/'.join([doc['frbr_uri'], doc['language'], doc['expression_date'] or doc['publication_date']])


def fetch(url, target):
    click.echo("Archiving documents from %s to %s" % (url, target))

    docs = get_remote_documents(url)
    docs = {expression_uri(d): d for d in docs}
    click.echo("Documents: %d" % len(docs))

    for uri, doc in docs.iteritems():
        download_doc(uri, doc, target)

    return docs.values()


@click.command()
@click.option('--target', default='.', help='Target directory')
@click.option('--url', default=API_ENDPOINT, help='Indigo API URL (%s)' % API_ENDPOINT)
@click.option('--regions', help='Comma-separated region codes (ALL, za-cpt, za-eth, etc.)')
def main(target, url, regions):
    if regions == "ALL":
        regions = REGIONS.keys()
    else:
        regions = regions.split(",")
    click.echo("Regions: " + ", ".join(regions))

    all_docs = []
    for region in regions:
        all_docs.extend(fetch(url + "/" + region, target))

    write_registry(all_docs, target)


if __name__ == '__main__':
    main()
