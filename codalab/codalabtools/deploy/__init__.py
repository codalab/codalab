"""
Provides tools to deploy CodaLab.
"""
import logging
import logging.config
import os
import sys

# Add codalabtools to the module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from codalabtools import BaseConfig

logger = logging.getLogger('codalabtools')


class DeploymentConfig(BaseConfig):
    """
    Defines credentials and configuration values needed to deploy CodaLab.
    .codalabconfig is the YAML file being passed from codalab-deployment repo which
    is sitting in Bitbucket

    """
    def __init__(self, label=None, filename='.codalabconfig'):
        super(DeploymentConfig, self).__init__(filename)

        self.label = label
        self._dinfo = self.info['deployment']
        self._azure_mgmt_info = self._dinfo['azure-management']
        self._svc_global = self._dinfo['service-global']
        self._svc = self._dinfo['service-configurations'][label] if label is not None else {}
        self.new_relic_key = self._dinfo['new-relic-key']

    @staticmethod
    def _cap(word):
        """
        Returns a capitalized word.
        """
        return word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()

    def getNewRelicKey(self):
        """
        Get the new relic key.
        """
        return self.new_relic_key

    def getLoggerDictConfig(self):
        """Gets Dict config for logging configuration."""
        if 'logging' in self._dinfo:
            return self._dinfo['logging']
        else:
            return super(DeploymentConfig, self).getLoggerDictConfig()

    def getAzureSubscriptionId(self):
        """Gets the Azure Subscription ID."""
        return self._azure_mgmt_info['subscription-id']

    def getAzureCertificatePath(self):
        """Gets the path for the Azure Service Management certificate."""
        return self._azure_mgmt_info['certificate-path']

    def getAzureOperationTimeout(self):
        """
        Gets a duration (in seconds) to limit the time spent waiting for the completion
        of a long running operation in Azure.
        """
        return self._azure_mgmt_info['operation-timeout']

    def getServiceLocation(self):
        """Gets the name of the Azure region in which services will be deployed."""
        return self._svc_global['location']

    def getServicePrefix(self):
        """Gets the unique prefix used to build the name of services and other resources."""
        return self._svc_global['prefix']

    def getAffinityGroupName(self):
        """Gets the name of the affinity group used to co-locate services."""
        return "{0}location".format(self.getServicePrefix())

    # Stuff related to service-global
    def getServiceCertificateThumbprint(self):
        """Gets the thumbprint for the service certificate."""
        return self._svc_global['certificate']['thumbprint']

    def getServiceCertificateFilename(self):
        """Gets the local path of the file holding the service certificate."""
        return self._svc_global['certificate']['filename']

    def getServiceCertificateKeyFilename(self):
        """Gets the local path of the file holding the service certificate key."""
        return self._svc_global['certificate']['key-filename']

    def getServiceCertificateFormat(self):
        """Gets the format of the service certificate."""
        return self._svc_global['certificate']['format']

    def getServiceCertificatePassword(self):
        """Gets the password for the service certificate."""
        return self._svc_global['certificate']['password']

    def getVirtualMachineLogonUsername(self):
        """Gets the username to log into a virtual machine of the service deployment."""
        return self._svc_global['vm']['username']

    def getVirtualMachineLogonPassword(self):
        """Gets the password to log into a virtual machine of the service deployment."""
        return self._svc_global['vm']['password']

    def getEmailHost(self):
        """Gets the host for the e-mail service."""
        return self._svc_global['e-mail']['host']

    def getEmailUser(self):
        """Gets the username for the e-mail service."""
        return self._svc_global['e-mail']['user']

    def getEmailPassword(self):
        """Gets the password for the e-mail service."""
        return self._svc_global['e-mail']['password']

    # Configuration related to different Azure services
    def getServiceName(self):
        """Gets the cloud service name. It will return something <codalabtest> or <codalabprod>"""
        return "{0}{1}".format(self.getServicePrefix(), self.label)

    def getServiceOSImageName(self):
        """Gets the name of the OS image used to create virtual machines in the service deployment."""
        return self._svc['vm']['os-image']

    def getServiceInstanceCount(self):
        """Gets the number of virtual machines to create in the service deployment."""
        return self._svc['vm']['count']

    def getServiceInstanceRoleSize(self):
        """Gets the role size for each virtual machine in the service deployment."""
        return self._svc['vm']['role-size']

    def getServiceInstanceSshPort(self):
        """Gets the base SSH port value. If this value is N, the k-th web instance will have SSH port number (N+k)."""
        return self._svc['vm']['ssh-port']

    def get_broker_url(self):
        return self._svc['broker-url']

    def get_CELERY_DEFAULT_ROUTING_KEY(self):
        return self._svc['broker-routing-key']

    def getGitUser(self):
        """Gets the name of the Git user associated with the target source code repository."""
        return self._svc['git']['user']

    def getGitRepo(self):
        """Gets the name of the Git of the target source code repository."""
        return self._svc['git']['repo']

    def getGitTag(self):
        """Gets the Git tag defining the specific version of the source code."""
        return self._svc['git']['tag']

    def getDjangoConfiguration(self):
        """Gets the name of the Django configuration."""
        return self._svc['django']['configuration']

    def getDjangoSecretKey(self):
        """Gets the value of the Django secret key."""
        return self._svc['django']['secret-key']

    def getAdminEmail(self):
        """Gets the database engine type."""
        return self._svc['django']['admin-email']

    def getDatabaseEngine(self):
        """Gets the database engine type."""
        return self._svc['database']['engine']

    def getDatabaseName(self):
        """Gets the Django site database name."""
        return self._svc['database']['name']

    def getDatabaseUser(self):
        """Gets the database username."""
        return self._svc['database']['user']

    def getDatabasePassword(self):
        """Gets the password for the database user."""
        return self._svc['database']['password']

    def getDatabaseHost(self):
        """Gets the database host."""
        return self._svc['database']['host']

    def getDatabasePort(self):
        """Gets the database port."""
        return self._svc['database']['port']

    def getDatabaseAdminPassword(self):
        """Gets the password for the database admin."""
        return self._svc['database']['admin_password']

    def getUseAWS(self):
        """Gets the service cloud storage account name."""
        return self._svc['storage'].get('storage-class') == 'storages.backends.s3boto3.S3BotoStorage'

    def getFileStorageClass(self):
        """Gets the service cloud storage account name."""
        return self._svc['storage'].get('storage-class', 'codalab.azure_storage.AzureStorage')

    def getServiceStorageAccountName(self):
        """Gets the service cloud storage account name."""
        return self._svc['storage'].get('storage-account-name')

    def get_service_storage_account_key(self):
        """Gets the storage account key."""
        return self._svc['storage'].get('storage-account-key')

    def getServiceCertificateAlgorithm(self):
        """Gets the algorithm for the service certificate."""
        return self._svc_global['certificate']['algorithm']

    def getServicePublicStorageContainer(self):
        """Gets the name of the public Blob container for the service."""
        return self._svc['storage'].get('public-container')

    def getServiceBundleStorageContainer(self):
        """Gets the name of the bundle Blob container for the service."""
        return self._svc['storage'].get('bundles-container')

    def getServiceStorageCorsAllowedOrigins(self):
        """Gets the comma-separated list of allowed hosts for CORS with Windows Azure storage service."""
        return self._svc['storage']['cors-allowed-origins'] if 'cors-allowed-origins' in self._svc['storage'] else '*'

    def getServiceBusNamespace(self):
        """Gets the namespace for the service bus."""
        return self._svc['bus']['namespace']

    def get_service_bus_key(self):
        """
        Gets the key for the service bus
        """
        return self._svc['bus']['bus-service-account-key'] if 'bus-service-account-key' in self._svc['bus'] else ''

    def get_service_bus_shared_access_key_name(self):
        """Gets the SAS shared access key name"""
        return self._svc['bus']['shared-access-key-name'] if 'shared-access-key-name' in  self._svc['bus'] else ''

    def get_service_bus_shared_access_key_value(self):
        """Gets the SAS shared access key value"""
        return self._svc['bus']['shared-access-key-value'] if 'shared-access-key-name' in self._svc['bus'] else ''

    def getSslCertificatePath(self):
        """Gets the path of the SSL certificate file to install."""
        return self._svc['ssl']['filename'] if 'ssl' in self._svc else ""

    def getSslCertificateKeyPath(self):
        """Gets the path of the SSL certificate key file to install."""
        return self._svc['ssl']['key-filename'] if 'ssl' in self._svc else ""

    def getSslCertificateInstalledPath(self):
        """Gets the path of the installed SSL certificate file."""
        if len(self.getSslCertificatePath()) > 0:
            return "/etc/ssl/certs/%s" % os.path.basename(self.getSslCertificatePath())
        else:
            return ""

    def getSslCertificateKeyInstalledPath(self):
        """Gets the path of the installed SSL certificate key file."""
        if len(self.getSslCertificateKeyPath()) > 0:
            return "/etc/ssl/private/%s" % os.path.basename(self.getSslCertificateKeyPath())
        else:
            return ""

    def getSslRewriteHosts(self):
        """Gets the list of hosts for which HTTP requests are automatically re-written as HTTPS requests."""
        if 'ssl' in self._svc and 'rewrite-hosts' in self._svc['ssl']:
            return self._svc['ssl']['rewrite-hosts']
        return []

    def getWebHostnames(self):
        """
        Gets the list of web instances. Each name in the list if of the form '<service-name>.cloudapp.net:<port>'.
        """
        service_name = self.getServiceName()  # e.g., codalab
        vm_numbers = list(range(1, 1 + self.getServiceInstanceCount()))  # e.g., prod
        ssh_port = self.getServiceInstanceSshPort()
        return ['{0}.cloudapp.net:{1}'.format(service_name, str(ssh_port + vm_number)) for vm_number in vm_numbers]

    def get_compute_worker_logs_password(self):
        """
        Get that password that will allow to see the logs
        """
        return self._svc_global['compute-worker']['misc']['logs-password']


