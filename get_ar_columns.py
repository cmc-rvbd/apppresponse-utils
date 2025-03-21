#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# get_ar_columns.py
#
# Copyright (c) 2025 Riverbed Technology, Inc.
#
# This software is licensed under the terms and conditions of the MIT License
# accompanying the software ("License").  This software is distributed "AS IS"
# as set forth in 
"""
Get the list of columns available from an AppResponse.

Usage/Example:

    python get_ar_columns.py <host> -u <username> -p <password> [--source packets|aggregates|alert_list]

Default source is “packets”

Output sample:

ID                                                Description                             Type       Metric  Key/Value
------------------------------------------------------------------------------------------------------------------------
apps.test_servers                                 Add it in the filter to test Auto       boolean    ---     Key
                                                  Discovered Servers
apps.test_servers_name                            Add it in the filter to test Auto       string     ---     Value
                                                  Discovered Servers
arp.class                                         ARP packet class code                   integer    ---     Key
arp.class_name                                    ARP packet class                        string     ---     Value
arp.hw.type                                       Hardware type code (e.g. 1)             integer    ---     Key
...
"""


from steelscript.appresponse.commands.columns import Command

if __name__ == '__main__':
    Command().run()

