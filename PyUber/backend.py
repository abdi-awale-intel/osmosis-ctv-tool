# -*- coding: utf-8 -*-

import importlib
import logging

from ._compat import supress

logger = logging.getLogger(__name__)


def get_backend(backend=None):
    if backend not in (None, 'clr', 'win32com', '__fake__'):
        raise NameError("Invalid backend specified")

    if backend is None:
        logger.info("Backend not specified")

    if backend in ('clr', None):
        with supress(ImportError):
            return importlib.import_module('PyUber._uCLR')

    if backend in ('win32com', None):
        with supress(ImportError):
            return importlib.import_module('PyUber._win32com')

    if backend == '__fake__':
        with supress(ImportError):
            return importlib.import_module('PyUber.__fake__')

    if backend == None:
        raise ImportError("No valid backend avaliable")
    else:
        raise ImportError("%s backend not avaliable" % backend)
