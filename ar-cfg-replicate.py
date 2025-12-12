#!/usr/bin/env python3
"""
Export AppResponse General Application definitions to CSV and JSON.

Requirements:
  - Python 3.8+
  - pip install requests

Usage:
  python export_ar_general_apps.py --host https://ar11.example.com \
                                   --username admin --password ***** \
                                   --outfile general_apps

Outputs:
  - general_apps.json
  - general_apps.csv
"""

import argparse
import getpass
import json
import requests
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---- Configuration knobs -----------------------------------------------------
VERIFY_TLS = False  # Set to False only in lab scenarios

def fail (mesg):
    print ("failed: %s", mesg)
    sys.exit(1)
    
def appresponse_authenticate (hostname, username, password):
    
    credentials = {"username":username, "password":password}

    payload = {"generate_refresh_token":False, "user_credentials":credentials}
    headers = {"Content-Type":"application/json"}
    result = requests.post ('https://' + hostname + '/api/mgmt.aaa/2.0/token', data=json.dumps(payload), headers=headers, verify=False)

    if result.status_code not in [200, 201, 204]:
        print("Status code was %s" % result.status_code)
        print("Error: %s" % result.content)
        return None
    else:
        token_json = result.json ()
        access_token = token_json ["access_token"]
        return access_token

def appresponse_hostgroups_get (hostname, access_token):
    
    bearer = "Bearer " + access_token
    headers = {"Authorization":bearer}

    result = requests.get('https://' + hostname + '/api/npm.classification/3.2/hostgroups', headers=headers,
        verify=False)

    if result.status_code in [200, 201, 204]:
        result_json = result.json ()
    else:
        return None

    hostgroups = result_json ['items']

    return hostgroups

def appresponse_hostgroups_put (hostname, access_token, hostgroups):
    
    bearer = "Bearer " + access_token
    headers = {"Authorization":bearer}
    
    bulk_deleter = { 'delete_all': True }
    
    result = requests.post('https://' + hostname + '/api/npm.classification/3.2/hostgroups/bulk_delete', headers=headers,
        data=json.dumps(bulk_deleter), verify=False)   
         
    if not result.status_code in [200, 201, 204]:
        print ("Bulk Delete failed: " + result.content)
        return None
        
    # Place hostgroups in proper format
    payload = {}
    payload ['items'] = hostgroups
    
    result = requests.post('https://' + hostname + '/api/npm.classification/3.2/hostgroups/bulk_create', headers=headers,
        data=json.dumps(payload), verify=False)

    if result.status_code in [200, 201, 204]:
        return result
    else:
        print ("Bulk Create failed: " + result.content)
        return None
    
def main ():
    
    # Parse the arguments
    parser = argparse.ArgumentParser (description="Automated replication of AppResponse configuration items from a master to a slave")
    parser.add_argument('--master', help='the master AppResponse and source of the config data')
    parser.add_argument('--slave', help='the slave AppResponse and target for the config data')
    parser.add_argument('--musername')
    parser.add_argument('--susername')
    parser.add_argument('--mpassword')
    parser.add_argument('--spassword')
    parser.add_argument('--object', help="an object type: hgroups, apps, tags")
    args = parser.parse_args ()
    
    # Assuming there is a new update or the user has not requested to check for updates, validate the other arguments
    # and confirm that the script can authenticate to the AppResponse appliance
    if args.master == None:
        print ("Please specify a hostname for the master appliance using --master")
        return
    if args.slave == None:
        print ("Please specify a hostname for the slave (target) appliance using --slave")
        return
    if args.musername == None:
        print ("Please specify a username for the master appliance using --musername")
        return
    if args.mpassword == None:
        print ("Please provide the password for the master appliance for account %s" % args.musername)
        mpassword = getpass.getpass ()
    else:
        mpassword = args.mpassword
    if args.susername == None:
        print ("Please specify a username for the slave appliance using --susername")
        return
    if args.spassword == None:
        print ("Please provide the password for the slave appliance for account %s" % args.susername)
        spassword = getpass.getpass ()
    else:
        spassword = args.spassword
        
    access_token_master = appresponse_authenticate (args.master, args.musername, mpassword)
    if access_token_master == None:
        fail("failed to authenticate to the master appresponse: " + args.master)
        
    access_token_slave = appresponse_authenticate (args.slave, args.susername, spassword)
    if access_token_slave == None:
        fail("failed to authenticate to the slave appresponse: " + args.slave)

    # Pull existing Host Groups from appliance for comparison
    # The script allows filtering, so it will compare existing Host Groups to new definitions to provide details on changes
    master_hostgroups = appresponse_hostgroups_get (args.master, access_token_master)
    
    if master_hostgroups != None:
        update = appresponse_hostgroups_put (args.slave, access_token_slave, master_hostgroups)
        if update == None:
            print ("Update of slave system failed")
    else:
        print("Get of master system's host groups failed")
    
    # done

if __name__ == "__main__":
    main ()
    
# done

