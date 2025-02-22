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

from helpers.helpers import requests, initAuth, fetchUniqueResource, formatTransactionPayload, postToSuresalamaChannel, getPortPart, pingChannel, getPaginatedRecords, findOrCreateOpenIMISSubscriptionResource

from constants.resource import FhirResource

# Add this temporarily for testing purposes
# Will be taken out upon configuration of SSL certificate
# from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
# requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


@api_view(['GET', 'POST', 'PUT'])
def getPatient(request):
    try:
        print(" Executing getPatient ........")

        # get url params
        page_offset = request.GET.get("page-offset", "")

        org_id = request.GET.get("orgId", "")

        print("page_offset")
        print(page_offset)

        result = configview()
        configurations = result.__dict__
        # username:password-openhimclient:openhimclientPasskey
        authvars = configurations["data"]["openimis_user"] + \
            ":"+configurations["data"]["openimis_passkey"]
        # Standard Base64 Encoding
        encodedBytes = base64.b64encode(authvars.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")
        auth_openimis = "Basic " + encodedStr

        # Standard Base64 Encoding
        url = configurations["data"]["openimis_url"]+getPortPart(
            configurations["data"]["openimis_port"])+"/api/api_fhir_r4/Patient"

        # Verify existience of Subscription and create if it doesn't exists;

        # result = findOrCreateOpenIMISSubscriptionResource(
        #     auth_openimis, FhirResource.Patient)

        # return Response({"data": result})
        
        error_message = ""

        if page_offset != "":
            url = url+"?page-offset="+page_offset
        # Query the upstream server via openHIM mediator port 8000
        # Caution: To secure the endpoint with SSL certificate,FQDN is required
        if request.method == 'GET':
            print(" yes I was here")
            querystring = {"": ""}
            payload = ""

            headers = {
                'Content-Type': "application/json",
                'Authorization': auth_openimis
            }
            print(url)
            print(headers)
            response = requests.request(
                "GET", url, data=payload, headers=headers, params=querystring, verify=False)

            datac = json.loads(response.text)

            # Pass any subsequent data updates as callback parameters

            # Here we intend update to patient records retrieved to reflect organization Id

            def submitPaginatedResourcesToChannelCallback(paginatedData):

                print(f'current data is this: {paginatedData}')

                def update_patient_org(
                    data, org): return data['resource'].update(org)

                # Managing organization to be updated

                org = {"managingOrganization": {
                    "reference": "Organization/"+str(org_id)}}

                # Format and serialize data to JSON string

                channelPayload = formatTransactionPayload(
                    paginatedData, update_patient_org, org)

                # # Post to Suresalama channel
                open_him_url = configurations["data"]["openhim_url"]+':' + \
                    str(configurations["data"]["openhim_port"])

                channelUrl = open_him_url + '/suresalama/resource'

                print(response.status_code)

                return postToSuresalamaChannel(channelUrl,  channelPayload)

            getPaginatedRecords(datac, url, payload, headers,
                                submitPaginatedResourcesToChannelCallback)

            return Response(datac)

            # return response.json()
        elif request.method == 'POST' or request.method == 'PUT':
            
            reqBody = request.data
            
            resource_type = reqBody["resourceType"]
            
            resource_id = reqBody["id"]
            
            resource = fetchUniqueResource(resource_type, resource_id)
            
            headers = {
                'Content-Type': "application/json",
                'Authorization': auth_openimis
            }
            
            querystring = {"": ""}
            
            payload = json.dumps(reqBody)

            if (resource and resource["resourceType"] == resource_type):
                
                print("Update Patient resource")

                # Update Resource
                
                put_url = configurations["data"]["openimis_url"]+getPortPart(
                configurations["data"]["openimis_port"])+"/api/api_fhir_r4/Patient/"+str(resource_id)+"/"
                
                print(put_url)
                
                response = requests.request(
                "PUT", put_url, data=payload, headers=headers, params=querystring, verify=False)
                
                datac = json.loads(response.text)
                
                # @Todo: Handle error message properly latter
                
                return Response(datac)
                
            # Create Patient resource
            
            print("Create Patient resource")

            url = url + "/"
            
            print(url)
            
            response = requests.request(
                "POST", url, data=payload, headers=headers, params=querystring, verify=False)
            
            datac = json.loads(response.text)
            
            # @Todo: Handle error message properly latter
            
            return Response(datac)

    except Exception as e:
        print('%s' % type(e))
   
        # return Response({"status": "errror", "message": str(e)})


@api_view(['POST'])
def savePreference(request):
    try:
        print(" SavePreference executing ........")
        # get url params
        page_offset = request.GET.get("page-offset", "")
        # resources = request.POST.get("resources")
        result = configview()
        configurations = result.__dict__
        # username:password-openhimclient:openhimclientPasskey
        # authvars = configurations["data"]["openimis_user"] + \
        #     ":"+configurations["data"]["openimis_passkey"]

        body = request.body.decode('utf-8')

        payload = json.loads(body)

        resources = payload['resources']

        # OpenHIM CORE URL and PORT for accessing channel
        # Add channel authenication latter
        open_him_url = configurations["data"]["openhim_url"]+':' + \
            str(configurations["data"]["openhim_port"])

        print(resources)
        
        if 'codesystem' in resources:
            print('=====About to fetch and migrate codesystem resource=====')

            url = open_him_url+'/openimis/codesystem'
            # Send request to OpenHIM channel
            pingChannel(url, 'Codesystem')
            
        if 'medication' in resources:
            print('=====About to fetch and migrate medication resource=====')

            url = open_him_url+'/openimis/medication'
            # Send request to OpenHIM channel
            pingChannel(url, 'Medication')
        
        if 'activityDefinition' in resources:
            print('=====About to fetch and migrate medical service (ActivityDefinition) resources=====')

            url = open_him_url+'/openimis/activityDefinition'
            # Send request to OpenHIM channel
            pingChannel(url, 'ActivityDefinition')

        if 'insuranceProduct' in resources:
            print('=====About to fetch and migrate insurance products resource=====')

            url = open_him_url+'/openimis/product'
            # Send request to OpenHIM channel
            pingChannel(url, 'Insurance Product')

        if 'organization' in resources:
            print('=====About to fetch and migrate organization resource=====')

            url = open_him_url+'/openimis/organization'
            # Send request to OpenHIM channel
            pingChannel(url, 'Organization')

        if 'practitioner' in resources:
            print('=====About to fetch and migrate practitioner resource=====')

            url = open_him_url+'/openimis/practitioner'
            # Send request to OpenHIM channel
            pingChannel(url, 'Practitioner')
            
        if 'insuree' in resources:
            print('=====About to fetch and migrate insuree resource=====')

            querystring = {"orgId": payload["orgId"] or ""}

            url = open_him_url+'/openimis/insuree'
            # Send request to OpenHIM channel
            pingChannel(url, 'Insuree', querystring)

        if 'group' in resources:
            print('=====About to fetch and migrate group resource=====')

            url = open_him_url+'/openimis/group'
            # Send request to OpenHIM channel
            pingChannel(url, 'Group')

        if 'policy' in resources:
            print('=====About to fetch and migrate policy resource=====')

            url = open_him_url+'/openimis/policy'
            # Send request to OpenHIM channel
            pingChannel(url, 'Policy')

        if 'location' in resources:
            print('=====About to fetch and migrate locationn resource=====')

            url = open_him_url+'/openimis/location'
            # Send request to OpenHIM channel
            pingChannel(url, 'Location')

        if 'claim' in resources:
            print('=====About to fetch and migrate claim resource=====')

            url = open_him_url+'/openimis/claim'
            # Send request to OpenHIM channel
            pingChannel(url, 'Claim')

        if 'claimResponse' in resources:
            print('=====About to fetch and migrate claimResponse resource=====')

            url = open_him_url+'/openimis/claimResponse'
            # Send request to OpenHIM channel
            pingChannel(url, 'ClaimResponse')

        if 'coverage' in resources:
            print('=====About to fetch and migrate coverage resource=====')

            url = open_him_url+'/openimis/coverage'
            # Send request to OpenHIM channel
            pingChannel(url, 'Coverage')

        if 'coverageEligibility' in resources:
            print('=====About to fetch and migrate coverageEligibility resource=====')

            url = open_him_url+'/openimis/coverageEligibility'
            # Send request to OpenHIM channel
            pingChannel(url, 'CoverageEligibility')
            
    # USERNAME = configurations["data"]["openhim_user"]
    # PASSWORD = configurations["data"]["openhim_passkey"]

        return Response({'status': "sucess", 'message': 'Preference save succesfully'}, status=200, content_type="application/json")

    except Exception as e:
        print('%s' % type(e))
        return Response({'status': "error", 'message': str(e)},  status=500, content_type="application/json")


@api_view(['POST'])
def fetchSingleResource(request):

    print("========= Executing fetchSingleResource ========== ")
    
    try:

        body = request.body.decode('utf-8')

        payload = json.loads(body)

        resource_type = payload["resourceType"]

        resource_id = payload["resourceId"]

        print(resource_type)

        resource = fetchUniqueResource(resource_type, resource_id)
        
        if (resource and resource["resourceType"] == resource_type):
            return Response({"status": "success", "data": resource, "code":"200"}, content_type="application/json", status="200")

        # Standard Base64 Encoding
        return Response({"status": "failed", "message": "Failed to fetch resource", "code":"404"}, status=400, content_type='application/json')
    except Exception as e:
        print('%s' % type(e))
        return Response({"status": "failed", "message": "Internal server error"}, status=500, content_type='application/json')


@api_view(['POST'])
def subscriptionHandler(request):

    try:

        configurations = initAuth()["config"]

        body = request.body.decode('utf-8')

        payload = json.loads(body)

        # print(payload)

        resource_type = payload["resourceType"].title()

        resource_id = payload["id"]

        # # Post to Suresalama channel
        open_him_url = configurations["data"]["openhim_url"]+':' + \
            str(configurations["data"]["openhim_port"])

        channelUrl = open_him_url + '/suresalama/singleResource'

        if (resource_type == FhirResource.Patient):
            resource = fetchUniqueResource(resource_type, resource_id)
            print(resource)
            if (resource):
                # Send to Suresamala Single resource Channel

                postToSuresalamaChannel(channelUrl, payload)

                return Response({"status": "success", "message": "Resource sent"}, status=200, content_type='application/json')

            return Response({"status": "failed", "message": "Failed to fetch message"}, status=400, content_type='application/json')

            # Send Other resources to Suresamala Single resource Channel
        postToSuresalamaChannel(channelUrl, payload)

        return Response({"status": "success", "message": "Resource sent"}, status=200, content_type='application/json')

    except Exception as e:
        print('%s' % type(e))

        return Response({"status": "failed", "message": type(e)}, status=500, content_type='application/json')


def registerPatientMediator():
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
        "urn": "urn:mediator:python_fhir_r4_Patient_mediator",
        "version": "1.0.1",
        "name": "Python Fhir R4 Patient Mediator",
        "description": "Python Fhir R4 Patient Mediator",

        "defaultChannelConfig": [
            {
                "name": "Python Fhir R4 Patient Mediator",
                "urlPattern": "^/api/api_fhir_r4/Patient$",
                "routes": [
                        {
                            "name": "Python Fhir R4 Patient Mediator Route",
                            "host": configurations["data"]["mediator_url"],
                            "path": "/api/api_fhir_r4/Patient",
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
                "path": "/api/api_fhir_r4/Patient",
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


# when the resource is create or updated, the server sends request to openHIM channe


# mediator create subscription if it doesn't exist on OpenIMIS FHIR server
# the endpoint to be called is openHIM channel
# channel will be configured to a particular mediator which recieves the data fetches the payload
# athe payload will be forwarded to another channel for final submission to Lafia FHIR server through suresalama

# /Query to fetch resource subscription from FHIR server

#  http://localhost:8080/fhir/Subscription?criteria=Observation?code=http://loinc.org\|1975-2&_pretty=true

# https://fhir-server-service.lafia.io/fhir/Subscription?criteria=Observation?code=http://loinc.org\|1975-2

# Working example is here
# https://fhir-server-service.lafia.io/fhir/Subscription?_pretty=true&criteria=Observation%3Fcode%3Dhttp%3A%2F%2Floinc.org%5C%7C1975-2
