# standard library imports
import logging
import pathlib
import sqlite3

# 3rd party library imports
import pandas as pd
import requests

# Local imports
from .common import CommonProcessor


class Initializer(CommonProcessor):
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
    def __init__(self, project, document_root=None):
        """
        Parameters
        ----------
        graphics : bool
            Whether or not to produce any plots or HTML output.
        """
        self.project = project

        self.setup_logger()

        if document_root is None:
            self.root = pathlib.Path.home() \
                        / 'Documents' \
                        / 'arcgis_apache_logs'
        else:
            self.root = pathlib.Path(document_root)

        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)

        self.database = self.root / f'arcgis_apache_{self.project}.db'

    def setup_logger(self):

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        format = '%(asctime)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(format)
        ch.setFormatter(formatter)

        self.logger.addHandler(ch)

    def run(self):
        self.initialize_service_tables()
        self.initialize_referer_tables()
        self.initialize_ip_address_tables()
        self.populate_service_lut()

    def initialize_referer_tables(self):
        """
        Verify that all the database tables are setup properly for managing
        the referers.
        """

        cursor = self.conn.cursor()

        sql = """
              CREATE TABLE referer_lut (
                  id integer PRIMARY KEY,
                  name text
              )
              """
        cursor.execute(sql)
        sql = """
              CREATE UNIQUE INDEX idx_referer
              ON referer_lut(name)
              """
        cursor.execute(sql)

    if 'referer_logs' not in df.name.values:

        sql = """
              CREATE TABLE referer_logs (
                  date integer,
                  id integer,
                  hits integer,
                  errors integer,
                  nbytes integer,
                  CONSTRAINT fk_referer_lut_id
                      FOREIGN KEY (id)
                      REFERENCES referer_lut(id)
                      ON DELETE CASCADE
              )
              """
        cursor.execute(sql)

        # Unfortunately the index cannot be unique here.
        sql = """
              CREATE UNIQUE INDEX idx_referer_logs_date
              ON referer_logs(date, id)
              """
        cursor.execute(sql)

    def initialize_database(self):

        # Create the known services and logs tables.
        sql = """
              CREATE TABLE service_lut (
                  id integer PRIMARY KEY,
                  folder text,
                  service text,
                  service_type text
              )
              """
        cursor.execute(sql)

        sql = """
              CREATE UNIQUE INDEX idx_services
              ON service_lut(folder, service, service_type)
              """
        cursor.execute(sql)

        sql = """
              CREATE TABLE service_logs (
                  date integer,
                  id integer,
                  hits integer,
                  errors integer,
                  nbytes integer,
                  export_mapdraws integer,
                  wms_mapdraws integer,
                  CONSTRAINT fk_service_lut_id
                      FOREIGN KEY (id)
                      REFERENCES service_lut(id)
                      ON DELETE CASCADE
              )
              """
        cursor.execute(sql)

        sql = """
              CREATE UNIQUE INDEX idx_services_logs_date
              ON service_logs(date, id)
              """
        cursor.execute(sql)

    def populate_service_lut(self):
        """
        Populate the services database with existing services.
        """
        if self.database.exists():
            self.logger.warning(f"Deleting {self.database}")
            self.database.unlink()

        self.conn = sqlite3.connect(self.database)
        df = self.retrieve_services()

        df.to_sql('service_lut', self.conn, index=False, if_exist='append')
        self.conn.commit()

    def retrieve_services(self):
        """
        Examine the project web site and retrieve a list of the services.
        """
        url = f"https://{self.project}.ncep.noaa.gov/arcgis/rest/services"
        params = {'f': 'json'}

        self.logger.info(f"Retrieving folders from {url}")

        r = requests.get(url, params=params)
        r.raise_for_status()

        j = r.json()
        folders = j['folders']
        records = []
        for folder in folders:

            # Retrieve the JSON metadata for the folder, which will contain
            # the list of all services.
            url = (
                f"https://{self.project}.ncep.noaa.gov"
                f"/arcgis/rest/services/{folder}"
            )

            self.logger.info(f"Retrieving services from {url}")

            r = requests.get(url, params=params)
            r.raise_for_status()

            # Save each service.
            j = r.json()
            for item in j['services']:
                folder, service = item['name'].split('/')
                service_type = item['type']
                records.append((folder, service, service_type))

        columns = ['folder', 'service', 'service_type']
        df = pd.DataFrame.from_records(records, columns=columns)

        self.logger.info(f"Retrieved {len(df)} services...")
        return df
