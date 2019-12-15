"""Testing the server module
Requires:
pytest (version == 5.3.1)
pytest-asyncio (version == 0.10.0)
pytest-trio (version == 0.5.2)
pytest_tornasync (version == 0.6.0.post2)


To run tests just enter the apk-total file in terminal and run the command:
pytest -v

To run all tests in a file just add the filename:
pytest -v test_server.py

To run just a single test in a file, add "::testname" (without quotation marks), for example:
pytest -v test_server.py::test_upload_no_file_response_status
"""
import pytest
import server
from server import app
from typing import BinaryIO
from starlette.testclient import TestClient
from unittest.mock import MagicMock as Mock

client = TestClient(app)

APK_TESTFILE = "./tests/mocks/brilliant.apk"


def test_upload_no_file_response_status():
    """Test response status when no file is uploaded"""
    response = client.post("/api/v1/upload/binary/")

    # 422 = Validation Error
    assert response.status_code == 422


def test_upload_no_file_response_json():
    """Test json response when no file is uploaded"""
    response = client.post("/api/v1/upload/binary/")
    assert response.json() == {'detail': [{'loc': ['body', 'file'],
                                           'msg': 'field required',
                                           'type': 'value_error.missing'}]}


def test_upload_invalid_file_response_status():
    """Test response status when a file that is not a valid .apk file (by content_type) is uploaded"""
    f: BinaryIO

    # the file may be an actual apk file but we label the content type as not valid
    with open(APK_TESTFILE, mode='rb') as f:
        f.filename = "fake file"
        f.content_type = "not a legitimate .apk file!"
        response = client.post("/api/v1/upload/binary/", files={"file": f})

    # 400 = Error: Bad Request
    assert response.status_code == 400


def test_upload_invalid_file_response_json():
    """Test json response when a file that is not a valid .apk file (by content_type) is uploaded"""
    f: BinaryIO

    # the file may be an actual apk file but we label the content type as not valid
    with open(APK_TESTFILE, mode='rb') as f:
        f.filename = "fake file"
        f.content_type = "not a legitimate .apk file!"
        response = client.post("/api/v1/upload/binary/", files={"file": f})

    assert response.json() == {"detail": "I only accept Android APK files as input."}


def test_upload_valid_apk_file_response_status():
    f: BinaryIO

    # actual apk file, correctly labeled as apk file (by content_type)
    with open(APK_TESTFILE, mode='rb') as f:
        #f.filename = "mock apk file"
        #f.content_type = "application/vnd.android.package-archive"  # see if monkeypatching works TODO: fix

        response = client.post("/api/v1/upload/binary/",
                               files={"file": f},
                               headers={"content_type": "application/vnd.android.package-archive"})

    # 200 = successful response
    assert response.status_code == 200


def test_upload_valid_apk_file_json():
    # actual apk file, correctly labeled as apk file (by content_type)
    with open(APK_TESTFILE, mode='rb') as f:  # type f: BinaryIO
        #f.filename = "mock apk file"
        #f.content_type = "application/vnd.android.package-archive"  # see if monkeypatching works TODO: fix

        response = client.post("/api/v1/upload/binary/",
                               files={"file": f},
                               headers={"content_type": "application/vnd.android.package-archive"})

    assert response.json() == {"uploaded_file": "brilliant.apk",
                               "stored_path": "/tmp/brilliant.apk.387ea496db2bf09f42bde63e4751fdbbf977d82ae26e21fcdbc3d691a5c47f11.4984.apk",
                               "already_analyzed": "true",
                               "md5": "cc9fd9707cd830609375edfd4341ba85",
                               "sha1": "4a1a5ac1050ad08397d208eeb7ca715447f4f9dd",
                               "sha256": "387ea496db2bf09f42bde63e4751fdbbf977d82ae26e21fcdbc3d691a5c47f11",
                               "classification": {
                                   "contains_malware": "false",
                                   "contains_trackers": "false",
                                   "contains_adware": "true"
                               },
                               "extra": {}}


def test_sha256_not_in_cache():
    cached = server.is_cached("this string should NOT be in the cache/database")
    assert cached == False  # TODO: figure out why this passes when test_sha256_in_cache() throws an error


def test_sha256_in_cache():
    cached = server.is_cached("abc")  # TODO: mock database and lookup sha256 of existing entry
    assert cached == True


async def test_file_validation_success():
    mock_file = Mock()  # TODO: set up mock database and replace with call to actual file
    mock_file.content_type = "application/vnd.android.package-archive"
    is_valid = await server.initial_check_file(mock_file)
    assert is_valid == True


async def test_file_validation_failure():
    mock_file = Mock()  # TODO: set up mock database and replace with call to actual file
    mock_file.content_type = "not a valid apk file"
    with pytest.raises(server.HTTPException):
        is_valid = await server.initial_check_file(mock_file)
