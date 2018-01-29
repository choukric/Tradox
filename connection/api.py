import base64
import hashlib
import hmac
import json
import time
import urllib

import connection

URI = 'https://api.kraken.com'
API_VERSION = '0'
KEY = ''
SECRET = ''
LAST_QUERY_TIMESTAMP = 0
TIME_BETWEEN_QUERIES = 3
KEY_FILE = '../kraken.key'


def init(path):
    with open(path, "r") as f:
        global KEY
        global SECRET
        key = f.readline().strip()
        secret = f.readline().strip()
        KEY = key
        SECRET = secret


def _query(urlpath,l=None, req = {}, conn = None, headers = {}):
    """Low-level query handling.
    
    Arguments:
    urlpath -- API URL path sans host (string, no default)
    req     -- additional API reque st parameters (default: {})
    conn    -- kraken.Connection object (default: None)
    headers -- HTTPS headers (default: {})
    
    """
    ret = None
    try:
        if l is not None:
            l.acquire()
        global LAST_QUERY_TIMESTAMP
        time_since_last = time.time() - LAST_QUERY_TIMESTAMP
        if time_since_last < TIME_BETWEEN_QUERIES :
            time.sleep(TIME_BETWEEN_QUERIES - time_since_last + 0.5)

        url = URI + urlpath

        if conn is None:
            conn = connection.Connection()

        LAST_QUERY_TIMESTAMP = time.time()
        ret = conn.request(url, req, headers)
    finally:
        if l is not None:
            l.release()
        try:
            return json.loads(ret)
        except TypeError:
            return None


def query_public(method, l=None,req = {}, conn = None):
    """API queries that do not require a valid key/secret pair.
    
    Arguments:
    method -- API method name (string, no default)
    req    -- additional API request parameters (default: {})
    conn   -- connection object to reuse (default: None)
    
    """
    urlpath = '/' + API_VERSION + '/public/' + method
    return _query(urlpath, l,req, conn)


def query_private(method, req={},conn = None):
    """API queries that require a valid key/secret pair.
    
    Arguments:
    method -- API method name (string, no default)
    req    -- additional API request parameters (default: {})
    conn   -- connection object to reuse (default: None)
    
    """

    if KEY == '':
        init(KEY_FILE)

    urlpath = '/' + API_VERSION + '/private/' + method

    req['nonce'] = int(1000*time.time())
    postdata = urllib.urlencode(req)
    message = urlpath + hashlib.sha256(str(req['nonce']) +
                                       postdata).digest()
    signature = hmac.new(base64.b64decode(SECRET),
                         message, hashlib.sha512)
    headers = {
        'API-Key': KEY,
        'API-Sign': base64.b64encode(signature.digest())
    }

    return _query(urlpath, req, conn, headers)
