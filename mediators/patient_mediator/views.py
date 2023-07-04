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

from helpers.helpers import requests, formatTransactionPayload, postToSuresalamaChannel, getPortPart, pingChannel, getPaginatedRecords


# Add this temprarily for testing purposes
# Will be taken out upon configuration of SSL certificate
# from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
# requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

@api_view(['GET', 'POST'])
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

        # retur`n url

        if page_offset != "":
            url = url+"?page-offset="+page_offset
        # Query the upstream server via openHIM mediator port 8000
        # Caution: To secure the endpoint with SSL certificate,FQDN is required
        if request.method == 'GET':
            print(" yes I was here")
            querystring = {"": ""}
            payload = ""
            headers = {'Authorization': auth_openimis}
            print(url)
            print(headers)
            response = requests.request(
                "GET", url, data=payload, headers=headers, params=querystring, verify=False)

            datac = json.loads(response.text)

            getPaginatedRecords(datac, url, payload, headers)

            # Pass any subsequent data updates as callback parameters

            # Here we intend update to patient records retrieved to reflect organization Id

            def update_patient_org(
                data, org): return data['resource'].update(org)

            # Managing organization to be updated

            org = {"managingOrganization": {
                "reference": "Organization/"+str(org_id)}}

            # Format and serialize data to JSON string

            channelPayload = formatTransactionPayload(
                datac, update_patient_org, org)

            # # Post to Suresalama channel
            open_him_url = configurations["data"]["openhim_url"]+':' + \
                str(configurations["data"]["openhim_port"])

            channelUrl = open_him_url + '/suresalama/resource'

            postToSuresalamaChannel(channelUrl,  channelPayload)

            print(response.status_code)

            return Response(datac)

            # return response.json()
        elif request.method == 'POST':
            print(" yes I was here 2")

            querystring = {"": ""}
            data = json.dumps(request.data)
            payload = data
            headers = {
                'Content-Type': "application/json",
                'Authorization': auth_openimis
            }
            response = requests.request(
                "POST", url, data=payload, headers=headers, params=querystring)
            datac = json.loads(response.text)
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

        if 'insuranceProduct' in resources:
            print('=====About to fetch and migrate insurance products=====')

            url = open_him_url+'/openimis/product'
            # Send request to OpenHIM channel
            pingChannel(url, 'Insurance Product')

        if 'policy' in resources:
            print('=====About to fetch and migrate policy=====')

            url = open_him_url+'/openimis/policy'
            # Send request to OpenHIM channel
            pingChannel(url, 'Policy')

        if 'insuree' in resources:
            print('=====About to fetch and migrate insuree=====')

            querystring = {"orgId": payload["orgId"] or ""}

            url = open_him_url+'/openimis/insuree'
            # Send request to OpenHIM channel
            pingChannel(url, 'Insuree', querystring)

        if 'organization' in resources:
            print('=====About to fetch and migrate insuree=====')

            url = open_him_url+'/openimis/organization'
            # Send request to OpenHIM channel
            pingChannel(url, 'Organization')

        if 'practitioner' in resources:
            print('=====About to fetch and migrate practitioner=====')

            url = open_him_url+'/openimis/practitioner'
            # Send request to OpenHIM channel
            pingChannel(url, 'Practitioner')

    # USERNAME = configurations["data"]["openhim_user"]
    # PASSWORD = configurations["data"]["openhim_passkey"]

        return Response({'status': "sucess", 'message': 'Preference save succesfully'})

        # print("page_offset")
        # print(page_offset)

        # result = configview()
        # configurations = result.__dict__
        # authvars = configurations["data"]["openimis_user"]+":"+configurations["data"]["openimis_passkey"]#username:password-openhimclient:openhimclientPasskey
        # # Standard Base64 Encoding
        # encodedBytes = base64.b64encode(authvars.encode("utf-8"))
        # encodedStr = str(encodedBytes, "utf-8")
        # auth_openimis = "Basic " + encodedStr

        # # Standard Base64 Encoding
        # url = configurations["data"]["openimis_url"]+getPortPart(configurations["data"]["openimis_port"])+"/api/api_fhir_r4/Patient"

        # # retur`n url

        # if page_offset!="":
        # 	url = url+"?page-offset="+page_offset
        # # Query the upstream server via openHIM mediator port 8000
        # # Caution: To secure the endpoint with SSL certificate,FQDN is required
        # if request.method == 'GET':
        # 	print(" yes I was here")
        # 	querystring = {"":""}
        # 	payload = ""
        # 	headers = {'Authorization': auth_openimis}
        # 	print(url)
        # 	print(headers)
        # 	response = requests.request("GET", url, data=payload, headers=headers, params=querystring, verify=False)

        # 	datac = json.loads(response.text)

        # 	getPaginatedRecords(datac, url, payload, headers)

        # 	print(response.status_code)

        # 	# print(response.json())

        # 	# datac = json.loads(response.text)

        # 	return Response(datac)

        # 	# return response.json()
        # elif request.method == 'POST':
        # print(" yes I was here 2")

        # querystring = {"":""}
        # data = json.dumps(request.data)
        # payload = data
        # headers = {
        # 	'Content-Type': "application/json",
        # 	'Authorization': auth_openimis
        # 	}
        # response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
        # datac = json.loads(response.text)
        # return Response(datac)

    except Exception as e:
        print('%s' % type(e))
        return Response({'status': "error", 'message': str(e)})


