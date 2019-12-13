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
  4. Create the (postgres) binhash database: 
```bash
sudo -u postgres
createdb bincache
createuser bincache
psql bincache
  GRANT all on database bincache to bincache;
  GRANT all on cache to bincache;
Ctrl-D
exit

cd db; psql -U binache bincache < db.sql
```

  5. Make sure the new DB is accessible:
```
  psql -U bincache bincache
  \d cache
```
You  should see the database structure.

## Running the server / the app via uvicorn

** Note**: the following section describes how to run a development server. This should not 
be run on a system which is directly available to the internet, due to the potential security 
implications. Please follow the fastapi docs on how to properly have a HTTPs proxy in front of 
uvicorn or similar ASWGI application servers.


  1. source the virtual env: ``source venv/bin/activate``
  2. Double check if the config and especially the DB username is correct in the file ``config.py``. Adapt as needed. The example above used a username "bincache" for the "bincache" database which is residing on "localhost".
  3. Start uvicorn:

```bash
uvicorn --reload --debug server:app
```

Now direct your browser to http://localhost:8000/docs. You should see the OpenAPI-generated interactive RESTful API.
Please try to upload a binary to the application.

The code which returns ``contains_malware`` is still a sample function but may be replaced by a proper call.

Try uploading a .apk file via http://localhost:8000/docs.
You should see the uploaded binary in the folder which was specified as UPLOAD_PATH in config.py




