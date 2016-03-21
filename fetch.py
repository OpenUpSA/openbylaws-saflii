#!/bin/env python

# Script that downloads documents from indigo.openbylaws.org.za
# and stores them for use with the SAFLII content system.

import os
import requests
import errno
import json
import codecs
import urlparse
import click


API_ENDPOINT = os.environ.get('INDIGO_API_URL', "http://indigo.openbylaws.org.za/api")
BASE_DIR = os.getcwd()

session = requests.Session()


def make_path(uri, doc, target):
    return os.path.join(target)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e
        pass


def download(uri, doc, target):
    """ Download this document.
    """
    path = make_path(uri, doc, target)
    click.echo("Fetching: %s -> %s" % (uri, path))
    mkdir_p(path)

    base_fname = os.path.join(path, base_filename(doc))

    # add alternate forms
    for title in ['Standalone HTML', 'ePUB', 'PDF']:
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

    fname = os.path.join(path, 'metadata.json')
    with codecs.open(fname, 'w', 'utf-8') as f:
        json.dump(doc, f)


def base_filename(doc):
    # the filename to use for this doc
    return doc['frbr_uri'][1:].replace('/', '-')


def do_fetch(docs, target):
    for uri, doc in docs.iteritems():
        download(uri, doc, target)

    write_manifest(docs, target)


def write_manifest(docs, target):
    fname = os.path.join(target, 'manifest.txt')
    click.echo("Writing manifest to %s" % fname)
    with codecs.open(fname, 'w', 'utf-8') as f:
        for doc in docs.itervalues():
            fname = base_filename(doc)
            f.write("\"%s\",%s,%s.html\n" % (doc['title'], doc['year'], fname))


def get_remote_documents(url):
    resp = session.get(url + '/documents.json')
    resp.raise_for_status()
    docs = resp.json()['results']
    # only published docs
    return [d for d in docs if not d['draft']]


def expression_uri(doc):
    return '/'.join([doc['frbr_uri'], doc['language'], doc['expression_date'] or doc['publication_date']])


@click.command()
@click.option('--target', default='.', help='Target directory')
@click.option('--url', default=API_ENDPOINT, help='Indigo API URL')
def fetch(target, url):
    click.echo("Archiving documents from %s to %s" % (url, target))

    remote = get_remote_documents(url)
    remote = {expression_uri(d): d for d in remote}
    click.echo("Remote: %d" % len(remote))
    do_fetch(remote, target)


if __name__ == '__main__':
    fetch()
