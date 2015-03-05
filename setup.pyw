# -*- coding: utf-8 -*-

from distutils.core import setup
import py2exe

from PyQt4 import QtCore, QtGui
import numpy

option = {
    "compressed": 1,
    "optimize": 2,
    "bundle_files": 1,
    "includes": [
        "sip",
        "PyQt4.QtCore",
        "PyQt4.QtGui",
        "scipy.sparse.csgraph._validation",
    ],
}

setup(
    options = {
        "py2exe": option,
    },
    windows = [
        {"script": "main.py"},
    ],
    zipfile=None
)