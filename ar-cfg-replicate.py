#!/usr/bin/env python3
"""
Summary and usage
This script will take config elements from a primary source (AppResponse) and replicate the configuration
to a slave system. Note that any local configuration for the specified element(s) on the slave system will
be overwritten and settings will not be merged.

The process will first get the current settings from the master appliance, then clear any settings for the
element on the slave system and then insert the cloned config from the master.

Usage:
  ar-cfg-replicate --master mname --slave sname --musername muser [--mpassword mpasswd] 
    --susername suser [--spassword spasswd] --object {hostgroups, applications, urls, webapps}

if either of the passwords is not provided, it will be prompted for on the CLI.
"""

import argparse
import getpass
import json
import requests
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -----------------------------------------------------------------------------

def fail (mesg):
    print ("failed: %s", mesg)
    sys.exit(1)

# -----------------------------------------------------------------------------
   
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

# -----------------------------------------------------------------------------
# A generic function that can "get" the definition for various object
# types, as per the API specs. Works for "hostgroups", "applications" (general apps)
# and "urls" (URL apps)
#
def appresponse_object_get (hostname, access_token, api_name, api_vers, obj_type):
    
    bearer = "Bearer " + access_token
    headers = {"Authorization":bearer}

    url = 'https://' + hostname + '/api/' + api_name + '/' + api_vers + '/'+ obj_type
    #print ('URL (1): ' + url)
    result = requests.get(url, headers=headers,
        verify=False)

    if result.status_code in [200, 201, 204]:
        result_json = result.json ()
    else:
        return None

    obj = result_json ['items']

    return obj

# -----------------------------------------------------------------------------
# A generic function that can "put" (redfine) the definition for various object
# types, as per the API specs. Works for "hostgroups", "applications" (general apps)
# and "urls" (URL apps)
#
def appresponse_object_put (hostname, access_token, api_name, api_vers, obj_type, obj, item_type):
    
    bearer = "Bearer " + access_token
    headers = {"Authorization":bearer}
    
    # -----------------------------------------------------------------------------
    # First clear out the existing defs - this is risky as a crash could leave us without any definitions!
    # Ideally, a backup should be taken and saved before we proceed.
    #
    bulk_deleter = { 'delete_all': True }
    
    url = 'https://' + hostname + '/api/' + api_name + '/' + api_vers + '/'+ obj_type + '/bulk_delete'
    #print ('URL (2): ' + url)
    result = requests.post(url, headers=headers, data=json.dumps(bulk_deleter), verify=False)   
         
    if not result.status_code in [200, 201, 204]:
        print ("Bulk Delete failed: " + result.text)
        return None
        
    # -----------------------------------------------------------------------------
    # Now install the cloned object defs using "merge" as the target config should be empty now

    # Place objects in proper format
    payload = {}
    payload [item_type] = obj
    
    url = 'https://' + hostname + '/api/' + api_name + '/' + api_vers + '/'+ obj_type + '/merge'
    #print ('URL (3): ' + url)
    result = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)

    if result.status_code in [200, 201, 204]:
        return result
    else:
        print ("Merge failed: " + result.text)
        return None

# -----------------------------------------------------------------------------
# A function to "put" (import) policy definitions
# INCOMPLETE - the import mechanism uses a one policy at a time method with system-specific IDs
# making it more complicated to do. Save for later...
#
def appresponse_policies_put (hostname, access_token, api_name, api_vers, obj):
    
    bearer = "Bearer " + access_token
    headers = {"Authorization":bearer}
    
    # -----------------------------------------------------------------------------
    # Install the cloned policy defs

    # Place objects in proper format
    payload = {}
    payload ['items'] = obj
    
    url = 'https://' + hostname + '/api/' + api_name + '/' + api_vers + '/policies'
    #print ('URL (4): ' + url)
    result = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)

    if result.status_code in [200, 201, 204]:
        return result
    else:
        print ("POST failed: " + result.text)
        return None
   
# -----------------------------------------------------------------------------
# MAIN
#
def main ():
    
    # -----------------------------------------------------------------------------
    # Parse the arguments
    #
    parser = argparse.ArgumentParser (description="Automated replication of AppResponse configuration items from a master to a slave")
    parser.add_argument('--master', help='the master AppResponse and source of the config data')
    parser.add_argument('--slave', help='the slave AppResponse and target for the config data')
    parser.add_argument('--musername')
    parser.add_argument('--susername')
    parser.add_argument('--mpassword')
    parser.add_argument('--spassword')
    parser.add_argument('--object', help="an object type: hostgroups, applications (General apps), urls (URL-defined apps)")
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
    if args.object == None:
        print ("Please specify which config element type should be replicated (hostgroups, applications, urls)")
        return
    
    # -----------------------------------------------------------------------------
    # Authenticate to the target systems
    #
    access_token_master = appresponse_authenticate (args.master, args.musername, mpassword)
    if access_token_master == None:
        fail("failed to authenticate to the master appresponse: " + args.master)
        
    access_token_slave = appresponse_authenticate (args.slave, args.susername, spassword)
    if access_token_slave == None:
        fail("failed to authenticate to the slave appresponse: " + args.slave)


    if args.object == "hostgroups" or args.object == "applications" or args.object == "urls":
        # -----------------------------------------------------------------------------
        # Pull existing definitions from master appliance for cloning to slave appliance
        # 
        api_name = 'npm.classification'
        api_vers = '3.2'
        master_obj = appresponse_object_get (args.master, access_token_master, api_name, api_vers, args.object)
    
        if master_obj != None:
            update = appresponse_object_put (args.slave, access_token_slave, api_name, api_vers, args.object, master_obj, 'items')
            if update == None:
                print ("Update of slave system failed")
        else:
            print("Get of master system's " + args.object + " definitions failed")
    elif args.object == "webapps":
        # -----------------------------------------------------------------------------
        # Pull existing webapp definitions from master appliance for cloning to slave appliance
        # 
        api_name = 'npm.wta_config'
        api_vers = '1.0'
        obj_type = 'wta_webapps'
        master_obj = appresponse_object_get (args.master, access_token_master, api_name, api_vers, obj_type)
    
        if master_obj != None:
            update = appresponse_object_put (args.slave, access_token_slave, api_name, api_vers, obj_type, master_obj, 'rules')
            if update == None:
                print ("Update of slave system's webapps failed")
        else:
            print("Get of master system's webapp failed")        
#    elif args.object == "policies":
#        # -----------------------------------------------------------------------------
#        # Pull existing policy definitions from master appliance for cloning to slave appliance
#        # Unfinished - Does not work as easy as with other definitions as polcies have a complex structure with
#        # system-specific dependencies and a one-policy-at-a-time import API (no bulk merging)
#        # 
#        api_name = 'npm.policies.export'
#        api_vers = '1.0'
#        obj_type = 'policies'
#        master_obj = appresponse_object_get (args.master, access_token_master, api_name, api_vers, obj_type)
#    
#        if master_obj != None:
#            update = appresponse_policies_put (args.slave, access_token_slave, api_name, api_vers, master_obj)
#            if update == None:
#                print ("Update of slave system's policies failed")
#        else:
#            print("Get of master system's policies failed")        
    else:
        fail ("Unsupported object type specified: " + args.object)
        return
        
    # done

if __name__ == "__main__":
    main ()
    
# done