# @api_view(['POST'])
# def savePrefs(request):
#     requestt = {
#         "method": 'GET'
#     }
#     # getPatient(requestt)

#     org_id = request.data.get("id")
#     # host = request.data.get("id")
#     # username = request.data.get("id")
#     # password = request.data.get("id")

#     # return Response({"org_id":org_id})

#     result = configview()
#     configurations = result.__dict__

#     print("Step 1")

#     # username:password-openhimclient:openhimclientPasskey
#     authvars_him = configurations["data"]["openhim_user"] + \
#         ":"+configurations["data"]["openhim_passkey"]
#     # Standard Base64 Encoding
#     encodedBytes_home = base64.b64encode(authvars_him.encode("utf-8"))
#     encodedStr_him = str(encodedBytes_home, "utf-8")
#     auth_openhim = "Basic " + encodedStr_him
#     # /api/api_fhir_r4/Patient
#     base_him = 'http://'+configurations["data"]["openhim_url"]+":"+str(5001)
#     url_him_get = base_him+"/api/api_fhir_r4/Patient"
#     url_him = base_him+"/api/lafia/PatientResource"

#     print("Step 2")
#     querystring = {"": ""}
#     payload = ""
#     # headers = {'Authorization': auth_openhim}
#     headers = {'Content-Type': "application/json"}
#     print(url_him_get)
#     print(headers)
#     response = requests.request(
#         "GET", url_him_get, data=payload, headers=headers, params=querystring)
#     print("Step 2.1")
#     print(response.status_code)
#     datac = json.loads(response.text)


# # x_sample = {"resourceType": "Bundle",
# # "type": "transaction",
# # "total": 61,
# # "link": [
# #     {
# #         "relation": "self",
# #         "url": "https%3A%2F%2Fdemo.openimis.org%2Fapi%2Fapi_fhir_r4%2FPatient%2F%3F%3D"
# #     },
# #     {
# #         "relation": "next",
# #         "url": "https%3A%2F%2Fdemo.openimis.org%2Fapi%2Fapi_fhir_r4%2FPatient%2F%3F%3D%26page-offset%3D2"
# #     }
# # ],
# # "entry": []
#     # }
#     entries = datac["entry"]
#     total = datac['total']
#     print(total)
#     have_now = len(datac['entry'])
#     if total > 10:
#         print('pagintion 1')
#         print(datac['link'][1])
#         i = 2
#         while have_now < total:
#             print('havenow ' + str(have_now))
#             print('total ' + str(total))

#             print('pagintion 1.2')
#             print(datac['link'][1]['url'])
#             # decoded_url = unquote(datac['link'][1]['url'])
#             # part_after_patient = decoded_url.split("/Patient", 1)[1]
#             print("after part")
#             # replace =& with ''
#             # part_after_patient = part_after_patient.replace("=&", "")
#             # part_after_patient = part_after_patient.replace("/", "")
#             part_after_patient = '?page-offset='+str(i)
#             i = i+1
#             next_url = url_him_get + part_after_patient

