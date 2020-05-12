# Standard library imports ...

# Third party library imports ...
from setuptools import setup, find_packages

cmdline = 'arcgis_apache_logs.commandline'
console_scripts = [
    f'ags-initialize={cmdline}:init_db',
    f'ags-parse-logs={cmdline}:parse_arcgis_apache_logs',
    f'ags-prune-database={cmdline}:prune_arcgis_apache_database',
    f'ags-produce-graphics={cmdline}:produce_arcgis_apache_graphics',
    f'ags-get-akamai-logs=akamai.commandline:get_akamai_logs',
],

kwargs = {
    'name': 'ArcGIS-Apache-Logs',
    'description': 'Tools for processing ArcGIS Apache Logs',
    'author': 'John Evans',
    'author_email': 'john.g.evans.ne@gmail.com',
    'url': 'https://github.com/quintusdias/gis-monitoring',
    'packages': find_packages(),
    'entry_points': {
        'console_scripts': console_scripts,
    },
    'license': 'MIT',
    'install_requires': ['pandas', 'lxml', 'setuptools'],
    'version': '0.0.7',
}

kwargs['classifiers'] = [
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: Implementation :: CPython",
    "License :: OSI Approved :: MIT License",
    "Development Status :: 5 - Production/Stable",
    "Operating System :: MacOS",
    "Operating System :: POSIX :: Linux",
    "Operating System :: Microsoft :: Windows :: Windows XP",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Information Technology",
    "Topic :: Software Development :: Libraries :: Python Modules"
]

setup(**kwargs)
