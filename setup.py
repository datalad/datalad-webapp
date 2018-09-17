#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages

setup(
    # basic project properties can be set arbitrarily
    name="datalad_webapp",
    author="The DataLad Team and Contributors",
    author_email="team@datalad.org",
    version='0.1',
    description="DataLad extension for exposing commands via a web request API",
    packages=[pkg for pkg in find_packages('.') if pkg.startswith('datalad')],
    # datalad command suite specs from here
    install_requires=[
        'datalad',
        'flask',
        'flask-restful',
        'pytest',
        'pytest-cov',
    ],
    entry_points = {
        'datalad.extensions': [
            'webapp=datalad_webapp:command_suite',
        ],
        # 'datalad.webapps' is THE entrypoint inspected by the datalad webapp command
        'datalad.webapp.resources': [
            # the label in front of '=' is the REST endpoint name
            # the entrypoint can point to any symbol of any name
            'auth=datalad_webapp.resources.auth:AuthenticationResource',
            'file=datalad_webapp.resources.file:FileResource',
            'subdataset=datalad_webapp.resources.subdataset:SubdatasetResource',
        ]
    },
)