class Deployment(object):
    """
    Helper class to handle deployment of the web site.
    """
    def __init__(self, config):
        self.config = config

    def getSettingsFileContent(self):
        """
        Generates the content of the local Django settings file.
        Modified only if you know what you doing
        """
        # Use the same allowed hosts for SSL and not SSL
        allowed_hosts = ssl_allowed_hosts = \
            self.config.getSslRewriteHosts() + \
            ['{0}.cloudapp.net'.format(self.config.getServiceName())]

        lines = [
            "# THIS FILE IS AUTO-GENERATED - DON'T EDIT!",
            "from base import Base",
            "from default import *",
            "from configurations import Settings",
            "",
            "import sys",
            "from os.path import dirname, abspath, join",
            "from pkgutil import extend_path",
            "import codalab",
            "import uuid",
            "",
            "class {0}(Base):".format(self.config.getDjangoConfiguration()),
            "",
            "    DEBUG = False",
            "",
            "    ALLOWED_HOSTS = {0}".format(allowed_hosts),
            "",
            "    SSL_PORT = '443'",
            "    SSL_CERTIFICATE = '{0}'".format(self.config.getSslCertificateInstalledPath()),
            "    SSL_CERTIFICATE_KEY = '{0}'".format(self.config.getSslCertificateKeyInstalledPath()),
            "    SSL_ALLOWED_HOSTS = {0}".format(ssl_allowed_hosts),
            "",

            "    DEFAULT_FILE_STORAGE = '{0}'".format(self.config.getFileStorageClass()),

            # AWS
            '    USE_AWS = {0}'.format(self.config.getUseAWS()),
            '    AWS_ACCESS_KEY_ID = "{0}"'.format(self.config._svc['storage'].get('AWS_ACCESS_KEY_ID')),
            '    AWS_SECRET_ACCESS_KEY = "{0}"'.format(self.config._svc['storage'].get('AWS_SECRET_ACCESS_KEY')),
            '    AWS_STORAGE_BUCKET_NAME = "{0}"'.format(self.config._svc['storage'].get('AWS_STORAGE_BUCKET_NAME')),
            '    AWS_STORAGE_PRIVATE_BUCKET_NAME = "{0}"'.format(self.config._svc['storage'].get('AWS_STORAGE_PRIVATE_BUCKET_NAME')),
            '    AWS_S3_CALLING_FORMAT = "boto.s3.connection.OrdinaryCallingFormat"',
            '    AWS_S3_HOST = "s3-us-west-2.amazonaws.com"',
            '    AWS_QUERYSTRING_AUTH = False  # This stops signature/auths from appearing in saved URLs',

            # S3Direct (S3 uploads)
            "    S3DIRECT_REGION = 'us-west-2'",
            "    S3DIRECT_DESTINATIONS = {",
            "        'competitions': {",
            "            'key': lambda f: 'uploads/competitions/{}/competition.zip'.format(uuid.uuid4()),",
            "            'auth': lambda u: u.is_authenticated(),",
            "            'bucket': AWS_STORAGE_PRIVATE_BUCKET_NAME,",
            "        },",
            "        'submissions': {",
            "            'key': lambda f: 'uploads/submissions/{}/submission.zip'.format(uuid.uuid4()),",
            "            'auth': lambda u: u.is_authenticated(),",
            "            'bucket': AWS_STORAGE_PRIVATE_BUCKET_NAME,",
            "        }",
            "    }",

            # Azure
            "    AZURE_ACCOUNT_NAME = '{0}'".format(self.config.getServiceStorageAccountName()),
            "    AZURE_ACCOUNT_KEY = '{0}'".format(self.config.get_service_storage_account_key()),
            "    AZURE_CONTAINER = '{0}'".format(self.config.getServicePublicStorageContainer()),
            "    BUNDLE_AZURE_ACCOUNT_NAME = AZURE_ACCOUNT_NAME",
            "    BUNDLE_AZURE_ACCOUNT_KEY = AZURE_ACCOUNT_KEY",
            "    BUNDLE_AZURE_CONTAINER = '{0}'".format(self.config.getServiceBundleStorageContainer()),
            "",
            "    SBS_NAMESPACE = '{0}'".format(self.config.getServiceBusNamespace()),
            "    SBS_ISSUER = 'owner'",
            "    SBS_ACCOUNT_KEY = '{0}'".format(self.config.get_service_bus_key()),
            "    SBS_SHARED_ACCESS_KEY_NAME = '{0}'".format(self.config.get_service_bus_shared_access_key_name()),
            "    SBS_SHARED_ACCESS_KEY_VALUE = '{0}'".format(self.config.get_service_bus_shared_access_key_value()),
            "    SBS_RESPONSE_QUEUE = 'jobresponsequeue'",
            "    SBS_COMPUTE_QUEUE = 'windowscomputequeue'",
            "",
            "    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'",
            "    EMAIL_HOST = '{0}'".format(self.config.getEmailHost()),
            "    EMAIL_HOST_USER = '{0}'".format(self.config.getEmailUser()),
            "    EMAIL_HOST_PASSWORD = '{0}'".format(self.config.getEmailPassword()),
            "    EMAIL_PORT = 587",
            "    EMAIL_USE_TLS = True",
            "    DEFAULT_FROM_EMAIL = 'CodaLab <info@codalab.org>'",
            "    SERVER_EMAIL = 'info@codalab.org'",
            "",
            "    BROKER_URL = '{0}'".format(self.config.get_broker_url()),
            # "    CELERY_DEFAULT_ROUTING_KEY = '{0}'".format(self.config.get_CELERY_DEFAULT_ROUTING_KEY()),
            "    # Django secret",
            "    SECRET_KEY = '{0}'".format(self.config.getDjangoSecretKey()),
            "",
            "    ADMINS = (('Admin', '{0}'),)".format(self.config.getAdminEmail()),
            "    MANAGERS = ADMINS",
            "",
            "    DATABASES = {",
            "        'default': {",
            "            'ENGINE': '{0}',".format(self.config.getDatabaseEngine()),
            "            'NAME': '{0}',".format(self.config.getDatabaseName()),
            "            'USER': '{0}',".format(self.config.getDatabaseUser()),
            "            'PASSWORD': '{0}',".format(self.config.getDatabasePassword()),
            "            'HOST': '{0}',".format(self.config.getDatabaseHost()),
            "            'PORT': '{0}', ".format(self.config.getDatabasePort()),
            "            'OPTIONS' : {",
            "                'init_command': 'SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED',",
            "                'read_timeout': 5",
            "            }",
            "        }",
            "    }",
            "",
            "    LOGS_PATH = abspath(join(dirname(abspath(__file__)), '..', '..', '..', '..', 'logs'))",
            "",
            "    RABBITMQ_HOST = 'localhost'",
            "    RABBITMQ_DEFAULT_USER = '{}'".format(self.config._svc['broker-user']),
            "    RABBITMQ_DEFAULT_PASS = '{}'".format(self.config._svc['broker-pass']),
            "    BROKER_USE_SSL = False  # Force SSL off",
            "",
            "    codalab.__path__ = extend_path(codalab.__path__, codalab.__name__)",
            "    NEW_RELIC_KEY = '{0}'".format(self.config.getNewRelicKey()),
            "",
        ]
        return '\n'.join(lines) + '\n'

    def get_compute_workers_file_content(self):
        '''
        Creates the content of the configuration file for a compute worker
        '''
        lines = [
            "compute-worker:",
            "    azure-storage:",
            "        account-name: '{0}'".format(self.config.getServiceStorageAccountName()),
            "        account-key: '{0}'".format(self.config.get_service_storage_account_key()),
            "    azure-service-bus:",
            "        namespace: '{0}'".format(self.config.getServiceBusNamespace()),
            "        key: '{0}'".format(self.config.get_service_bus_key()),
            "        issuer: 'owner'",
            "        shared-access-key-name: '{0}'".format(self.config.get_service_bus_shared_access_key_name()),
            "        shared-access-key-value: '{0}'".format(self.config.get_service_bus_shared_access_key_value()),
            "        listen-to: windowscomputequeue",
            "    local-root: '/codalabtemp'",
            "logging:",
            "    version: 1",
            "    formatters:",
            "        simple:",
            "            format: '%(asctime)s %(levelname)s %(message)s'",
            "    handlers:",
            "        console:",
            "            class: logging.StreamHandler",
            "            level: DEBUG",
            "            formatter: simple",
            "            stream: ext://sys.stdout",
            "    loggers:",
            "        codalabtools:",
            "            level: DEBUG",
            "            handlers: [console]",
            "            propagate: no",
            "    root:",
            "        level: DEBUG",
            "        handlers: [console]",
            "",
        ]
        return '\n'.join(lines) + '\n'
