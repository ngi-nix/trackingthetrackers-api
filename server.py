#!/usr/bin/env python

# system imports
import hashlib
import shutil
from tempfile import SpooledTemporaryFile
import random
import os

# FastAPI framework imports
from fastapi import FastAPI, File, UploadFile
from fastapi import HTTPException

# local imports
from malware_cache import *
from models import ResponseModel
from config import config

app = FastAPI()
cache = FileEntryCache()


def contains_malware(filename: str) -> bool:
    """
    This function returns True if the uploaded binary residing in "filename" is malware.
    False otherwise.
    @param filename:
    @return: True if malware
    """
    # XXX FIXME XXX insert the call to your function
    return random.random() > 0.5


def contains_trackers(filename: str) -> bool:
    # XXX FIXME XXX insert the call to your function
    return random.random() > 0.5


def contains_adware(filename: str) -> bool:
    # XXX FIXME XXX insert the call to your function
    return random.random() > 0.5


def is_cached(sha256: str) -> bool:
    """
    This function checks if a certain file's hash is in the global cache
    @param sha256: the hash of the uploaded file
    @return: True, if it's in the cache
    """
    global cache
    return sha256 in cache


def store_file(orig_filename: str, file: SpooledTemporaryFile, path_prefix=config['UPLOAD_PATH'], prefix="", suffix="") -> str:
    """
    Stores a SpooledTemporaryFile to a permanent location and returns the path to it
    @param orig_filename:  the APK filename
    @param file: the SpooledTemporary File
    @return: full path to the stored file
    """
    # Unfortunately we need to really shutil.copyfileobj() the file object to disk, even though we already have a
    # SpooledTemporaryFile object... this is needed for SpooledTemporaryFiles . Sucks. See here:
    #   https://stackoverflow.com/questions/94153/how-do-i-persist-to-disk-a-temporary-file-using-python
    #
    # filepath syntax:  <UPLOAD_PATH>/<prefix><original filename>.sha1.pid<suffix>
    #   example: /tmp/BAWAG.apk.
    pid=os.getpid()
    path = "{}/{}{}{}".format(path_prefix, prefix, orig_filename, suffix)
    logging.info("storing %s ... to %s" %(orig_filename, path))
    file.seek(0)
    with open(path, "w+b") as outfile:
       shutil.copyfileobj(file._file, outfile)
    return path


def classify_apk_file(filename: str, mode="malware") -> bool:
    """
    This function takes the uploaded file, and sends it to the classifier(s).
    Returns True if we consider this a positive, False otherwise.
    """
    logging.info("classify_apk_file(): file.filename = %s" %filename)
    if mode=="malware":
        return contains_malware(filename)
    elif mode=="trackers":
        return contains_trackers(filename)
    elif mode=="adware":
        return contains_adware(filename)


def initial_check_file(file: UploadFile) -> bool:
    """
    Do an initial check of the file. All checks which can be done before
    it gets sent to the classifier should be run.
    @param file: the uploaded file
    @return: True on success. Exception on failure
    """
    if file.content_type != "application/vnd.android.package-archive":
        raise HTTPException(status_code=400, detail="I only accept Android APK files as input.")
    return True


def stage2_check_file(filename: str):
    # XXX FIXME Implement if needed
    unzip_file(filename)
    extract_metadata_inf(filename)


# ==============================================================
# helper functions
async def hash_file(file: UploadFile) -> (str, str, str):
    """ Hash the file. Returns a triplet tuple: (md5, sha1, sha256)
    @param file: the uploaded file
    @return: tuple: (md5, sha1, sha256)
    """

    logging.info("hashing file %s" %file.file.name)
    BLOCKSIZE = 65536
    hasher_md5 = hashlib.md5()
    hasher_sha1 = hashlib.sha1()
    hasher_sha256 = hashlib.sha256()
    await file.seek(0)
    buf = await file.read(BLOCKSIZE)
    logging.debug("buf = %r" %(buf,))
    while len(buf) > 0:
        hasher_md5.update(buf)
        hasher_sha1.update(buf)
        hasher_sha256.update(buf)
        buf = await file.read(BLOCKSIZE)
    md5 = hasher_md5.hexdigest()
    sha1 = hasher_sha1.hexdigest()
    sha256 = hasher_sha256.hexdigest()
    logging.info("hashes %s / %s / %s" % (md5, sha1, sha256))
    BLOCKSIZE = 65536
    return (md5, sha1, sha256)


def unzip_file(filename: str):
    # unzip it
    # XXX Implement
    pass


def extract_metadata_inf(filename: str):
    # extract METADATA.INF
    # XXX Implement
    pass


# ==============================================================
# main HTTP GET/POST endpoints
@app.post("/api/v1/upload/binary/", response_model=ResponseModel)
async def upload_file(file: UploadFile = File(...)):
    # file is a SpooledTemporaryFile (see:
    # https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile) . So first write it to disk:
    initial_check_file(file)
    (md5, sha1, sha256) = await hash_file(file)
    tmp_file_on_disk = store_file(file.filename, file.file)    # This dumps the file to disk and returns a Path
    stage2_check_file(tmp_file_on_disk)                 # XXX FIXME. Additional checks on the dumped file still missing
    entry = FileEntry(file.filename, path=tmp_file_on_disk, md5=md5, sha1=sha1, sha256=sha256,
                      contains_malware=None, contains_trackers=None, contains_adware=None)
    print(str(entry))
    response_dict = {'uploaded_file': entry.path,
                     'already_analyzed': None,
                     'md5': entry.md5,
                     'sha1': entry.sha1,
                     'sha256': entry.sha256,
                     'classification': {},
                     'extra': {},
                    }
    if entry in cache:
        response_dict['classification']['contains_malware'] = cache.contains_malware(entry)
        # response_dict['classification']['contains_trackers'] = cache.contains_trackers(entry)
        # response_dict['classification']['contains_adware'] = cache.contains_adware(entry)
        response_dict['already_analyzed'] = True
    else:
        entry.contains_malware = classify_apk_file(tmp_file_on_disk, mode="malware")
        entry.contains_trackers = classify_apk_file(tmp_file_on_disk, mode="trackers")
        entry.contains_adware = classify_apk_file(tmp_file_on_disk, mode="adware")
        cache.insert(entry)
        response_dict['already_analyzed']: False
        response_dict['classification']['contains_malware'] = entry.contains_malware
        response_dict['classification']['contains_trackers'] = entry.contains_trackers
        response_dict['classification']['contains_adware'] = entry.contains_adware
    return response_dict
