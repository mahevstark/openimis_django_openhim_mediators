"""
Settings for openhim Patient mediator developed in Django.

The python-based Patient mediator implements python-utils
from https://github.com/de-laz/openhim-mediator-utils-py.git.

For more information on this file, contact the Python developers
Stephen Mburu:ahoazure@gmail.com & Peter Kaniu:peterkaniu254@gmail.com

"""

from django.shortcuts import render

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import http.client

import json


from urllib.parse import unquote
# import requests
from datetime import datetime
from openhim_mediator_utils.main import Main
from time import sleep

from overview.models import configs
from overview.views import configview
import http.client
import base64

from helpers.helpers import requests, fetchUniqueResource, submitPaginatedLocationResourcesToChannelCallback, getPortPart, getPaginatedRecords, initAuth


# Add this temprarily for testing purposes
# Will be taken out upon configuration of SSL certificate
# from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
# requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

@api_view(['GET', 'POST'])
def getLocation(request):
    try:
        print(" Executing getLocation ........")

        # get url params
        page_offset = request.GET.get("page-offset", "")

        print("page_offset")
        print(page_offset)

        auth_data = initAuth()

        # Standard Base64 Encoding
        url = auth_data["config"]["data"]["openimis_url"]+getPortPart(
            auth_data["config"]["data"]["openimis_port"])+"/api/api_fhir_r4/Location"

        # retur`n url

        if page_offset != "":
            url = url+"?page-offset="+page_offset
        # Query the upstream server via openHIM mediator port 8000
        # Caution: To secure the endpoint with SSL certificate,FQDN is required
        if request.method == 'GET':
            querystring = {"": ""}
            payload = ""
            headers = {'Authorization': auth_data["auth"]}
            print(url)
            print(headers)
            response = requests.request(
                "GET", url, data=payload, headers=headers, params=querystring, verify=False)

            datac = json.loads(response.text)

            getPaginatedRecords(datac, url, payload, headers,
                                submitPaginatedLocationResourcesToChannelCallback)

            print(response.status_code)

            return Response(data)

            # return response.json()
        elif request.method == 'POST':
            
            reqBody = request.data
            
            resource_type = reqBody["resourceType"]
            
            resource_id = reqBody["id"]
            
            resource = fetchUniqueResource(resource_type, resource_id)
            
            headers = {
                'Content-Type': "application/json",
                'Authorization': auth_data["auth"]
            }
            
            querystring = {"": ""}
            
            payload = json.dumps(reqBody)

            if (resource and resource["resourceType"] == resource_type):
                
                print("Update Location resource")

                # Update Resource
                
                put_url = auth_data["config"]["data"]["openimis_url"]+getPortPart(
                auth_data["config"]["data"]["openimis_port"])+"/api/api_fhir_r4/Location/"+str(resource_id)+"/"
                
                print(put_url)
                
                response = requests.request(
                "PUT", put_url, data=payload, headers=headers, params=querystring, verify=False)
                
                datac = json.loads(response.text)
                
                return Response(datac)
            
            url = url + "/"
            print("Create Location resource")
            

            querystring = {"": ""}
            data = json.dumps(request.data)
            payload = data
            headers = {
                'Content-Type': "application/json",
                'Authorization': auth_data["auth"]
            }
            response = requests.request(
                "POST", url, data=payload, headers=headers, params=querystring, verify=False)
            datac = json.loads(response.text)
            return Response(datac)

    except Exception as e:
        print('%s' % type(e))

        # return Response({"status": "errror", "message": str(e)})


def registerLocationMediator():
    result = configview()
    configurations = result.__dict__

    API_URL = 'https://' + \
        configurations["data"]["openhim_url"]+':' + \
        str(configurations["data"]["openhim_port"])
    USERNAME = configurations["data"]["openhim_user"]
    PASSWORD = configurations["data"]["openhim_passkey"]

    options = {
        'verify_cert': False,
        'apiURL': API_URL,
        'username': USERNAME,
        'password': PASSWORD,
        'force_config': False,
        'interval': 10,
    }

    conf = {
        "urn": "urn:mediator:python_fhir_r4_Location_mediator",
        "version": "1.0.1",
        "name": "Python Fhir R4 Location Mediator",
        "description": "Python Fhir R4 Location Mediator",

        "defaultChannelConfig": [
            {
                "name": "Python Fhir R4 Location Mediator",
                "urlPattern": "^/api/api_fhir_r4/Location$",
                "routes": [
                        {
                            "name": "Python Fhir R4 Location Mediator Route",
                            "host": configurations["data"]["mediator_url"],
                            "path": "/api/api_fhir_r4/Location",
                                    "port": configurations["data"]["mediator_port"],
                                    "primary": True,
                                    "type": "http"
                        }
                ],
                "allow": ["admin"],
                "methods": ["GET", "POST"],
                "type": "http"
            }
        ],

        "endpoints": [
            {
                "name": "Bootstrap Scaffold Mediator Endpoint",
                "host": configurations["data"]["mediator_url"],
                "path": "/api/api_fhir_r4/Location",
                "port": configurations["data"]["mediator_port"],
                "primary": True,
                "type": "http"
            }
        ]
    }

    openhim_mediator_utils = Main(
        options=options,
        conf=conf
    )

    openhim_mediator_utils.register_mediator()
    checkHeartbeat(openhim_mediator_utils)


# Morning the health status of the client on the console
def checkHeartbeat(openhim_mediator_utils):
    openhim_mediator_utils.activate_heartbeat()

#  #boizinlife
