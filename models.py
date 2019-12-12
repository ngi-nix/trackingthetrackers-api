#!/usr/bin/env python

from typing import List, Dict

from fastapi import FastAPI
from pydantic import BaseModel


""" Example response (JSON) 

{
  "uploaded_file": "/tmp/BAWAG.apk",
  "cache_hit": false,
  "md5": "1c581611eb8e2ab5d947ed481e96f59b",
  "sha1": "d69e12ba01c9373ae4da083df65466d5cafb7a25",
  "sha256": "239e856979cf26ac999a83bd94d1984a38d65a7dcc6022c83ede2f97b937d60f",
  "classification": {
    "contains_malware": false,
    "contains_trackers": true,
    "contains_adware": false
  },
  "extra": {}
}
"""


class ResponseModel(BaseModel):
    uploaded_file: str
    already_analyzed: bool
    md5: str
    sha1: str
    sha256: str
    classification: Dict[str, bool]
    extra: Dict = None
