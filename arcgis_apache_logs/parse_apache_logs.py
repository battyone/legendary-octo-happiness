# standard library imports
import gzip
import logging
import pathlib
import re

# 3rd party library imports
import lxml.etree
import pandas as pd

# local imports
from .ip_address import IPAddressProcessor
from .referer import RefererProcessor
from .services import ServicesProcessor
from .summary import SummaryProcessor
from .user_agent import UserAgentProcessor


class ApacheLogParser(object):
    """
    Attributes
    ----------
    database_file : path or str
        Path to database
    infile : file-like
        The apache log file (can be stdin).
    logger : object
        Log any pertinent events.
    project : str
        Either nowcoast or idpgis
    """
    def __init__(self, project, infile=None, document_root=None,
                 services_only=False):
        """
        Parameters
        ----------
        infile : str
            Path to gzipped log file
        document_root : str
            Where the database and graphical output is written
        services_only : bool
            If true, do not track referers, ip addresses, or user agents.
        """
        self.project = project
        self.infile = infile
        self.services_only = services_only

        if document_root is None:
            self.root = pathlib.Path.home() \
                        / 'Documents' \
                        / 'arcgis_apache_logs'
        else:
            self.root = pathlib.Path(document_root)

        self.setup_logger()

        kwargs = {'logger': self.logger, 'document_root': document_root}
        self.ip_address = IPAddressProcessor(self.project, **kwargs)
        self.referer = RefererProcessor(self.project, **kwargs)
        self.services = ServicesProcessor(self.project, **kwargs)
        self.summarizer = SummaryProcessor(self.project, **kwargs)
        self.user_agent = UserAgentProcessor(self.project, **kwargs)

        # Setup a skeleton output document.
        self.doc = lxml.etree.Element('html')
        head = lxml.etree.SubElement(self.doc, 'head')
        style = lxml.etree.SubElement(head, 'style')
        style.text = ''
        body = lxml.etree.SubElement(self.doc, 'body')
        ul = lxml.etree.SubElement(body, 'ul')
        ul.attrib['class'] = 'tableofcontents'

    def setup_logger(self):

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        format = '%(asctime)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(format)
        ch.setFormatter(formatter)

        self.logger.addHandler(ch)

    def parse_input(self):
        """
        Process the entire log file.
        """
        if self.infile is None:
            return

        pattern = r'''
            # (?P<ip_address>((\d+.\d+.\d+.\d+)|((\w*?:){6}(\w*?:)?(\w+)?)))
            (?P<ip_address>.*?)
            \s
            # Client identity, always -?
            -
            \s
            # Remote user, always -?
            -
            \s
            # Time of request.  The timezone is always UTC, so don't bother
            # parsing it.
            \[(?P<timestamp>\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})\s.....\]
            \s
            # The request
            "(?P<request_op>(GET|DELETE|HEAD|OPTIONS|POST|PROPFIND|PUT))
            \s
            (?P<path>.*?)
            \s
            HTTP\/1.1"
            \s
            # Status code
            (?P<status_code>\d+)
            \s
            # payload size
            (?P<nbytes>\d+)
            \s
            # referer
            "(?P<referer>.*?)"
            \s
            # user agent
            "(?P<user_agent>.*?)"
            \s
            # something else that seems to always be "-"
            "-"
            '''
        regex = re.compile(pattern, re.VERBOSE)

        records = []

        self.logger.info(f"Parsing {self.infile}...")

        for line in gzip.open(self.infile, mode='rt', errors='replace'):
            m = regex.match(line)
            if m is None:
                msg = (
                    f"This line from the apache log files was not matched.\n"
                    f"\n"
                    f"{line}"
                )
                self.logger.warning(msg)
                continue

            # the 4th row is to designate a "hit".
            records.append((
                m.group('timestamp'),
                m.group('ip_address'),
                m.group('path'),
                1,
                int(m.group('status_code')),
                int(m.group('nbytes')),
                m.group('referer'),
                m.group('user_agent')
            ))

            if len(records) % 1000000 == 0:
                self.process_records(records)

                # reset for the next batch
                records = []

        self.process_records(records)

    def process_records(self, records):

        columns = [
            'date', 'ip_address', 'path', 'hits', 'status_code', 'nbytes',
            'referer', 'user_agent'
        ]
        df = pd.DataFrame.from_records(records, columns=columns)

        format = '%d/%b/%Y:%H:%M:%S'
        df['date'] = pd.to_datetime(df['date'], format=format)

        df['errors'] = df.eval(
            'status_code < 200 or status_code >= 400'
        ).astype(int)

        self.logger.info(f"Parsed {len(df)} log records...")

        if not self.services_only:
            self.ip_address.process_raw_records(df)
            self.referer.process_raw_records(df)
            self.user_agent.process_raw_records(df)

        self.services.process_raw_records(df)
        self.summarizer.process_raw_records(df)

    def process_graphics(self):

        if self.infile is not None:
            # Do not produce graphics when parsing.
            return

        if not self.services_only:
            self.summarizer.process_graphics(self.doc)
            self.referer.process_graphics(self.doc)

        self.services.process_graphics(self.doc)

        if not self.services_only:
            self.ip_address.process_graphics(self.doc)
            self.user_agent.process_graphics(self.doc)

        # Write the HTML document.
        path = self.root / f'{self.project}.html'
        lxml.etree.ElementTree(self.doc).write(str(path))
