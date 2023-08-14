
import json
import requests
import base64

from time import sleep

from overview.views import configview


# Add this temprarily for testing purposes
# Will be taken out upon configuration of SSL certificate
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


def getPortPart(p):

    if (p == "" or p == "80" or p == 80):
        return ""

    return ":"+str(p)


def formatTransactionPayload(datac, callback=None, data_to_update={}):
    print('=========Executing formatTransactionPayload========= ')

    request_dict = {"request": {"method": "POST"}}

    datac["type"] = "transaction"

    for i in range(len(datac["entry"])):
        datac["entry"][i].update(request_dict)
        if (callback != None):
            callback(datac["entry"][i], data_to_update)
            #   datac["entry"][i]["resource"].update(org)

    payload = json.dumps(datac)

    return payload


def formatLocationTransactionPayload(datac):
    print('=========Executing formatLocationTransactionPayload========= ')
    
    location_id_list = [{"id": entry["resource"]["id"]} for entry in datac["entry"]]
    
    request_dict = {"method": "PUT"}

    datac["type"] = "transaction"
    
    size = len(datac["entry"])
    
    def retrieveAndUpdateLocationPartOfValue(entry: dict, entryBundle: dict):
        
      try:
            print('=========Executing retrieveAndUpdateLocationPartOfValue========= ')
        
            result = configview()
            
            configurations = result.__dict__
            
            if("partOf" not in entry):
                return None
                
            part_of_reference = str(entry["partOf"]["reference"]).split("/")
                
            search_location_id = {"id": part_of_reference[1]}
            
            if(search_location_id in location_id_list):
                # Fetch the single location the resource
                return None
                
            fetchedLocation = fetchUniqueResource(part_of_reference[0], part_of_reference[1])
            
            fetchedEntry = {"fullUrl":f"{configurations['data']['openimis_url']}/api/api_fhir_r4/Location/{fetchedLocation['id']}","resource": fetchedLocation}
            
            fetchedEntry["request"] = {**request_dict, "url":f"{part_of_reference[0]}?identifier={part_of_reference[1]}"}
            
            location_id_list.append({"id": fetchedLocation["id"]})
            
            entryBundle["entry"].append(fetchedEntry)
            
            return retrieveAndUpdateLocationPartOfValue(fetchedLocation, entryBundle)
      except  Exception as e:
            print('%s' % type(e))
          
             
    for i in range(size):
        location_id = datac["entry"][i]["resource"]["id"]
        
        entry = datac["entry"][i]
        
        resource_type = datac["entry"][i]["resource"]["resourceType"]
        
        datac["entry"][i].update({"request": {**request_dict, "url":f"{resource_type}?identifier={location_id}"}})
        
        retrieveAndUpdateLocationPartOfValue(entry["resource"], datac)

    payload = json.dumps(datac)

    return payload



def postToSuresalamaChannel(url, payload):
    print('=========Executing postToSuresalamaChannel========= ')
    querystring = {"": ""}
    #  headers = {'Content-Type': "application/json",  # 'Authorization': auth_openhim}
    headers = {'Content-Type': "application/json"}

    responsee = requests.request(
        "POST", url, data=payload, headers=headers, params=querystring, verify=False)

    return responsee


# Ping required Channel
def pingChannel(channelUrl, resource='', querystring={"": ""}):
    print(
        f'=====Send Request to OpenHIM channel to Migrate {resource} resource=====')

    payload = ""
    headers = {"": ""}

    print(channelUrl)

    print(headers)

    return requests.request(
        "GET", channelUrl, data=payload, headers=None, params=querystring, verify=False)


def getPaginatedRecords(datac, url, payload, headers, submitToChannelCallback=None):
    try:
        entries = datac["entry"]

        total = datac['total']

        print(f'Total is {total}')

        if (submitToChannelCallback and len(datac["entry"]) > 0):
            # Submit fetch records to the channnel before continuing
            # Submit per pagination
            resource = datac["entry"][0]['resource']['resourceType']

            print(f"About to Submit first pagination of {resource} to channel")

            response = submitToChannelCallback(datac)
            
            print(
                f'Status Code for aftter submission of {resource} to channel is {response.status_code}')

        have_now = len(datac['entry'])
        if total > 10:
            print('pagintion 1')
            print(datac['link'][1])
            i = 2
            while have_now < total:
                print('havenow ' + str(have_now))
                print('total ' + str(total))

                print(f'pagination {i}')
                print(datac['link'][1]['url'])

                print("after part")

                part_after_patient = '?page-offset='+str(i)
                i = i+1
                next_url = url + part_after_patient

                print(next_url)

                # Make the next request
                sleep(1)
                response = requests.request(
                    "GET", next_url, data=payload, headers=headers, verify=False)
                print(response.status_code)
                datac2 = json.loads(response.text)

                if datac2.get('entry') is None:

                    break

                print("got new data")
                
                # len(datac["entry"]) > 0

                if (submitToChannelCallback and datac2["entry"]):
                    # Submit fetch records to the channnel before continuing
                    # Submit per pagination
                    print("About to submit to channel")

                    submitToChannelCallback(datac2)

                    sleep(1)

                print(str(len(datac2['entry'])))

                entries.extend(datac2['entry'])

                have_now = len(entries)

            datac['entry'] = entries
        return datac
    except Exception as e:
        print('%s' % type(e))

# Change here to post latter (Updated)


