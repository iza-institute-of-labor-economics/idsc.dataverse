## idsc.dataverse.api

**About**

This module reads metadata and files of datasets from a dataverse ```dataverse.example1.com``` and writes them into ```~/.idsc/dataverse/api/dataverse.example1.com``` organized in directories ```PID_type/prefix/suffix```, where PID_type is one of: hdl, doi or ark. It can then ''export'' the local copy of the dataverse from ```~/.idsc/dataverse/api/dataverse.example1.com``` to ```~/.idsc/.cache/dataverse.example2.com``` so that one can upload them to ```dataverse.example2.com```. See the **migrate.MD** file for copying all datasets from one dataverse to another. It can also delete and publish datasets as well as modify the PID of a dataset for when you e.g. are not on datacite etc. It can also create, delete and publish dataverses.

The code in the *idsc.dataverse.api* was written while learning the Dataverse search and native APIs. It grew in an attempt to quickly learn how to program the API, understand dataverse itself, fix issues particular to our dataverse instance and do necessary dataverse chores aimed at shortening time to deployment. The code is in a very early stage and does not attempt a comprehensive python implementation of the various Dataverse APIs (as e.g. https://github.com/IQSS/dataverse-client-python does). It is placed here in the hope that others might need to do similar chores. 

**Basic Use**

```python
myDV = api.API("https://myDV.example.com", "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX")
myDV.getTotalCount()
pid2dataverse = myDV.getPIDs()
myDV.getMetadata("doi:10.1000/suffix")
myDV.getDatasetFiles("doi:10.1000/suffix")
etc.
```

**Create/Publish/Delete dataverse**


```python
myDV.createDataverse(name="Nikos' Repository", 
        alias="nikos", 
        dataverseContacts="nikos@iza.org,askitas@iza.org",
        affiliation = "IZA - Institute of Labor Economics",
        description = "Metadata, Data and Code repository from Nikos Askitas's",
        dataverseType = "RESEARCHERS",
        parent = "G2LM-LIC"
        
       )

myDV.publishDataverse("nikos")
myDV.deleteDataverse("nikos")

```
**Modify PID (doi, hdl, ark)**

```python
pid_old = 'doi:10.1000/suffix1'
pid_new = 'hdl:10.2000/suffix2'
myDV.modifyPID(pid_old, pid_new)

```
