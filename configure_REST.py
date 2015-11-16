#!/usr/bin/python
"""
Configure controller through script
"""

import json, urllib
import requests
from optparse import OptionParser

# Parameters from shell
parser = OptionParser()
parser.add_option("","--idle",type="int",default=5)
parser.add_option("","--hard",type="int",default=0)
(options, args) = parser.parse_args()
print options


url = "http://localhost:8080/wm/core/controller/configure/json"
payload = {'idle_timeout': options.idle,'hard_timeout': options.hard}
print(requests.get(url, data=payload))

