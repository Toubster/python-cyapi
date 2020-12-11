import sys
from cyapi.cyapi import CyAPI, debug_level
import csv
import argparse
from datetime import datetime
import json


__VERSION__ = '1.0'

##################################################################################
# Arguments
#
##################################################################################
def ParseArgs():

    regions = []
    regions_help = "Region the tenant is located: "
    for (k, v) in CyAPI.regions.items():
        regions.append(k)
        regions_help += " {} - {} ".format(k, v['fullname'])

    parser = argparse.ArgumentParser(description='Delete all multiple clients. See -F flag', add_help=True)
    parser.add_argument('-v', '--verbose', action="count", default=0, dest="debug_level", help='Show process location, comments and api responses')
    parser.add_argument('-tid', '--tid_val', help='Tenant Unique Identifier')
    parser.add_argument('-aid', '--app_id', help='Application Unique Identifier')
    parser.add_argument('-ase', '--app_secret', help='Application Secret')
    parser.add_argument('-c', '--creds_file', dest='creds', help='Path to JSON File with API info provided')
    parser.add_argument('-r', '--region', dest='region', help=regions_help, choices=regions, default='NA')
    parser.add_argument('-F','--Force', dest='delete', default=False, action='store_true', help='Delete all found Devices.')

    return parser

##################################################################################
# Tenant Integration
# Modify the keys to align with your tenant API
##################################################################################

commandline = ParseArgs()
args = commandline.parse_args()
debug_level += args.debug_level


class CylanceApi():
    def __init__(self, app_id, app_secret, creds, debug_level, delete, region, tid_val):
        self.app_id = app_id
        self.app_secret = app_secret
        self.creds = creds
        self.delete = delete
        self.region = region
        self.tid_val = tid_val

    def make_api_conn(self):
        if self.creds:
            with open(args.creds, 'rb') as file:
                creds = json.loads(file.read())

            if not creds.get('region'):
                creds['region'] = args.region

            API = CyAPI(**creds)
        elif self.tid_val and self.app_id and self.app_secret:
            API = CyAPI(tid=self.tid_val, app_id=self.app_id,
                        app_secret=self.app_secret, region=self.region)
        else:
            print("[-] Must provide valid token information")
            exit(-1)

        if not self.delete:
            print("[+] Listing all multiple clients in your environment")
        else:
            print("[+] Delete all multiple clients in your environment")

        print(API.baseURL)
        API.create_conn()
        return API

    def load_devices(self):
        API = self.make_api_conn()
        devices = API.get_devices()
        print("Successful: {}".format(devices.is_success))
        print(len(devices.data))
        devices.data.sort(key=lambda device: device["name"])
        return devices, API

    def find_duplicates(self):
        devices, API = self.load_devices()
        count = 0

        for indexI, device in enumerate(devices.data):
            if len(devices.data)-1 <= indexI:
                break
            if device["name"] == devices.data[indexI+1]["name"]:
                indexU = 1
                while device["name"] == devices.data[indexI + indexU]["name"]:

                    if devices.data[indexI]["state"] == "Online" or devices.data[indexI + indexU]["state"] != "Online" and devices.data[indexI]["date_offline"] > devices.data[indexI + indexU]["date_offline"]:
                        self.delete_client(API, devices.data[indexI + indexU]['id'], devices.data[indexI + indexU]['name'], devices.data[indexI + indexU]['date_offline'])
                        devices.data.pop(indexI + indexU)
                        count += 1
                        continue

                    elif devices.data[indexI + indexU]["state"] == "Online" or devices.data[indexI]["state"] != "Online" and devices.data[indexI]["date_offline"] < devices.data[indexI + indexU]["date_offline"]:
                        self.delete_client(API, devices.data[indexI]['id'], devices.data[indexI]['name'], devices.data[indexI]["date_offline"])
                        devices.data.pop(indexI)
                        count += 1
        print(f"There are {count} duplicates!")
        self.csvwriter(count, path="./cylance-dupplicate-count.txt")

    def delete_client(self, API, id, name, date):
        if self.delete:
            if type(id) != list:
                idarray = []
                idarray.append(id)
            else:
                idarray = id
            deldevice = API.delete_devices(idarray)
            if not deldevice.is_success:
                print(f"Error: Failed to delete client! Error-Message: {deldevice.errors} - Data: {deldevice.data}")
                self.delete = False
                sys.exit()
            else:
                #print(f"Deleting the client was successful! Error-Message: {deldevice.errors} - Data: {deldevice.data}") #DEBUG
                print(f"Delete: {id} Name: {name} Offline-Date: {date}")
                self.csvwriter(id, name, date, "./cylance-dupplicate")
        else:
            print(f"The client {name} with the ID {id} would get deleted! Offline-Date: {date}")

    def csvwriter(self, id=None, name=None, date=None, path=None):
        if id and name and path:
            if date is not None:
                try:
                    date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
                except ValueError:
                    date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
                date = datetime.strftime(date_obj, "%d.%m.%Y-%H:%M:%S")
            else:
                date = "None"
            with open(path + ".txt", 'a', newline='', encoding='utf-8') as file:
                csvwriter = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csvwriter.writerow([id, name, date])
            with open(path + "-for-msteams.txt", 'a') as file:
                file.write(str(id) + ";\\r" + name + ";\\r" + date + "\\r\\r\\n")
        elif id is not None and not name and not date and path:
            with open(path, 'w') as file:
                file.write(str(id))
        else:
            print("[-] Invalid file params at CSV Writer!")
            exit(-1)

CyDuplicates = CylanceApi(**vars(args))
CyDuplicates.find_duplicates()