def submitPaginatedResourcesToChannelCallback(paginatedData):

    result = configview()
    configurations = result.__dict__

    print(f'current data is this: {paginatedData}')

    # Format and serialize data to JSON string

    channelPayload = formatTransactionPayload(
        paginatedData)
    # # Post to Suresalama channel
    open_him_url = configurations["data"]["openhim_url"]+':' + \
        str(configurations["data"]["openhim_port"])

    channelUrl = open_him_url + '/suresalama/resource'

    return postToSuresalamaChannel(channelUrl,  channelPayload)

    # print(response.status_code)
    
def submitPaginatedLocationResourcesToChannelCallback(paginatedData):

    result = configview()
    configurations = result.__dict__

    print(f'current data is this: {paginatedData}')

    # Format and serialize data to JSON string
    channelPayload = formatLocationTransactionPayload(
        paginatedData)
    # # Post to Suresalama channel
    open_him_url = configurations["data"]["openhim_url"]+':' + \
        str(configurations["data"]["openhim_port"])

    channelUrl = open_him_url + '/suresalama/resource'

    return postToSuresalamaChannel(channelUrl,  channelPayload)

    # print(response.status_code)


def find(predicate, iterable):
    for item in iterable:
        if predicate(item):
            return item
    return None


# Create Subscription
def createSubscriptionResourceOnOpenIMIS(resource, endpoint, headers, subscription_url):

    print("==========Executing createSubscriptionResourceOnOpenIMIS ======= ")

    print("========Resource========="+resource)

    print(endpoint, headers, subscription_url)

    try:

        # "payload": "application/fhir+json",
        # "header": [
        #     "Authorization: Bearer secret-token-abc-123"
        # ]

        payload = {
            "resourceType": "Subscription",
            "status": "active",
            "criteria": resource,
            "reason": resource,
            "channel": {
                "type": "rest-hook",
                "endpoint": endpoint,
                "payload": "application/fhir+json",
                "header": [
                    "Authorization: Bearer secret-token-abc-123"
                ]
            },
            "end": "4021-12-31T23:59:59Z"
        }

        payload = json.dumps(payload)

        response = requests.request(
            "POST", subscription_url, data=payload, headers={**headers,  'Content-Type': "application/json"}, verify=False)

        data = json.loads(response.text)
        return data
    except Exception as e:
        print('%s' % type(e))


def findOrCreateOpenIMISSubscriptionResource(auth_openimis, resource):
    result = configview()
    configurations = result.__dict__

    open_him_url = configurations["data"]["openhim_url"]+':' + \
        str(configurations["data"]["openhim_port"])

    status = ""

    subscription_url = configurations["data"]["openimis_url"]+getPortPart(
        configurations["data"]["openimis_port"])+"/api/api_fhir_r4/Subscription/"

    # channelUrl = open_him_url + '/resource/subscribe'
    channel_subscription_url = 'https://143.198.111.7:5000/resource/subscribe'

    headers = {'Authorization': auth_openimis}

    response = requests.request(
        "GET", subscription_url, data="", headers=headers, verify=False)

    data = json.loads(response.text)

    print(data)

    if (len(data['entry']) > 0):
        # Subscriptions are available

        subscription = find(lambda x: x['resource']
                            ['criteria'] == resource, data['entry'])

        if (subscription is None):
            # Subscription doesnt' exist Create a new Subscription for the given resource
            new_subscription = createSubscriptionResourceOnOpenIMIS(
                resource, channel_subscription_url, headers, subscription_url)

            criteria, sub_id, status = new_subscription[
                'criteria'], new_subscription['id'], new_subscription['status']

            status = f'New Subscription for resoure ({resource}) created with id: {sub_id} and status: {status}'
        else:
            print(criteria, sub_id, status)
            criteria, sub_id, status = subscription['resource']['criteria'], subscription[
                'resource']['id'], subscription['resource']['status']

            status = f'Subscription for resource ({criteria}) already exists with id: {sub_id}. Status is {status}'

    return {"status": status}


def fetchUniqueResource(resource_type, resource_id):

    try:
        print("==========Executing fetchUniqueResource ======= ")

        data = initAuth()

        configurations = data["config"]

        auth_openimis = data["auth"]

        if (len(str(resource_type)) > 0 and len(resource_id) > 0):
            resource_type = resource_type.title()

            url = configurations["data"]["openimis_url"]+getPortPart(
                configurations["data"]["openimis_port"])+"/api/api_fhir_r4/"+str(resource_type)+"/"+str(resource_id)

            headers = {
                'Content-Type': "application/json",
                'Authorization': auth_openimis
            }

            querystring = {"": ""}

            payload = ""

            response = requests.request(
                "GET", url, data=payload, headers=headers, params=querystring, verify=False)

            datac = json.loads(response.text)

            return datac
        return None
    except Exception as e:
        print('%s' % type(e))
        

def initAuth():
    result = configview()
    configurations = result.__dict__
    # username:password-openhimclient:openhimclientPasskey
    authvars = configurations["data"]["openimis_user"] + \
        ":"+configurations["data"]["openimis_passkey"]
    # Standard Base64 Encoding
    encodedBytes = base64.b64encode(authvars.encode("utf-8"))
    encodedStr = str(encodedBytes, "utf-8")
    auth_openimis = "Basic " + encodedStr

    return {"auth": auth_openimis, "config": configurations}
