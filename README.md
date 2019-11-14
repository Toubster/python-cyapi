# Summary

This Library provides python bindings to interact with the Cylance API. Examples have been created for you in the Examples/ directory, and provide a majority of the common code you'll need to get setup. In order to utilize this Library, you will need an API token from the API Integrations tab inside of the Cylance Console.

# Installation

```
python setup.py install
```

# Example

This example will create a connection to the API and return all devices that have registered.

```
from cyapi.cyapi import CyAPI
API = CyAPI(tid=your_id, aid=your_aid, ase=your_ase)
API.create_conn()
API.get_devices()
```

Additionally you can copy examples/simple_setup.py to your_new_file.py and begin hacking away from there.

# Creds File

You can create a file that will store your api credentials instead of passing them in via the command line. The creds file should look like the following:

creds.json:
```
{
    "tid": "123456-55555-66666-888888888",
    "app_id": "11111111-222222-33333-44444444",
    "app_secret": "555555-666666-222222-444444",
    "region": "NA"
}
```

This file can then be passed in by passing -c path/to/creds.json
