"""
Settings for openhim Contract mediator developed in Django.

The python-based Contract mediator implements python-utils 
from https://github.com/de-laz/openhim-mediator-utils-py.git.

For more information on this file, contact the Python developers
Stephen Mburu:ahoazure@gmail.com & Peter Kaniu:peterkaniu254@gmail.com

"""

from helpers.helpers import getPortPart, submitPaginatedResourcesToChannelCallback, getPaginatedRecords
from django.shortcuts import render

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import http.client

import json


import requests
from datetime import datetime
from openhim_mediator_utils.main import Main
from time import sleep

from overview.models import configs
from overview.views import configview
import http.client
import base64
from helpers.helpers import requests, getPortPart, getPaginatedRecords, initAuth


# Add this temprarily for testing purposes
# Will be taken out upon configuration of SSL certificate
# from urllib3.exceptions import InsecureRequestWarning

# requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


@api_view(['GET', 'POST'])
def getMedication(request):

    print("========Executing getMedication method========")

    # result = configview()
    # configurations = result.__dict__
    # # username:password-openhimclient:openhimclientPasskey
    # authvars = configurations["data"]["openimis_user"] + \
    #     ":"+configurations["data"]["openimis_passkey"]
    # # Standard Base64 Encoding
    # encodedBytes = base64.b64encode(authvars.encode("utf-8"))
    # encodedStr = str(encodedBytes, "utf-8")
    # auth_openimis = "Basic " + encodedStr
    
    auth_data = initAuth()
    
    page_offset = request.GET.get("page-offset", "")


    url = auth_data["data"]["openimis_url"]+getPortPart(
        auth_data["data"]["openimis_port"])+"/api/api_fhir_r4/Medication"

    # url = configurations["data"]["openimis_url"]+":" + \
    #     str(configurations["data"]["openimis_port"]) + \
    #     "/api/api_fhir_r4/Contract"
    # Query the upstream server via openHIM mediator port 8000
    # Caution: To secure the endpoint with SSL certificate,FQDN is required
    
    if page_offset != "":
        url = url+"?page-offset="+page_offset
    
    if request.method == 'GET':
        querystring = {"": ""}
        payload = ""
        headers = {'Authorization': auth_data["auth"]}

        print(f'Medication headers {headers}')
        response = requests.request(
            "GET", url, data=payload, headers=headers, params=querystring, verify=False)
        datac = json.loads(response.text)
        
        # Fetch all paginated records
        getPaginatedRecords(datac, url, payload, headers,
                            submitPaginatedResourcesToChannelCallback)
        print(response.status_code)

        return Response(datac)

    elif request.method == 'POST':
        print("Create Medication resource")

        url = url + "/"
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

    elif request.method == 'PUT':
        resource_id = request.data['id']
        
        if not resource_id:
            raise Exception("No resource Id Found")

        url = url + f"/{resource_id}/"
        
        print(url)
        
        print("Update Medication resource")
        
        querystring = {"": ""}
        data = json.dumps(request.data)
        payload = data
        headers = {
            'Content-Type': "application/json",
            'Authorization': auth_data['auth']
        }
        response = requests.request(
            "PUT", url, data=payload, headers=headers, params=querystring, verify=False)
        
        
        print(response)
        
        datac = json.loads(response.text)
        
        return Response(datac)


def registerMedicationMediator():
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
        "urn": "urn:mediator:python_fhir_r4_Medication_mediator",
        "version": "1.0.1",
        "name": "Python Fhir R4 Medication Mediator",
        "description": "Python Fhir R4 Medication Mediator",

        "defaultChannelConfig": [
            {
                "name": "Python Fhir R4 Medication Mediator",
                "urlPattern": "^/api/api_fhir_r4/Medication$",
                "routes": [
                        {
                            "name": "Python Fhir R4 Medication Mediator Route",
                            "host": configurations["data"]["mediator_url"],
                            "path": "/api/api_fhir_r4/Medication",
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
                "path": "/api/api_fhir_r4/Medication",
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
