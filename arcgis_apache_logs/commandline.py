# standard library imports
import argparse

# local imports
from .parse_apache_logs import ApacheLogParser
from .initialize import Initializer


def parse_arcgis_apache_logs():
    """
    Entry point for parsing the log fragments.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument('project', choices=['idpgis', 'nowcoast'])
    parser.add_argument('--infile')

    help = 'If specified, ignore the user agent, referer, and IP address'
    parser.add_argument('--services-only', action='store_true', help=help)

    help = (
        "Write the documents in this directory.  Default is "
        "$HOME/Documents/arcgis_apache_logs"
    )
    parser.add_argument('--document-root', nargs='?', help=help)

    args = parser.parse_args()

    log_processor = ApacheLogParser(args.project, infile=args.infile,
                                    document_root=args.document_root,
                                    services_only=args.services_only)
    log_processor.parse_input()


def produce_arcgis_apache_graphics():
    """
    Entry point for creating the HTML and graphics.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument('project', choices=['idpgis', 'nowcoast'])

    help = 'If specified, ignore the user agent, referer, and IP address'
    parser.add_argument('--services-only', action='store_true', help=help)

    args = parser.parse_args()

    p = ApacheLogParser(args.project, infile=None,
                        services_only=args.services_only)
    p.process_graphics()


def init_db():
    """
    Entry point for initializing the database.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument('project', choices=['idpgis', 'nowcoast'])

    help = "Initialize the database in this directory."
    parser.add_argument('--document-root', nargs='?', help=help)

    args = parser.parse_args()

    with Initializer(args.project, document_root=args.document_root) as p:
        p.initialize()


def prune_arcgis_apache_database():
    """
    Entry point for cleaning up the database.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument('project', choices=['idpgis', 'nowcoast'])
    args = parser.parse_args()

    with Initializer(args.project) as p:
        p.prune_database()
