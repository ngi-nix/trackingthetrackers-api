#!/usr/bin/env python

import hashlib
from tempfile import SpooledTemporaryFile
import logging

from fastapi import FastAPI, File, UploadFile
from fastapi import HTTPException

from malware_cache import *

app = FastAPI()
cache = FileEntryCache()

basedir = "/tmp/"


def is_malware(filename: str) -> bool:
    """
    This function returns True if the uploaded binary residing in "filename" is malware.
    False otherwise.
    @param filename:
    @return: True if malware
    """
    # XXX FIXME XXX insert the call to your function
    return False


def is_cached(sha256: str) -> bool:
    """
    This function checks if a certain file's hash is in the global cache
    @param sha256: the hash of the uploaded file
    @return: True, if it's in the cache
    """
    global cache

    return sha256 in cache


def permanently_store_file(orig_filename: str, file: SpooledTemporaryFile) -> str:
    # docs: https://docs.python.org/3/library/io.html#io.IOBase
    logging.info("storing %s ... to %s/%s" %(orig_filename, basedir, orig_filename))
    entry = FileEntry()
    cache.insert(entry)
    return file.name


def classify_apk_file(filename: str) -> bool:
    """
    This function takes the uploaded file, and sends it to the classifier.
    Returns True if we consider this a positive, False otherwise.
    """
    logging.info("classify_apk_file(): file.filename = %s" %filename)
    return is_malware(filename)


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
    return (md5, sha1, sha256)


def unzip_file(filename: str):
    # unzip it
    # XXX Implement
    pass


def extract_metadata_inf(filename: str):
    # extract METADATA.INF
    # XXX Implement
    pass


def check_file_stage2(filename: str):
    # XXX Implement
    unzip_file(filename)
    extract_metadata_inf(filename)


# ==============================================================
# main HTTP GET/POST endpoints
@app.post("/api/v1/upload/binary/")
async def upload_file(file: UploadFile = File(...)):
    # file is a SpooledTemporaryFile (see:
    # https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile) . So first write it to disk:
    initial_check_file(file)
    (md5, sha1, sha256) = await hash_file(file)
    entry = FileEntry(file.filename, md5, sha1, sha256)
    if entry in cache:
        is_positive = cache.get_cached_result(entry)
        return {'cache-hit': True, 'is_malware': is_positive}
    else:
        # XXX implement me please!
        #stored_file = permanently_store_file(entry, file.file)
        #check_file_stage2(stored_file)
        # is_positive = classify_apk_file(stored_file)
        stored_file = "/tmp/myupload.apk"
        is_positive = True
        # store_analysis(file, is_positive)      # XXX FIXME implement
    return {'uploaded_file': stored_file,
            'md5': md5,
            'sha1': sha1,
            'sha256': sha256,
            "is_malware": is_positive}

