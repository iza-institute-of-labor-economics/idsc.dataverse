### Migrate from one Dataverse to another

**Setup**

Keep your credentials in files (e.g. in the same folder as this code) .env.demo1 and .env.demo2 which might look like this:

```
baseURL=https://Demo1 Instance URL 
myKey=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
```

```
baseURL=https://Demo2 Instance URL 
myKey=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
```

**Load your credentials in a dictionary**


```python
from dotenv import dotenv_values
config = {
    "demo1":{**dotenv_values(".env.demo1")},  
    "demo2": {**dotenv_values(".env.demo2")}
}

print(json.dumps(config,indent=4))

```

    {
        "demo1": {
            "baseURL": "https://demo1 url",
            "myKey": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
        },
        "demo2": {
            "baseURL": "https://demo2 url",
            "myKey": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
        }
    }


**Instantiate the API class for each Dataverse instance**


```python
from idsc.dataverse import api
dv1 = api.API(config["demo1"]["baseURL"], config["demo1"]["myKey"])
dv2 = api.API(config["demo2"]["baseURL"], config["demo2"]["myKey"])

#e.g.
print("Demo1 Count", dv1.getTotalCount())
print("Demo2 Count", dv2.getTotalCount())
```

**List Dataverse**


```python
print("Demo1 Listing")
print(json.dumps(dv1.getDVList(),indent=4))
```


**Make a dictionary of PIDs of datasets and their respective dataverse**


```python
import json
pid2dataverse = dv1.getPIDs()
print(f"pid2dataverse ({dv1.host}) = \n", json.dumps(pid2dataverse,indent=4))
```

**Get all dataset of Demo1**


```python
pid2dataverse = dv1.getPIDs()
for pid in pid2dataverse.keys():
    dv1.getMetadata(pid)
    dv1.getDatasetFiles(pid)
    
```

**Export datasets from Demo1 for ingesting them into Demo2**

```python
dv1.exportDataFor("https://Demo2 Instance URL")
```

**Reset Demo2 (optional)**


```python
pid2dataverse_dv2 = dv2.getPIDs()
for pid in pid2dataverse_dv2.keys():
    dv2.deleteDataset(pid)
```

 
**Upload Demo1 to Demo2 and publish**


```python
import os
for pid, dataverse in pid2dataverse.items():

    print("---------------------------")
    print("Creating ",pid)
    
    dv2.createDataset(pid,dataverse)
    dv2.uploadFiles(pid)
    dv2.publishDataset(pid)
  
```

    ---------------------------
    Creating  doi:10.15185/suffix.1.1
    publishDataset: Request was successful.
    publishDataset : {"status":"OK",...}
    ---------------------------
    Creating  doi:10.15185/suffix.1.2
    publishDataset: Request was successful.
    publishDataset : {"status":"OK",...}
    ...
    ---------------------------
    Creating  doi:10.15185/suffix.1.n
    publishDataset: Request was successful.
    publishDataset : {"status":"OK",...}
