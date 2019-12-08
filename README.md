# web-submit
Simple [fastapi](https://fastapi.tiangolo.com/) based web server for submitting APK files and getting them analysed. 
This app uses a small PostgreSQL DB to cache already analysed results.

Author: [aaron kaplan](https://github.com/aaronkaplan)


# How to run this program?

## DB initialisation & preparation steps

**Note**: these instructions assume python 3.7 or higher.

  1. Create a virtual env: ``virtualenv venv``
  2. Install the requirements: ``pip install -r requirements.txt``
  3. Install PostgreSQL if needed according to your OS recommendations
  4. Create the (postgres) binhash database: ``cd db; createdb bincache; psql bincache < db.sql``
  5. Make sure the new DB is accessible:
```
  psql bincache
  \d cache
```

## Running the server / the app via uvicorn

** Note**: the following section describes how to run a development server. This should not 
be run on a system which is directly available to the internet, due to the potential security 
implications. Please follow the fastapi docs on how to properly have a HTTPs proxy in front of 
uvicorn or similar ASWGI application servers.


  1. source the virtual env: ``source venv/bin/activate``
  2. Double check if the config and especially the DB username is correct in the file ``config.py``. Adapt as needed.
  3. Start uvicorn:

```bash
uvicorn --reload --debug server:app
```

Now direct your browser to http://localhost:8000/docs. You should see the OpenAPI-generated interactive RESTful API.
Please try to upload a binary to the application.

The code which returns ``is_malware`` is still a sample function but may be replaced by a proper call.

