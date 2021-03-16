"""
Common utilities to interact with Azure Storage.
"""

import datetime
import os.path
import re
import itertools

from django.conf import settings
from django.core.files.storage import Storage
from django.core.exceptions import ImproperlyConfigured
from io import RawIOBase

# keep consistent path separators
pathjoin = lambda *args: os.path.join(*args).replace("\\", "/")

try:
    import azure
    import azure.storage

    from azure.storage import (
        AccessPolicy,
        BlobService,
        SharedAccessPolicy,
        SharedAccessSignature,
        StorageServiceProperties,
    )

except ImportError:
    raise ImproperlyConfigured(
        "Could not load Azure bindings. "
        "See https://github.com/WindowsAzure/azure-sdk-for-python")

from storages.utils import setting


def clean_name(name):
    return os.path.normpath(name).replace("\\", "/")


class AzureStorage(Storage):
    chunk_size = 65536

    def __init__(self, *args, **kwargs):
        self.account_name = kwargs.pop('account_name', setting("AZURE_ACCOUNT_NAME"))
        self.account_key = kwargs.pop('account_key', setting("AZURE_ACCOUNT_KEY"))
        self.azure_container = kwargs.pop('azure_container', setting("AZURE_CONTAINER"))
        super(AzureStorage, self).__init__(*args, **kwargs)
        self._connection = None

    @property
    def connection(self):
        if self._connection is None:
            self._connection = azure.storage.BlobService(
                self.account_name,
                self.account_key,
                timeout=4096
            )
        return self._connection

    def _open(self, name, mode="rb"):
        return AzureBlockBlobFile(self.connection, self.azure_container, name, mode)

    def exists(self, name):
        try:
            p = self.properties(name)
        except azure.WindowsAzureMissingResourceError:
            return False
        else:
            return True

    def delete(self, name):
        self.connection.delete_blob(self.azure_container, name)

    def _save(self, name, content):
        f = self._open(name, 'wb')
        cur = 0
        while True:
            data = content.read(self.chunk_size)
            if not len(data): break
            f.write(data)
        f.close()
        return name

    def url(self, name):
        return "https://%s%s/%s/%s" % (self.account_name, settings.AZURE_BLOB_SERVICE_HOST_BASE or azure.BLOB_SERVICE_HOST_BASE, self.azure_container, name)

    def properties(self, name):
        return self.connection.get_blob_properties(
            self.azure_container, name)

    def size(self, name):
        return self.properties(name)["content-length"]

    def get_available_name(self, name, max_length=None):
        dir_path, file_name = os.path.split(name)
        name = clean_name(name)
        try:
            file_root, file_ext = re.match('^([^\.\s]+)(\.\S+)$', file_name).groups()
        except AttributeError:
            file_root, file_ext = (file_name, '')
        path_prefix = pathjoin(dir_path, file_root)
        file_list = {f.name: True for f in self.connection.list_blobs(self.azure_container, path_prefix)}
        ct = itertools.count(1)
        while name in file_list:
            name = path_prefix + "_%s%s" % (next(ct), file_ext)
        return name


class AzureBlockBlobFile(RawIOBase):

    def __init__(self, connection, container, name, mode):
        name = clean_name(name)
        self.connection = connection
        self.name = name
        self.container = container
        self.mode = mode
        self._properties = None
        if 'w' in mode:
            try:
                self.properties
                if 'a' not in mode:
                    raise Exception("File Already Exists.")
            except azure.WindowsAzureMissingResourceError as e:
                res = self.connection.put_blob(self.container, self.name, b'', "BlockBlob")
        self._cur = 0
        self._end = (int(self.properties['content-length']) - 1) if int(self.properties['content-length']) > 0 else 0
        self._block_list = []

    @property
    def properties(self):
        if self._properties is None:
            self._properties = self.connection.get_blob_properties(self.container, self.name)
        return self._properties

    @property
    def size(self):
        return int(self.properties.get('content-length'))

    def seek(self, offset, from_what=0):
        if from_what == 2:
            pos = int(offset) + (self.size - 1)
        elif from_what == 1:
            pos = self._cur + int(offset)
        else:
            pos = int(offset)
        self.flush()
        if pos > self._end:
            raise Exception("Cannot seek past end of file")
        self._cur = pos

    def tell(self):
        return self._cur

    def read(self, num_bytes=None):
        start = self._cur
        if not num_bytes:
            end = self.size -1
        else:
            end = self._cur+num_bytes-1
        if self._cur > self._end:
            raise Exception("Something odd happened.")
        if self._cur == self._end and not num_bytes:
            return None
        if self._end < end:
            end = self._end
        content = self.connection.get_blob(self.container,
                                           self.name,
                                           x_ms_range='bytes=%d-%d' % (start, end))
        self._cur = self._cur + len(content) if self._cur < self._end else self._end
        return content

    def write(self, data):
        blockid = "%6d" % len(self._block_list)
        try:
            self.connection.put_block(self.container, self.name, data, blockid)
            self._block_list.append((blockid, len(data)))
            return len(data)
        except azure.WindowsAzureError as e:
            raise e

    def flush(self):
        if self._block_list:
            self.connection.put_block_list(self.container, self.name, [b[0] for b in self._block_list])
            self._end = sum([b[1] for b in self._block_list]) - 1
            self._cur = 0
            self._block_list = []

    def close(self):
        self.flush()

PREFERRED_STORAGE_X_MS_VERSION = '2013-08-15'


def make_blob_sas_url(account_name,
                      account_key,
                      container_name,
                      blob_name,
                      permission='w',
                      duration=16):
    """
    Generate a Blob SAS URL to allow a client to upload a file.

    account_name: Storage account name.
    account_key: Storage account key.
    container_name: Storage container.
    blob_name: Blob name.
    duration: A timedelta representing duration until SAS expiration.
       SAS start date will be utcnow() minus one minute. Expiry date
       is start date plus duration.

    Returns the SAS URL.
    """
    sas = SharedAccessSignature(account_name, account_key)
    resource_path = '%s/%s' % (container_name, blob_name)
    date_format = "%Y-%m-%dT%H:%M:%SZ"
    start = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    expiry = start + datetime.timedelta(minutes=duration)
    sap = SharedAccessPolicy(AccessPolicy(
            start.strftime(date_format),
            expiry.strftime(date_format),
            permission))
    sas_token = sas.generate_signed_query_string(resource_path, 'b', sap)

    blob_url = BlobService(account_name, account_key)

    url = blob_url.make_blob_url(container_name=container_name, blob_name=blob_name, sas_token=sas_token)

    return url
