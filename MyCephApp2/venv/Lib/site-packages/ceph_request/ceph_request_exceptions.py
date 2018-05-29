"""
ceph-request exceptions
~~~~~~~~~~~~~~~~~~~
This module contains the ceph-request exceptions.
"""

class CEPH_REQUEST_Exception(RuntimeError):
    """There was a unlabeled exception that was raised during your request"""

class CEPH_REQUEST_CONFIG_FILE_NOT_EXIST(CEPH_REQUEST_Exception):
    """Access was denied for the request."""

class CEPH_REQUEST_SWIFT_TYPE_CONFIG_NOT_RIGHT(CEPH_REQUEST_Exception):
    """Access was denied for the request."""


