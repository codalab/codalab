import re

from django.conf import settings
from django.core.files.storage import get_storage_class



StorageClass = get_storage_class(settings.DEFAULT_FILE_STORAGE)

if hasattr(settings, 'USE_AWS') and settings.USE_AWS:
    BundleStorage = StorageClass(bucket=settings.AWS_STORAGE_PRIVATE_BUCKET_NAME)
    PublicStorage = StorageClass(bucket=settings.AWS_STORAGE_BUCKET_NAME)
elif hasattr(settings, 'BUNDLE_AZURE_ACCOUNT_NAME') and settings.BUNDLE_AZURE_ACCOUNT_NAME:
    BundleStorage = StorageClass(account_name=settings.BUNDLE_AZURE_ACCOUNT_NAME,
                                 account_key=settings.BUNDLE_AZURE_ACCOUNT_KEY,
                                 azure_container=settings.BUNDLE_AZURE_CONTAINER)

    PublicStorage = StorageClass(account_name=settings.AZURE_ACCOUNT_NAME,
                                 account_key=settings.AZURE_ACCOUNT_KEY,
                                 azure_container=settings.AZURE_CONTAINER)
else:
    # No storage provided, like in a test, let's just do something basic
    BundleStorage = StorageClass()
    PublicStorage = StorageClass()


def docker_image_clean(image_name):
    # Remove all excess whitespaces on edges, split on spaces and grab the first word.
    # Wraps in double quotes so bash cannot interpret as an exec
    image_name = '"{}"'.format(image_name.strip().split(' ')[0])
    # Regex acts as a whitelist here. Only alphanumerics and the following symbols are allowed: / . : -.
    # If any not allowed are found, replaced with second argument to sub.
    image_name = re.sub('[^0-9a-zA-Z/.:-]+', '', image_name)
    return image_name
