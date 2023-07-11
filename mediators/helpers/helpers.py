
import json
import requests

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

                if (submitToChannelCallback and len(datac["entry"]) > 0):
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
