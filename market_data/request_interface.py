from custom_exceptions import KrakenPublicException, KrakenPrivateException
import sys
import time
from connection import api as k
 
__getframe_expr = 'sys._getframe({}).f_code.co_name'


def get_private_result_or_none(uri, req={}):
    try:
        return private_request(uri, req=req)
    except KrakenPrivateException as error:
        print(error)
        return None


def get_public_result_for_pair(uri, pair, l=None, since = None):
    try:
        if since is None:
            req = {'pair': pair}
        else:
            req = {'pair': pair,
                   'since': since}
        return public_request(uri,l=l, req=req)
    except KrakenPublicException as error:
        raise KrakenPublicException(error.message)


def get_public_result_for_pair_or_none(uri, pair, since = None):
    try:
        if since is None:
            req = {'pair': pair}
        else:
            req = {'pair': pair,
                   'since': since}
        return public_request(uri, req)
    except KrakenPublicException as error:
        return None


def public_request(uri, l=None, req= {}):
    caller = eval(__getframe_expr.format(2))
    try:
        d = k.query_public(uri, l=l, req=req)
        if d is None:
            raise KrakenPublicException('Error executing %s : None' % caller)
        err = d['error']
        if not len(err):
            return d['result']
        else:
            raise KrakenPublicException('Error executing %s : %s' % (caller, ', '.join(err)))
    except ValueError as error:
        raise KrakenPublicException('Error executing %s : %s' % (caller, repr(error)))


def private_request(uri, req={}):
    caller = eval(__getframe_expr.format(2))
    try:
        d = k.query_private(uri, req=req)
        if d is None:
            raise KrakenPrivateException('Error executing %s : %s' % (caller, ', '.join('None')))
        err = d['error']
        if not len(err):
            return d['result']
        else:
            raise KrakenPrivateException('Error executing %s : %s' % (caller, ', '.join(err)))
    except ValueError as error:
        raise KrakenPrivateException('Error executing %s : %s' % (caller, repr(error)))
    except TypeError as error:
        raise KrakenPrivateException('Error executing %s : %s' % (caller, repr(error)))