#             # replace part before /api/ with url_him
#             # next_url = base_him + "/api/" + next_url.split("/api/", 1)[1]
#             print(next_url)

#             # Make the next request
#             sleep(1)
#             response = requests.request(
#                 "GET", next_url, data=payload, headers=headers, params=querystring)
#             print("pre erro")
#             print(response.status_code)
#             datac2 = json.loads(response.text)

#             print("got new data")
#             print(str(len(datac2['entry'])))

#             entries.extend(datac2['entry'])

#             have_now = len(entries)

#     print("entries total" + str(len(entries)))

#     datac["entry"] = entries
#     print("Step 3")

#     datac["type"] = "transaction"

#     request_dict = {
#         "request": {
#             "method": "POST"
#         }
#     }

#     org = {
#         "managingOrganization": {
#             "reference": "Organization/"+str(org_id)
#         }
#     }

#     for i in range(len(datac["entry"])):
#         datac["entry"][i].update(request_dict)
#         datac["entry"][i]["resource"].update(org)

#     data = json.dumps(datac)
#     payload = data
#     headers = {
#         'Content-Type': "application/json",
#         # 'Authorization': auth_openhim
#     }
#     print(url_him)
#     print("Step 3.01")
#     responsee = requests.request(
#         "POST", url_him, data=payload, headers=headers, params=querystring)
#     print("Step 3.1")
#     print(url_him)
#     print(responsee.status_code)
#     # datac = json.loads(responsee.text)

#     print("Step 4")
#     return Response({"nooo": "yes"})

#     # call getter openhim
#     # call poster

#     return Response({"ok": "thankyou"})


# @api_view(['GET', 'POST'])
# def getPatient(request):
#     print(" yes I was here 3")

#     # get url params
#     page_offset = request.GET.get("page-offset", "")

#     print("page_offset")
#     print(page_offset)

#     result = configview()
#     configurations = result.__dict__
#     # username:password-openhimclient:openhimclientPasskey
#     authvars = configurations["data"]["openimis_user"] + \
#         ":"+configurations["data"]["openimis_passkey"]
#     # Standard Base64 Encoding
#     encodedBytes = base64.b64encode(authvars.encode("utf-8"))
#     encodedStr = str(encodedBytes, "utf-8")
#     auth_openimis = "Basic " + encodedStr

#     # Standard Base64 Encoding
#     url = configurations["data"]["openimis_url"]+getPortPart(
#         configurations["data"]["openimis_port"])+"/api/api_fhir_r4/Patient"

#     if page_offset != "":
#         url = url+"?page-offset="+page_offset
#     # Query the upstream server via openHIM mediator port 8000
#     # Caution: To secure the endpoint with SSL certificate,FQDN is required
#     if request.method == 'GET':
#         print(" yes I was here")
#         querystring = {"": ""}
#         payload = ""
#         headers = {'Authorization': auth_openimis}
#         print(url)
#         print(headers)
#         response = requests.request(
#             "GET", url, data=payload, headers=headers, params=querystring, verify=False)
#         print("lol error")
#         print(response.status_code)

#         datac = json.loads(response.text)

#         return Response(datac)

#     elif request.method == 'POST':
#         print(" yes I was here 2")

#         querystring = {"": ""}
#         data = json.dumps(request.data)
#         payload = data
#         headers = {
#             'Content-Type': "application/json",
#             'Authorization': auth_openimis
#         }
#         response = requests.request(
#             "POST", url, data=payload, headers=headers, params=querystring)
#         datac = json.loads(response.text)
#         return Response(datac)


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


# 1. Deploy and automate V2 backend

# 2. Extend OpenIMIS mediators to handle other FHIR resources (Group, Location, Claim, ClaimResponse,  Coverage). Currently, we have the following FHIR resources migrated sucessfully: InsurancePlan, Contract (policy),  Insuree (Patient), and Organization,)

# 3. Collaborate with team members to resolve Issues with OpenHIM deployment

# 4. Integrate subscription FHIR resource on OpenIMIS  to hand two-way syncing of data across OpenIMIS system and Lafia FHIR Server
