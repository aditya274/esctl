#!/usr/bin/env python

from setuptools import setup, find_packages

PROJECT = "esctl"
VERSION = "1.0"

try:
    long_description = open("README.rst", "rt").read()
except IOError:
    long_description = ""

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name=PROJECT,
    version=VERSION,
    description="Esctl is CLI for Elasticsearch",
    long_description=long_description,
    author="Jérôme Pin",
    maintainer="Jérôme Pin",
    url="https://github.com/jeromepin/esctl",
    keywords=["elasticsearch", "es", "cli"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Utilities",
        "Topic :: System :: Shells",
        "Topic :: Systems Administration",
    ],
    platforms=["Any"],
    scripts=[],
    provides=[],
    install_requires=requirements,
    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": ["esctl = esctl.main:main"],
        "esctl": [
            "cat allocation = esctl.cmd.cat:CatAllocation",
            "cluster allocation explain = esctl.cmd.cluster:ClusterAllocationExplain",
            "cluster health = esctl.cmd.cluster:ClusterHealth",
            "cluster routing allocation enable = esctl.cmd.cluster:ClusterRoutingAllocationEnable",
            "cluster stats = esctl.cmd.cluster:ClusterStats",
            "config context list = esctl.cmd.config:ConfigContextList",
            "index close = esctl.cmd.index:IndexClose",
            "index create = esctl.cmd.index:IndexCreate",
            "index delete = esctl.cmd.index:IndexDelete",
            "index list = esctl.cmd.index:IndexList",
            "index open = esctl.cmd.index:IndexOpen",
            "logging get = esctl.cmd.logging:LoggingGet",
            "logging reset = esctl.cmd.logging:LoggingReset",
            "logging set = esctl.cmd.logging:LoggingSet",
            "node hot-threads = esctl.cmd.node:NodeHotThreads",
            "node list = esctl.cmd.node:NodeList",
        ],
    },
    zip_safe=False,
)
