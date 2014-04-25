import sys
import yaml
from distutils.core import setup

module_name = 'bitstreamer'
module_version = '1.0'
modules = 'bitstreamer', 'csviterator', 'devicelogger'

setup(name=module_name,
	  version=module_version,
	  py_modules=modules,
	  )

