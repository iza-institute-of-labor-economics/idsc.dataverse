import requests
from idsc.dataverse.utils import get_response, disassemblePID
import json
import re
import os
import math
from pathlib import Path
from requests.structures import CaseInsensitiveDict
import shutil
import zipfile
import glob
import urllib.parse as up


class API(object):

    def __init__(self, host, token):
        self.token = token
        self.host = host
        self.makeDataDir()
        # returns ddataverse saving dir and cache dir

    def getTotalCount(self):
        url = f"{self.host}/api/search?q=*&type=dataset"
        status = get_response(url, self.token)
        if status[0] == 200:
            a = json.loads(status[1])
            TotalCount = a["data"]["total_count"]
            return TotalCount
        else:
            print(f"{self.getTotalCount.__name__}: {status}")
        return None

    def getPIDs(self):
        pid2dataverse = {}
        TotalCount = self.getTotalCount()
        if not isinstance(TotalCount, int):
            print(f"{self.getPIDs.__name__}: Could not get a total count.")
            return pid2dataverse

        pages = math.ceil(TotalCount / 1000)

        for i in range(pages):
            # paginate to get all datasets
            url = self.host + "/api/search/?" + \
                    up.urlencode(
                        {
                            "q": "*",
                            "type": "dataset",
                            "start": i*1000,
                            "per_page": 1000}
                    )
            status = get_response(url, self.token)
            if status[0] == 200:
                a = json.loads(status[1])
                items = a["data"]["items"]
                for j in range(len(items)):
                    myJSON = items[j]
                    pid2dataverse[myJSON['global_id']] = \
                        myJSON['identifier_of_dataverse']
            else:
                print(f"{self.getPIDs.__name__}: {status}")
            return pid2dataverse

    def makeDataDir(self):
        myDataDir = re.sub(r"http.*//", "", self.host)
        myDataDir = re.sub(r"/", "", myDataDir)

        user_home = Path.home()
        if not os.path.exists(f'{user_home}/.idsc'):
            os.mkdir(f'{user_home}/.idsc')
        if not os.path.exists(f'{user_home}/.idsc/dataverse'):
            os.mkdir(f'{user_home}/.idsc/dataverse')
        if not os.path.exists(f'{user_home}/.idsc/dataverse/api'):
            os.mkdir(f'{user_home}/.idsc/dataverse/api')
        if not os.path.exists(f'{user_home}/.idsc/dataverse/api/{myDataDir}'):
            os.mkdir(f'{user_home}/.idsc/dataverse/api/{myDataDir}')
        if not os.path.exists(f'{user_home}/.idsc/.cache'):
            os.mkdir(f'{user_home}/.idsc/.cache')

        self.dvDir = f'{user_home}/.idsc/dataverse/api/{myDataDir}'
        self.cache = f'{user_home}/.idsc/.cache'

    def getMetadata(self, pid):
        pid = pid
        likeExample = {}
        url = f"{self.host}/api/datasets/:persistentId/?persistentId={pid}"
        a = json.loads(
            get_response(url, self.token)[1]
            )["data"]["latestVersion"]

        likeExample = {}
        likeExample["datasetVersion"] = a

        # this needs to be done or else one cannot send release=no
        if "versionState" in likeExample["datasetVersion"]:
            del likeExample["datasetVersion"]["versionState"]
        if "releaseTime" in likeExample["datasetVersion"]:
            del likeExample["datasetVersion"]["releaseTime"]
        without_files = {}
        only_files = {}
        without_files["datasetVersion"] = \
            {k: v for k, v in
             likeExample["datasetVersion"].items() if k != "files"}
        only_files["datasetVersion"] = {k: v for k, v in
                                        likeExample["datasetVersion"].items()
                                        if k != "metadataBlocks"}

        datasetPersistentId =\
            likeExample["datasetVersion"]["datasetPersistentId"]

        pid_type, prefix, identifier, identifier4path =\
            disassemblePID(datasetPersistentId)

        # identifier = re.sub(r"doi:\d+\.\d+\/", "", datasetPersistentId)

        if not os.path.exists(f'{self.dvDir}/{pid_type}'):
            os.makedirs(f'{self.dvDir}/{pid_type}')
        if not os.path.exists(f'{self.dvDir}/{pid_type}/{prefix}'):
            os.makedirs(f'{self.dvDir}/{pid_type}/{prefix}')
        if not os.path.exists(
            os.path.join(
                self.dvDir,
                pid_type,
                prefix,
                identifier4path
                )
                ):
            os.makedirs(f'{self.dvDir}/{pid_type}/{prefix}/{identifier4path}')

        with open(
            os.path.join(
                self.dvDir,
                pid_type,
                prefix,
                identifier4path,
                'no_files.json'
                ), 'w'
                ) as f:
            json.dump(without_files, f)
        with open(
            os.path.join(
                self.dvDir,
                pid_type,
                prefix,
                identifier4path,
                'files_only.json'
                ), 'w'
                ) as f:
            json.dump(only_files, f)
        with open(
            os.path.join(
                self.dvDir,
                pid_type,
                prefix,
                identifier4path,
                'all.json'
                ), 'w'
                ) as f:
            json.dump(likeExample, f)

    def getDatasetFiles(self, pid):
        pid = pid
        likeExample = {}
        url = f"{self.host}/api/datasets/:persistentId/?persistentId={pid}"
        a = json.loads(
            get_response(url, self.token)[1])["data"]["latestVersion"]
        likeExample["datasetVersion"] = a

        datasetPersistentId = \
            likeExample["datasetVersion"]["datasetPersistentId"]
        pid_type, prefix, identifier, identifier4path =\
            disassemblePID(datasetPersistentId)

        url = self.host + \
            "/api/access/dataset/:persistentId/?" + \
            up.urlencode(
                {"persistentId": pid, "format": "original"}
                )
        headers = CaseInsensitiveDict()
        headers["X-Dataverse-key"] = self.token

        if not os.path.exists(f'{self.dvDir}'):
            os.mkdir(f'{self.dvDir}')

        if not os.path.exists(f'{self.dvDir}/{pid_type}'):
            os.makedirs(f'{self.dvDir}/{pid_type}')

        if not os.path.exists(f'{self.dvDir}/{pid_type}/{prefix}'):
            os.makedirs(f'{self.dvDir}/{pid_type}/{prefix}')

        if not os.path.exists(
            os.path.join(
                self.dvDir,
                pid_type,
                prefix,
                identifier4path
                )
                ):
            os.makedirs(f'{self.dvDir}/{pid_type}/{prefix}/{identifier4path}')

        r = requests.get(url, headers=headers, allow_redirects=True)
        if r.status_code == 200:
            filename = r.headers.get("content-disposition")
            if filename:
                filename = filename.split("filename=")[1]
                filename = re.sub(r'"', '', filename)
                with open(
                    os.path.join(
                        self.dvDir,
                        pid_type,
                        prefix,
                        identifier4path,
                        filename
                        ), "wb"
                        ) as file:
                    file.write(r.content)
            else:
                filename = "downloaded_file.txt"
                with open(
                    os.path.join(
                        self.dvDir,
                        pid_type,
                        prefix,
                        identifier4path,
                        filename
                        ), "wb"
                        ) as file:
                    file.write(r.content)
            return filename

        else:
            print(f"{self.getDatasetFiles.__name__}:",
                  f"Failed to download files for {pid}.",
                  f"Status code: {r.status_code}")

    def deleteDataset(self, pid):
        pid = pid
        url = self.host +\
            "/api/datasets/:persistentId/destroy/?" + \
            up.urlencode({"persistentId": pid})

        # Define headers with the API token
        headers = {"X-Dataverse-key": self.token}

        # Make a DELETE request
        response = requests.delete(url, headers=headers)

        # Check the response
        if response.status_code == 200:
            print(f"{self.deleteDataset.__name__}:",
                  "Request was successful. The resource has been deleted.")
        else:
            print(f"{self.deleteDataset.__name__}:",
                  f"Request failed with status code: {response.status_code}")

    def exportDataFor(self, targetDataverse):
        targetDataverse = targetDataverse
        target = re.sub(r"http.*//", "", targetDataverse)
        target = re.sub(r"/", "", target)
        src = self.dvDir
        dst = self.cache
        dst = dst+"/"+target

        if os.path.isdir(dst):
            shutil.rmtree(dst)
        copyDestination = shutil.copytree(src, dst)
        print(f'{self.exportDataFor.__name__}:',
              f'copied all to {copyDestination}')

    def createDataset(self, pid, dataverse):
        pid = pid
        dataverse = dataverse
        cache = self.cache
        myDataDir = re.sub(r"http.*//", "", self.host)
        myDataDir = re.sub(r"/", "", myDataDir)
        myDataDir = cache+"/"+myDataDir

        rootDataverse = dataverse
        pid_type, prefix, identifier, identifier4path = disassemblePID(pid)
        filename = "no_files.json"

        file_path = os.path.join(
            myDataDir,
            pid_type,
            prefix,
            identifier4path,
            filename
        )

        url = self.host + \
            f"/api/dataverses/{rootDataverse}/datasets/:import?" + \
            up.urlencode(
                {
                    "pid": pid,
                    "release": "no",
                    "doNotValidate": "true"
                    }
                    )

        # Define the headers with the API token
        headers = {"X-Dataverse-key": self.token}

        # Make a POST request with the file upload
        response = requests.post(url, headers=headers,
                                 data=open(file_path, 'r').read())

        # Check the response
        # it returns "releaseCompleted":false but it is erroneous
        if response.status_code == 200 or response.status_code == 201:
            print("Request was successful.")
            print(response.text)
        else:
            print("Request failed with status code:",
                  f"{response.status_code}, {response.text}")

    def get_filenames_from_zipfile(self, pid):
        pid = pid
        pid_type, prefix, identifier, identifier4path = disassemblePID(pid)
        cache = self.cache
        myDataDir = re.sub(r"http.*//", "", self.host)
        myDataDir = re.sub(r"/", "", myDataDir)
        myDataDir = cache+"/"+myDataDir

        myZipFile = os.path.join(
            myDataDir,
            pid_type,
            prefix,
            identifier4path,
            'dataverse_files.zip'
        )
        myFileDict = {}
        if not os.path.exists(myZipFile):
            return myFileDict

        with zipfile.ZipFile(myZipFile, "r") as f:
            for name in f.namelist():
                if name != "MANIFEST.TXT":
                    data = f.read(name)
                    if re.match(r".+?\.zip$", name):
                        import io
                        # Create an in-memory buffer to hold the zip file
                        output_buffer = io.BytesIO()
                        # Create a new zip file in memory
                        with zipfile.ZipFile(output_buffer,
                                             'w', zipfile.ZIP_DEFLATED)\
                                as in_memory_zip:
                            # Add a file to the in-memory zip
                            in_memory_zip.writestr(name, data)
                        # You can now use output_buffer.getvalue()
                        # to get the zipped data as bytes.
                        data = output_buffer.getvalue()

                    myFileDict[name] = data
        return myFileDict

    def get_metadata_for_filename(self, pid, filename):
        pid = pid
        filename = filename
        cache = self.cache
        myDataDir = re.sub(r"http.*//", "", self.host)
        myDataDir = re.sub(r"/", "", myDataDir)
        myDataDir = cache+"/"+myDataDir

        pid_type, prefix, identifier, identifier4path = disassemblePID(pid)

        file_path = os.path.join(
            myDataDir,
            pid_type,
            prefix,
            identifier4path,
            'files_only.json'
        )
        with open(file_path) as f:
            data = json.load(f)

        data = data['datasetVersion']["files"]
        for snippet in data:
            if snippet["dataFile"]["filename"] == filename:
                snippet2return = snippet
                return snippet2return

    def uploadFile(self, pid, filename):
        pid = pid
        filename = filename
        cache = self.cache
        myDataDir = re.sub(r"http.*//", "", self.host)
        myDataDir = re.sub(r"/", "", myDataDir)
        myDataDir = cache+"/"+myDataDir

        url = self.host +\
            "/api/datasets/:persistentId/add?" +\
            up.urlencode({"persistentId": pid, "datasetId": "80"})

        # Define headers with the API token
        headers = {"X-Dataverse-key": self.token}

        jsonSTRING = str(self.get_metadata_for_filename(pid, filename))

        myFileDict = self.get_filenames_from_zipfile(pid)
        for k, v in myFileDict.items():
            if k == filename:
                FileContent = myFileDict[k]
                data = {'jsonData': jsonSTRING}
                files = {'file': (filename, FileContent)}

                response = requests.post(url, headers=headers,
                                         data=data, files=files)

                print(self.uploadFile.__name__, ":", response.status_code)
                print(self.uploadFile.__name__, ":", response.text)

    def uploadFiles(self, pid):

        pid = pid
        cache = self.cache
        myDataDir = re.sub(r"http.*//", "", self.host)
        myDataDir = re.sub(r"/", "", myDataDir)
        myDataDir = cache+"/"+myDataDir

        url = self.host + \
            "/api/datasets/:persistentId/add?" +\
            up.urlencode({"persistentId": pid, "datasetId": "80"})

        # Define headers with the API token
        headers = {"X-Dataverse-key": self.token}

        myFileDict = self.get_filenames_from_zipfile(pid)
        for k, v in myFileDict.items():
            filename = k
            FileContent = myFileDict[k]
            jsonSTRING = str(self.get_metadata_for_filename(pid, filename))
            data = {'jsonData': jsonSTRING}
            files = {'file': (filename, FileContent)}

            response = requests.post(url, headers=headers,
                                     data=data, files=files)

            print(self.uploadFile.__name__, ":", response.status_code)
            print(self.uploadFile.__name__, ":", response.text)

    def publishDataset(self, pid):
        pid = pid
        url = self.host + \
            "/api/datasets/:persistentId/actions/:publish?" + \
            up.urlencode({"persistentId": pid, "type": "major"})
        #print(url)

        headers = {"X-Dataverse-key": self.token}
        response = requests.post(url, headers=headers)
        # Check the response
        # it returns "releaseCompleted":false but it is erroneous
        if response.status_code == 200 or response.status_code == 201:
            print(f"{self.publishDataset.__name__}: Request was successful.")
            print(self.publishDataset.__name__, ":", response.text)
        else:
            print(f"{self.publishDataset.__name__}:",
                  "Request failed with status code:",
                  f"{response.status_code}, {response.text}")

    def modifyPID(self, pid_old, pid_new):
        '''
        strategy download pid_old, upload pid_new. Save in
        ~/.IDSC/Dataverse/.cache and destroy when done.
        '''
        # cacheDir = self.cache
        instanceDir = self.dvDir
        pid_old = pid_old
        pid_new = pid_new

        pid_type_old, prefix_old, identifier_old, \
            identifier4path_old = disassemblePID(pid_old)
        pid_type_new, prefix_new, identifier_new, \
            identifier4path_new = disassemblePID(pid_new)

        self.getMetadata(pid_old)
        self.getDatasetFiles(pid_old)

        print(f"{self.modifyPID.__name__}:",
              f"Deleting {pid_old} and uploading (meta-)data for {pid_new}")

        # a list with all json files
        fileList = glob.glob(
            os.path.join(
                instanceDir,
                pid_type_old,
                prefix_old,
                identifier4path_old,
                '*.json'
            )
        )

        # make doi changes
        for filePath in fileList:
            # readfile
            with open(filePath) as f:
                contents_old = f.read()
                # change DOI
                contents_new = contents_old.replace(
                    f"{pid_old}",
                    f"{pid_new}"
                    )
                contents_new = contents_new.replace(f"{identifier_old}",
                                                    f"{identifier_new}")

                with open(filePath, "w") as fnew:
                    fnew.write(contents_new)

        shutil.move(f'{instanceDir}/{pid_type_old}',
                    f'{instanceDir}/{pid_type_new}')
        shutil.move(f'{instanceDir}/{pid_type_new}/{prefix_old}',
                    f'{instanceDir}/{pid_type_new}/{prefix_new}')
        shutil.move(
            f'{instanceDir}/{pid_type_new}/{prefix_new}/{identifier4path_old}',
            f'{instanceDir}/{pid_type_new}/{prefix_new}/{identifier4path_new}')

        # get dataverse collection where pid_old belongs
        pid2dataverse = self.getPIDs()
        # print(pid2dataverse)
        dataverse = pid2dataverse[pid_old]

        # delete old dataset in target dataverse
        self.deleteDataset(pid_old)

        self.exportDataFor(self.host)
        # create new dataset with new DOI in known dataverse
        self.createDataset(pid_new, dataverse)

        # upload files in existing dataset
        myFileDict = self.get_filenames_from_zipfile(pid_new)
        for filename in myFileDict.keys():
            self.uploadFile(pid_new, filename)

        # cleanup
        print(f"{self.modifyPID.__name__}: Cleaning up")
        shutil.rmtree(f'{instanceDir}/{pid_type_new}/{prefix_new}')

        print(f"{self.modifyPID.__name__}: Done")

    def getDVList(self):
        dvTree = {}
        url = f"{self.host}/api/dataverses/1"
        status = get_response(url, self.token)
        if status[0] == 200:
            a = json.loads(status[1])
            dvTree["root"] = a["data"]["alias"]
        else:
            return status

        url = f"{self.host}/api/dataverses/1/contents"
        status = get_response(url, self.token)
        if status[0] == 200:
            a = json.loads(status[1])
            dvTree["children"] = a["data"]
        else:
            return status
        return dvTree

    def createDataverse(self, **kwargs):
        controlledV = '''DEPARTMENT, JOURNALS, LABORATORY,
        ORGANIZATIONS_INSTITUTIONS, RESEARCHERS, RESEARCH_GROUP,
        RESEARCH_PROJECTS, TEACHING_COURSES, UNCATEGORIZED'''
        controlledV = re.sub(r"\n", "", controlledV)
        controlledV = re.sub(r"\s+", " ", controlledV)

        if len(kwargs.keys()) == 0:
            usage = f'Usage:\n{self.createDataverse.__name__}(\n\tname=\
                "Name of Dataverse", \
            \n\talias="Alias of Dataverse", \
            \n\tdataverseContacts ="email1,email2,etc...", \
            \n\taffiliation="University of...", \
            \n\tdescription="This dataverse contains..", \
            \n\tdataverseType=type, \
            \n\tparent="A pre-existing parent dataverse"\n\t) \
            \nwhere type is one of: {controlledV}.'
            print(usage)
            return
        else:
            elements = ["name", "alias", "dataverseContacts", "affiliation",
                        "description", "dataverseType", "parent"]

            for element in elements:
                if element not in set(kwargs.keys()):
                    if element == "dataverseContacts":
                        print("Missing: dataverseContacts=\"comma seperated\
                           email addresses\"")
                        return
                    if element == "dataverseType":
                        print(f"Missing dataverseType. Needs to be one of:\
                          \n{controlledV}")
                        return
                    else:
                        print(f"Missing {element} ")
                        return

            contacts = ['{"contactEmail": "'+x+'"}' for x in
                        kwargs["dataverseContacts"].split(",")]
            contactsString = "["+", ".join(contacts)+"]"

            jsonString = '''

            {
            "name": "'''+kwargs["name"]+'''",
            "alias": "'''+kwargs["alias"]+'''",
            "dataverseContacts": '''+contactsString+''',
            "affiliation": "'''+kwargs["affiliation"]+'''",
            "description": "'''+kwargs["description"]+'''",
            "dataverseType": "'''+kwargs["dataverseType"]+'''"
            }

            '''

            headers = {"X-Dataverse-key": self.token}
            url = f'{self.host}/api/dataverses/{kwargs["parent"]}'

            response = requests.post(url, headers=headers, data=jsonString)
            if response.status_code == 200 or response.status_code == 201:
                print(f"{self.createDataverse.__name__}:",
                      "Successfully created dataverse")
                print(response.text)
            else:
                print(f"{self.createDataverse.__name__}",
                      "Failed to create dataverse with status code:",
                      f"{response.status_code}, {response.text}")

    def publishDataverse(self, dataverse):
        dataverse = dataverse
        headers = {"X-Dataverse-key": self.token}
        url = f"{self.host}/api/dataverses/{dataverse}/actions/:publish"
        response = requests.post(url, headers=headers)
        if response.status_code == 200 or response.status_code == 201:
            print(f"{self.publishDataverse.__name__}:",
                  f"Successfully published {dataverse}")
            print(response.text)
        else:
            print(f"{self.publishDataverse.__name__}",
                  f"Failed to publish {dataverse} with status code:",
                  f"{response.status_code}",
                  f"{response.text}")

    def deleteDataverse(self, dataverse):
        dataverse = dataverse
        headers = {"X-Dataverse-key": self.token}
        url = f"{self.host}/api/dataverses/{dataverse}"
        response = requests.delete(url, headers=headers)
        if response.status_code == 200 or response.status_code == 201:
            print(f"{self.deleteDataverse.__name__}:",
                  f"Successfully deleted dataverse {dataverse}")
            print(response.text)
        else:
            print(f"{self.deleteDataverse.__name__} Failed",
                  f"to delete dataverse {dataverse} with status code:",
                  f"{response.status_code}, {response.text}")
