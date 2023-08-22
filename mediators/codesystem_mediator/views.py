"""
Settings for openhim Codesystem mediator developed in Django.

The python-based Codesystem mediator implements python-utils
from https://github.com/de-laz/openhim-mediator-utils-py.git.

For more information on this file, contact the Python developers
Idiono-mfon:idionomfonetim@mail.com
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

from helpers.helpers import requests, postToSuresalamaChannel, getPortPart, getPaginatedRecords, initAuth


# Add this temprarily for testing purposes
# Will be taken out upon configuration of SSL certificate
# from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
# requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

@api_view(['GET', 'POST'])
def getCodesystem(request):
    try:
        print(" Executing getCodesystem ........")

        # get url params
        page_offset = request.GET.get("page-offset", "")

        print("page_offset")
        print(page_offset)

        auth_data = initAuth()

        # Standard Base64 Encoding
        url = auth_data["config"]["data"]["openimis_url"]+getPortPart(
            auth_data["config"]["data"]["openimis_port"])+"/api/api_fhir_r4/CodeSystem"

        # retur`n url

        if page_offset != "":
            url = url+"?page-offset="+page_offset
        # Query the upstream server via openHIM mediator port 8000
        # Caution: To secure the endpoint with SSL certificate,FQDN is required
        if request.method == 'GET':
            querystring = {"": ""}
            payload = ""
            headers = {'Authorization': auth_data["auth"]}
            
            codesystems = [
                'patient-education-level',
                'patient-profession',
                'patient-identification-type',
                'patient-contact-relationship',
                'group-type',
                'group-confirmation-type',
                'organization-hf-legal-form',
                'organization-hf-level',
                'diagnosis',
                'organization-ph-legal-form',
                'organization-ph-activity'
            ]
            
            codesystemEntry = []
            
            codesystemBundle = {
                "resourceType" : "Bundle",
                "type":"transaction",
                "total": len(codesystems),
                "entry":[]
            }
            
            for system in codesystems:
                
                new_url = ""
                
                new_url = url +"/"+system
                
                response = requests.request(
                "GET", new_url, data=payload, headers=headers, params=querystring, verify=False)
                
                datac = json.loads(response.text)
                
                if system == 'organization-ph-legal-form':
                    datac["id"] = system
                
                name= datac["name"]
                                
                entry = {
                    "fullUrl": new_url,
                    "resource": datac,
                    "request": {"method": "PUT", "url": f"CodeSystem?name={name}"}
                }
                
                codesystemEntry.append(entry)
                
                
            codesystemBundle["entry"] = codesystemEntry
            
             # # Post to Suresalama channel
            open_him_url = auth_data["config"]["data"]["openhim_url"]+':' + \
            str(auth_data["config"]["data"]["openhim_port"])

            channelUrl = open_him_url + '/suresalama/resource'
            
            postToSuresalamaChannel(channelUrl, json.dumps(codesystemBundle))
            
            return Response(codesystemBundle)

            # return response.json()
        elif request.method == 'POST':

            querystring = {"": ""}
            data = json.dumps(request.data)
            payload = data
            headers = {
                'Content-Type': "application/json",
                'Authorization': auth_data["auth"]
            }
            response = requests.request(
                "POST", url, data=payload, headers=headers, params=querystring)
            datac = json.loads(response.text)
            return Response(datac)

    except Exception as e:
        print('%s' % type(e))
        return Response({"status": "errror", "message": str(e)})
