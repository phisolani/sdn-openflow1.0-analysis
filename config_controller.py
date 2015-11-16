#!/usr/bin/python
"""
Create a new xml file for Floodlight-Default-Conf.launch
"""

import sys

idle_time = sys.argv[1]

floodlight_config = open('Floodlight-Default-Conf.launch', "w")
floodlight_config.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' \
                      + '<launchConfiguration type="org.eclipse.jdt.launching.localJavaApplication">\n' \
                      + '<listAttribute key="org.eclipse.debug.core.MAPPED_RESOURCE_PATHS">\n' \
                      + '<listEntry value="/floodlight/src/main/java/net/floodlightcontroller/core/Main.java"/>\n' \
                      + '</listAttribute>\n' \
                      + '<listAttribute key="org.eclipse.debug.core.MAPPED_RESOURCE_TYPES">\n' \
                      + '<listEntry value="1"/>\n' \
                      + '</listAttribute>\n' \
                      + '<stringAttribute key="org.eclipse.jdt.launching.MAIN_TYPE" value="net.floodlightcontroller.core.Main"/>\n' \
                      + '<stringAttribute key="org.eclipse.jdt.launching.PROJECT_ATTR" value="floodlight"/>\n' \
                      + '<stringAttribute key="org.eclipse.jdt.launching.VM_ARGUMENTS" value="-ea"/>\n' \
                      + '<idleTime value="' \
                      + str(idle_time) \
                      + '"/>\n' \
                      + '</launchConfiguration>')
floodlight_config.close()
