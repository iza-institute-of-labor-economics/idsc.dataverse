import requests
from requests.structures import CaseInsensitiveDict
import re


def get_response(url, myKey):
    myKey = myKey
    headers = CaseInsensitiveDict()
    headers["X-Dataverse-key"] = myKey
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.status_code, resp.text
    else:
        return resp.status_code, f"Cannot access dataverse at {url}"


def disassemblePID(datasetPersistentId):

    datasetPersistentId = datasetPersistentId
    # disassemble pid into its parts
    m = re.findall(r"(doi:|hdl:|ark:/)([\d\.]+)/(.+)", datasetPersistentId)
    pid_type = m[0][0]
    pid_type = re.sub(":", "", pid_type)
    pid_type = re.sub("/", "", pid_type)
    prefix = m[0][1]
    identifier = m[0][2]
    identifier4path = re.sub(r"/", "_", identifier)
    return (pid_type, prefix, identifier, identifier4path)
