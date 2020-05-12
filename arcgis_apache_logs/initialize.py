# standard library imports
import datetime as dt
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

    def prune_database(self):

        if dt.date.today().weekday() != 0:
            # If it's not Monday, do nothing.
            return

        self.drop_tables()

        self.initialize_ip_address_tables()
        self.initialize_referer_tables()
        self.initialize_user_agent_tables()

    def drop_tables():

        self.drop_ip_address_tables()
        self.drop_referer_tables()
        self.drop_user_agent_tables()

    def drop_referer_tables(self):

        cursor = self.conn.cursor()

        sql = """
              DROP INDEX idx_referer_logs_date
              """
        self.logger.info(sql)
        cursor.execute(sql)

        sql = """
              DROP TABLE referer_logs
              """
        self.logger.info(sql)
        cursor.execute(sql)

        sql = """
              DROP INDEX idx_referer
              """
        self.logger.info(sql)
        cursor.execute(sql)

        sql = """
              DROP TABLE referer_lut
              """
        self.logger.info(sql)
        cursor.execute(sql)
        self.conn.commit()

    def drop_user_agent_tables(self):

        cursor = self.conn.cursor()

        sql = """
              DROP INDEX idx_user_agent_logs_date
              """
        self.logger.info(sql)
        cursor.execute(sql)

        sql = """
              DROP TABLE user_agent_logs
              """
        self.logger.info(sql)
        cursor.execute(sql)

        sql = """
              DROP INDEX idx_user_agent
              """
        self.logger.info(sql)
        cursor.execute(sql)

        sql = """
              DROP TABLE known_user_agents
              """
        self.logger.info(sql)
        cursor.execute(sql)

        self.conn.commit()

    def drop_ip_address_tables(self):

        sql = """
              DROP INDEX idx_ip_address_logs_date
              """
        self.logger.info(sql)
        cursor.execute(sql)

        sql = """
              DROP TABLE ip_address_logs
              """
        self.logger.info(sql)
        cursor.execute(sql)

        sql = """
              DROP INDEX idx_ip_address
              """
        self.logger.info(sql)
        cursor.execute(sql)

        sql = """
              DROP TABLE ip_address_lut
              """
        self.logger.info(sql)
        cursor.execute(sql)

        self.conn.commit()

    def initialize(self):

        if self.database.exists():
            self.logger.warning(f"Deleting {self.database}")
            self.database.unlink()

        self.conn = sqlite3.connect(self.database)

        self.initialize_service_tables()
        self.populate_service_lut()

        self.initialize_ip_address_tables()
        self.initialize_referer_tables()
        self.initialize_user_agent_tables()

    def initialize_user_agent_tables(self):
        """
        Verify that all the database tables are setup properly for managing
        the user_agents.
        """

        cursor = self.conn.cursor()

        sql = """
              CREATE TABLE user_agent_lut (
                  id integer PRIMARY KEY,
                  name text
              )
              """
        cursor.execute(sql)
        sql = """
              CREATE UNIQUE INDEX idx_user_agent
              ON user_agent_lut(name)
              """
        cursor.execute(sql)

        sql = """
              CREATE TABLE user_agent_logs (
                  date timestamp,
                  id integer,
                  hits integer,
                  errors integer,
                  nbytes integer,
                  CONSTRAINT fk_user_agents_id
                      FOREIGN KEY (id)
                      REFERENCES user_agent_lut(id)
                      ON DELETE CASCADE
              )
              """
        cursor.execute(sql)

        sql = """
              CREATE UNIQUE INDEX idx_user_agent_logs_date
              ON user_agent_logs(date, id)
                  """
        cursor.execute(sql)

    def initialize_ip_address_tables(self):
        """
        Verify that all the database tables are setup properly for managing
        IP addresses.
        """
        cursor = self.conn.cursor()
        # Create the known IP addresses table.  The IP addresses must be
        # unique.
        sql = """
              CREATE TABLE ip_address_lut (
                  id integer PRIMARY KEY,
                  ip_address text,
                  name text
              )
              """
        cursor.execute(sql)
        sql = """
              CREATE UNIQUE INDEX idx_ip_address
              ON ip_address_lut(ip_address)
              """
        cursor.execute(sql)

        # Create the IP address logs table.
        sql = """
              CREATE TABLE ip_address_logs (
                  date timestamp,
                  id integer,
                  hits integer,
                  errors integer,
                  nbytes integer,
                  CONSTRAINT fk_known_ip_address_id
                      FOREIGN KEY (id)
                      REFERENCES ip_address_lut(id)
                      ON DELETE CASCADE
              )
              """
        cursor.execute(sql)

        # Unfortunately the index cannot be unique here.
        sql = """
              CREATE INDEX idx_ip_address_logs_date
              ON ip_address_logs(date)
              """
        cursor.execute(sql)

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

        sql = """
              CREATE TABLE referer_logs (
                  date timestamp,
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

    def initialize_service_tables(self):

        cursor = self.conn.cursor()

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
                  date timestamp,
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
        df = self.retrieve_services()
        df.to_sql('service_lut', self.conn, index=False, if_exists='append')
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
