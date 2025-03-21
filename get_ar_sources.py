#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# get_ar_sources.py
#
# Copyright (c) 2025 Riverbed Technology, Inc.
#
# This software is licensed under the terms and conditions of the MIT License
# accompanying the software ("License").  This software is distributed "AS IS"
# as set forth in 
"""
Get the list of sources available in the AppResponse.

Usage/Example:

    python get_ar_sources.py <host> -u <user name> -p <password>

Output sample:


Name        Groups                                                                  Filters Supported on Metric Columns  Granularities in Seconds     
------------------------------------------------------------------------------------------------------------------------------------------------------
packets     Packets                                                                 True                                 ---                          
aggregates  Application Stream Analysis, Web Transaction Analysis, DB Analysis,     True                                 60, 300, 3600, 21600, 86400  
            UC Analysis                                                                                                                               
alert_list  Alert Events                                                            True                                 ---                          

...
"""


from steelscript.appresponse.commands.sources import Command

if __name__ == '__main__':
    Command().run()

