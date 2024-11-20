import uuid

from celery.schedules import crontab
from datetime import timedelta

from configurations import importer

if not importer.installed:
    importer.install()

from configurations import Configuration
import os, sys
from os.path import abspath, basename, dirname, join


def _uuidpathext(filename, prefix):
    filename = basename(filename)
    filepath = join(prefix, str(uuid.uuid4()), filename)
    return filepath


# One always get a string from env and need to convert to bool.
def _bool_from_env(key, default):
    try:
        val = os.environ[key]
    except KeyError:
        return default
    else:
        if val.lower() in ("y", "yes", "t", "true", "on", "1"):
            return True
        elif val.lower() in ("n", "no", "f", "false", "off", "0"):
            return False
        else:
            raise ValueError(
                "'%s' value of '%s' failed to convert to bool"
                % (key, val)
            )


class Base(Configuration):
    SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_APP_DIR = os.path.dirname(SETTINGS_DIR)
    PROJECT_DIR = os.path.dirname(PROJECT_APP_DIR)
    ROOT_DIR = os.path.dirname(PROJECT_DIR)
    PORT = '8000'
    DOMAIN_NAME = 'localhost'
    SERVER_NAME = 'localhost'
    DEBUG = _bool_from_env('DEBUG', False)
    COMPILE_LESS = True  # is the less -> css already done or would you like less.js to compile it on render
    LOCAL_MATHJAX = False  # see prep_for_offline
    LOCAL_ACE_EDITOR = False  # see prep_for_offline
    IS_DEV = _bool_from_env('IS_DEV', False)

    if 'CONFIG_SERVER_NAME' in os.environ:
        SERVER_NAME = os.environ.get('CONFIG_SERVER_NAME')
    if 'CONFIG_HTTP_PORT' in os.environ:
        PORT = os.environ.get('CONFIG_HTTP_PORT')

    MAINTENANCE_MODE=0
    if 'MAINTENANCE_MODE' in os.environ:
        MAINTENANCE_MODE = os.environ.get('MAINTENANCE_MODE')

    STARTUP_ENV = {
        'DJANGO_CONFIGURATION': os.environ['DJANGO_CONFIGURATION'],
        'DJANGO_SETTINGS_MODULE': os.environ['DJANGO_SETTINGS_MODULE'],
        'NEW_RELIC_CONFIG_FILE': '%s/newrelic.ini' % PROJECT_DIR,
    }

    TEST_DATA_PATH = os.path.join(PROJECT_DIR,'test_data')
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'  #'codalab.test_runner.CodalabTestRunner'
    PYTEST_FORCE_CHAHUB = False  # disable Chahub overall during tests
    CONFIG_GEN_TEMPLATES_DIR = os.path.join(PROJECT_DIR,'config','templates')
    CONFIG_GEN_GENERATED_DIR = os.path.join(PROJECT_DIR,'config','generated')

    DJANGO_ROOT = dirname(dirname(abspath(__file__)))
    SITE_ROOT = dirname(DJANGO_ROOT)

    SOURCE_GIT_URL = 'https://github.com/codalab/codalab.git'
    VIRTUAL_ENV = os.environ.get('VIRTUAL_ENV',None)

    AUTH_USER_MODEL = 'authenz.ClUser'

    CODALAB_VERSION = '1.6'

    # Hosts/domain names that are valid for this site; required if DEBUG is False
    # See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
    ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', ['*'])

    # Example ADMINS = Name,example@test.com;Name2,example2@test.com
    ADMINS = os.environ.get('ADMINS')
    if ADMINS:
        ADMINS = [a.split(',') for a in ADMINS.split(';')]

    MANAGERS = ADMINS

    # Local time zone for this installation. Choices can be found here:
    # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
    # although not all choices may be available on all operating systems.
    # In a Windows environment this must be set to your system time zone.
    TIME_ZONE = 'UTC'

    # Language code for this installation. All choices can be found here:
    # http://www.i18nguy.com/unicode/language-identifiers.html
    LANGUAGE_CODE = 'en-us'

    SITE_ID = 1
    CODALAB_SITE_DOMAIN = os.environ.get('CODALAB_SITE_DOMAIN', 'localhost')
    CODALAB_SITE_NAME = 'CodaLab'

    # If you set this to False, Django will make some optimizations so as not
    # to load the internationalization machinery.
    USE_I18N = True

    # If you set this to False, Django will not format dates, numbers and
    # calendars according to the current locale.
    USE_L10N = True

    # If you set this to False, Django will not use timezone-aware datetimes.
    USE_TZ = True

    # Absolute filesystem path to the directory that will hold user-uploaded files.
    # Example: "/var/www/example.com/media/"
    MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media')

    # URL that handles the media served from MEDIA_ROOT. Make sure to use a
    # trailing slash.
    # Examples: "http://example.com/media/", "http://media.example.com/"
    MEDIA_URL = '/media/'

    # Absolute path to the directory static files should be collected to.
    # Don't put anything in this directory yourself; store your static files
    # in apps' "static/" subdirectories and in STATICFILES_DIRS.
    # Example: "/var/www/example.com/static/"
    STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

    # URL prefix for static files.
    # Example: "http://example.com/static/", "http://static.example.com/"
    STATIC_URL = '/static/'

    # Additional locations of static files
    STATICFILES_DIRS = [
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ]

    # List of finder classes that know how to find static files in
    # various locations.
    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'compressor.finders.CompressorFinder',
    ]

    # Make this unique, and don't share it with anybody.
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', "a-hidden-secret")

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        "django_switchuser.middleware.SuStateMiddleware",
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'apps.web.middleware.SingleCompetitionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ]

    ROOT_URLCONF = 'codalab.urls'

    # Python dotted path to the WSGI application used by Django's runserver.
    WSGI_APPLICATION = 'codalab.wsgi.application'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
            'DIRS': [
                os.path.join(PROJECT_DIR, 'templates')
            ],
            'OPTIONS': {
                'context_processors': [
                    'django.contrib.auth.context_processors.auth',
                    'django.template.context_processors.debug',
                    'django.template.context_processors.i18n',
                    'django.template.context_processors.media',
                    'django.template.context_processors.static',
                    'django.template.context_processors.tz',
                    'django.contrib.messages.context_processors.messages',
                    "codalab.context_processors.app_version_proc",
                    'django.template.context_processors.request',
                    "codalab.context_processors.common_settings",
                    "django_switchuser.context_processors.su_state",
                ],
                'debug': DEBUG
            }
        },
    ]

    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "allauth.account.auth_backends.AuthenticationBackend",
        'guardian.backends.ObjectPermissionBackend',
    ]

    INSTALLED_APPS = [
        # Standard django apps
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.admin',
        'django.contrib.humanize',

        # Analytics app that works with many services - IRJ 2013.7.29
        'analytical',
        'rest_framework',
        'django_filters',

        # This is used to manage the HTML page hierarchy for the competition
        'mptt',

        # TODO: Document the need for these
        'compressor',
        'guardian',
        'captcha',
        'bootstrapform',

        # Storage API
        'storages',
        's3direct',

        # Django Nose !!Important!! This needs to come after South.
        'django_nose',

        # CodaLab apps
        'apps.authenz',
        'apps.jobs',
        'apps.api',
        'apps.web',
        'apps.health',
        'apps.analytics',
        'apps.forums',
        'apps.coopetitions',
        'apps.common',
        'apps.chahub',
        'apps.queues',
        'apps.teams',
        'apps.customizer',
        'apps.newsletter',

        # Authentication app, enables social authentication
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'tinymce',
        'oauth2_provider',

        # Search
        'haystack',
        'django_extensions',

        # Switch User
        "django_switchuser",

        # Lockout
        'pin_passcode',
    ]

    ACCOUNT_ADAPTER = "apps.authenz.adapter.CodalabAccountAdapter"

    OPTIONAL_APPS = list()
    INTERNAL_IPS = []

    OAUTH2_PROVIDER = {
        'OAUTH2_VALIDATOR_CLASS': 'apps.authenz.oauth.Validator',
        'ACCESS_TOKEN_EXPIRE_SECONDS': 60 * 60 * 24 * 3,  # 3 days
    }

    # Authentication configuration
    LOGIN_REDIRECT_URL = '/'
    ANONYMOUS_USER_ID = -1
    ACCOUNT_AUTHENTICATION_METHOD='username_email'
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_USERNAME_REQUIRED = True
    ACCOUNT_EMAIL_VERIFICATION = os.environ.get('ACCOUNT_EMAIL_VERIFICATION', 'mandatory')
    ACCOUNT_SIGNUP_FORM_CLASS = 'apps.authenz.forms.CodalabSignupForm'
    ACCOUNT_LOGOUT_ON_GET = True

    # Privacy (leave empty to not track visitors with Google)
    GOOGLE_ANALYTICS = os.environ.get('GOOGLE_ANALYTICS', '')

    # Compress Configuration
    COMPRESS_PRECOMPILERS = [
        ('text/less', 'lessc {infile} {outfile}'),
        ('text/typescript', 'tsc {infile} --out {outfile}'),
    ]

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        ],
    }


    BUNDLE_SERVICE_URL = ""

    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
        },
    }

    # =========================================================================
    # SSL
    # =========================================================================
    SSL_PORT = os.environ.get('SSL_PORT', '443')
    SSL_CERTIFICATE = os.environ.get('SSL_CERTIFICATE')
    SSL_CERTIFICATE_KEY = os.environ.get('SSL_CERTIFICATE_KEY')

    if SSL_CERTIFICATE:
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
        # SECURE_SSL_REDIRECT = True
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True


    # =========================================================================
    # Caching
    # =========================================================================
    MEMCACHED_PORT = os.environ.get('MEMCACHED_PORT', 11211)
    CACHES = {
        'default': {
            # 'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
            'LOCATION': 'memcached:{}'.format(MEMCACHED_PORT),
        }
    }

    # Store information for celery
    CELERY_RESULT_BACKEND = 'cache+memcached://memcached:{}/'.format(MEMCACHED_PORT)

    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"


    # =========================================================================
    # Email
    # =========================================================================
    EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    EMAIL_PORT = os.environ.get('EMAIL_PORT', 587)
    EMAIL_USE_TLS = _bool_from_env('EMAIL_USE_TLS', True)
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'CodaLab <noreply@codalab.org>')
    SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'noreply@codalab.org')

    MAILCHIMP_API_KEY = os.environ.get('MAILCHIMP_API_KEY')
    MAILCHIMP_DATA_CENTER = os.environ.get('MAILCHIMP_DATA_CENTER')
    MAILCHIMP_EMAIL_LIST_ID_ALL = os.environ.get('MAILCHIMP_EMAIL_LIST_ID_ALL')
    MAILCHIMP_EMAIL_LIST_ID_NEWSLETTER = os.environ.get('MAILCHIMP_EMAIL_LIST_ID_NEWSLETTER')

    MAILCHIMP_API_URL = 'https://{}.api.mailchimp.com/3.0'.format(MAILCHIMP_DATA_CENTER) if MAILCHIMP_DATA_CENTER else None
    MAILCHIMP_MEMBERS_ENDPOINT_ALL = '{}/lists/{}/members'.format(MAILCHIMP_API_URL, MAILCHIMP_EMAIL_LIST_ID_ALL) if all([MAILCHIMP_API_URL, MAILCHIMP_EMAIL_LIST_ID_ALL]) else None
    MAILCHIMP_MEMBERS_ENDPOINT_NEWSLETTER = '{}/lists/{}/members'.format(MAILCHIMP_API_URL, MAILCHIMP_EMAIL_LIST_ID_NEWSLETTER) if all([MAILCHIMP_API_URL, MAILCHIMP_EMAIL_LIST_ID_NEWSLETTER]) else None


    # =========================================================================
    # Storage
    # =========================================================================
    DEFAULT_FILE_STORAGE = os.environ.get('DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage')

    # S3 from AWS
    USE_AWS = DEFAULT_FILE_STORAGE == 'storages.backends.s3boto3.S3Boto3Storage' or DEFAULT_FILE_STORAGE == 'apps.web.utils.CodalabS3BotoStorage'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_STORAGE_PRIVATE_BUCKET_NAME = os.environ.get('AWS_STORAGE_PRIVATE_BUCKET_NAME')
    AWS_S3_CALLING_FORMAT = os.environ.get('AWS_S3_CALLING_FORMAT', 'boto.s3.connection.OrdinaryCallingFormat')
    AWS_S3_HOST = os.environ.get('AWS_S3_HOST', 's3-us-west-2.amazonaws.com')

    AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL','https://s3.amazonaws.com')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_SIGNATURE_VERSION = os.environ.get('AWS_S3_SIGNATURE_VERSION', 's3v4')

    AWS_S3_SECURE_URLS = _bool_from_env('AWS_S3_SECURE_URLS', True)
    AWS_QUERYSTRING_AUTH = _bool_from_env(
        # This stops signature/auths from appearing in saved URLs
        'AWS_QUERYSTRING_AUTH',
        False
    )

    # Defaults to virtual because AWS recently deprecated 'path' style addressing. Boto3 required for virtual to have an effect.
    AWS_S3_ADDRESSING_STYLE = os.environ.get('AWS_S3_ADDRESSING_STYLE', 'virtual')

    # TODO: We will need to explicitly set this eventually. When set to None publicly uploaded files like images are not viewable. (Access Denied from AWS)
    # AWS_DEFAULT_ACL = None

    # Azure
    AZURE_ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME')
    AZURE_ACCOUNT_KEY = os.environ.get('AZURE_ACCOUNT_KEY')
    AZURE_CONTAINER = os.environ.get('AZURE_CONTAINER', 'public')
    BUNDLE_AZURE_ACCOUNT_NAME = os.environ.get('BUNDLE_AZURE_ACCOUNT_NAME', AZURE_ACCOUNT_NAME)
    BUNDLE_AZURE_ACCOUNT_KEY = os.environ.get('BUNDLE_AZURE_ACCOUNT_KEY', AZURE_ACCOUNT_KEY)
    BUNDLE_AZURE_CONTAINER = os.environ.get('BUNDLE_AZURE_CONTAINER', 'bundles')
    AZURE_BLOB_SERVICE_HOST_BASE = os.environ.get('AZURE_BLOB_SERVICE_HOST_BASE')


    # =========================================================================
    # S3Direct (S3 uploads)
    # =========================================================================
    S3DIRECT_REGION = os.environ.get('S3DIRECT_REGION', 'us-west-2')
    S3DIRECT_DESTINATIONS = {
        'competitions': {
            'key': lambda f: _uuidpathext(f, 'uploads/competitions/'),
            'auth': lambda u: u.is_authenticated(),
            'bucket': AWS_STORAGE_PRIVATE_BUCKET_NAME,
            'allowed': ['application/zip', 'application/octet-stream', 'application/x-zip-compressed']
        },
        'submissions': {
            'key': lambda f: _uuidpathext(f, 'uploads/submissions/'),
            'auth': lambda u: u.is_authenticated(),
            'bucket': AWS_STORAGE_PRIVATE_BUCKET_NAME,
            'allowed': ['application/zip', 'application/octet-stream', 'application/x-zip-compressed']
        }
    }

    # Default to {1}.{0} for `virtual` style addressing versus path. Path was deprecated by AWS. Use 'https://{0}/{1}' for path.
    # first arg (0) is host, second arg (1) is bucket name.
    S3DIRECT_URL_STRUCTURE = os.environ.get('S3DIRECT_URL_STRUCTURE', 'https://{1}.{0}')


    # =========================================================================
    # RabbitMQ
    # =========================================================================
    RABBITMQ_DEFAULT_USER = os.environ.get('RABBITMQ_DEFAULT_USER', 'guest')
    RABBITMQ_DEFAULT_PASS = os.environ.get('RABBITMQ_DEFAULT_PASS', 'guest')
    RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbit')
    RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', '5672')
    RABBITMQ_MANAGEMENT_PORT = os.environ.get('RABBITMQ_MANAGEMENT_PORT', '15672')

    if DEBUG and SSL_CERTIFICATE:
        # To make RABBITMQ api calls work locally over SSL we need this set for requests
        # to recognize our cert
        os.environ.setdefault('REQUESTS_CA_BUNDLE', SSL_CERTIFICATE)


    # =========================================================================
    # Celery
    # =========================================================================
    BROKER_URL = os.environ.get('BROKER_URL')
    if not BROKER_URL:
        # BROKER_URL might be set but empty, make sure it's set!
        BROKER_URL = 'pyamqp://{}:{}@{}:{}//'.format(RABBITMQ_DEFAULT_USER, RABBITMQ_DEFAULT_PASS, RABBITMQ_HOST, RABBITMQ_PORT)
    BROKER_POOL_LIMIT = None  # Stops connection timeout
    BROKER_USE_SSL = SSL_CERTIFICATE or _bool_from_env('BROKER_USE_SSL', False)
    # Don't use pickle -- dangerous
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    # Keep celery from becoming unresponsive
    CELERY_ACKS_LATE = True
    CELERYD_PREFETCH_MULTIPLIER = 1
    CELERYD_TASK_SOFT_TIME_LIMIT = 180  # 3 minutes
    FLOWER_PORT = os.environ.get('FLOWER_PORT', '15672')
    # Run as *not* root
    CELERYD_USER = "workeruser"
    CELERYD_GROUP = "workeruser"
    CELERYD_MAX_TASKS_PER_CHILD = 100  # Make celery restart every N tasks to stop leaks
    CELERYBEAT_SCHEDULE = {
        'phase_migrations': {
            'task': 'apps.web.tasks.do_phase_migrations',
            'schedule': timedelta(seconds=60 * 5),
        },
        'chahub_retries': {
            'task': 'apps.web.tasks.do_chahub_retries',
            'schedule': timedelta(seconds=60 * 10),
        },
        'chahub_competition_updates': {
            'task': 'apps.web.tasks.send_chahub_competition_updates',
            'schedule': timedelta(seconds=60 * 60 * 24),
        },
        'chahub_general_statistics': {
            'task': 'apps.web.tasks.send_chahub_general_stats',
            'schedule': timedelta(seconds=60 * 60 * 24),
        },
        'retry_mailing_list': {
            'task': 'apps.newsletter.tasks.retry_mailing_list',
            'schedule': timedelta(seconds=(60 * 60))
        },
        'create_storage_analytics_snapshot': {
            'task': 'apps.web.tasks.create_storage_analytics_snapshot',
            'schedule': crontab(hour=2, minute=0, day_of_week='sun') # Every Sunday at 02:00
        },
        'reset_computed_storage_analytics': {
            'task': 'apps.web.tasks.reset_computed_storage_analytics',
            'schedule': crontab(minute=0, hour=2, day_of_month=1, month_of_year="*/3") # Every 3 month at 02:00 on the 1st
        }
    }
    CELERY_TIMEZONE = 'UTC'


    # =========================================================================
    # Single Competition Mode
    # =========================================================================
    # Single competition mode features can be enabled on the customization page
    # or via ENV vars here.
    SINGLE_COMPETITION_VIEW_PK = os.environ.get('SINGLE_COMPETITION_VIEW_PK')
    CUSTOM_HEADER_LOGO = os.environ.get('CUSTOM_HEADER_LOGO')

    # NOTE! The above values are secondarily controlled via Configuration model objects,
    # which take precedence over these Env vars


    # =========================================================================
    # ChaHub
    # =========================================================================
    CHAHUB_API_URL = os.environ.get('CHAHUB_API_URL')
    CHAHUB_API_KEY = os.environ.get('CHAHUB_API_KEY')
    CHAHUB_PRODUCER_ID = os.environ.get('CHAHUB_PRODUCER_ID')
    SOCIAL_AUTH_CHAHUB_BASE_URL = os.environ.get('SOCIAL_AUTH_CHAHUB_BASE_URL')

    if CHAHUB_API_URL:
        assert CHAHUB_API_URL.endswith("/"), "ChaHub API url must end with a slash"

    # =========================================================================
    # Logging
    # =========================================================================
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '%(asctime)s %(levelname)s %(message)s'
            },
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'stream': sys.stdout
            },
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler'
            }
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            },
            'django.request': {
                'handlers': ['mail_admins'],
                'level': 'ERROR',
                'propagate': True,
            },
            'codalab': {
                'handlers': ['console'],
                'level': 'INFO'
            },
            'codalabtools': {
                'handlers': ['console'],
                'level': 'INFO'
            },
            'apps': {
                'handlers': ['console'],
                'level': 'INFO'
            }
        }
    }


    # =========================================================================
    # Database
    # =========================================================================
    if 'test' in sys.argv or any('py.test' in arg for arg in sys.argv):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
    else:
        db_engine = os.environ.get('DB_ENGINE')
        if db_engine:
            if db_engine == 'mysql':
                DATABASES = {
                    'default': {
                        'ENGINE': 'django.db.backends.mysql',
                        'NAME': os.environ.get('DB_NAME'),
                        'USER': os.environ.get('DB_USER', 'root'),
                        'PASSWORD': os.environ.get('DB_PASSWORD'),
                        'HOST': os.environ.get('DB_HOST', 'mysql'),
                        'PORT': os.environ.get('DB_PORT', '3306'),
                        'OPTIONS': {
                            'init_command': "SET time_zone='+00:00';",
                        },
                    }
                }
            elif db_engine == 'postgresql':
                DATABASES = {
                    'default': {
                        'ENGINE': 'django.db.backends.postgresql_psycopg2',
                        'NAME': os.environ.get('DB_NAME', 'codalab_website'),
                        'USER': os.environ.get('DB_USER', 'postgres'),
                        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
                        'HOST': os.environ.get('DB_HOST', 'postgres'),
                        'PORT': os.environ.get('DB_PORT', '5432'),
                    }
                }
            elif db_engine == 'sqlite3':
                DATABASES = {
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': 'codalab.sqlite3',
                    }
                }
            else:
                DATABASES = {
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': ':memory:',
                    }
                }
        else:
            # IF DB_ENGINE is not set, old behaviour is used
            mysqldb = os.environ.get('MYSQL_DATABASE')

            if mysqldb:
                DATABASES = {
                    'default': {
                        'ENGINE': 'django.db.backends.mysql',
                        'NAME': os.environ.get('MYSQL_DATABASE'),
                        'USER': os.environ.get('MYSQL_USERNAME', 'root'),
                        'PASSWORD': os.environ.get('MYSQL_ROOT_PASSWORD'),
                        'HOST': 'mysql',
                        'OPTIONS': {
                            'init_command': "SET time_zone='+00:00';",
                        },
                    }
                }
            else:
                DATABASES = {
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': 'codalab.sqlite3',
                    }
                }

    # =========================================================================
    # Docker
    # =========================================================================
    DOCKER_DEFAULT_WORKER_IMAGE = os.environ.get("DOCKER_DEFAULT_WORKER_IMAGE", "codalab/codalab-legacy:latest")
    DOCKER_MAX_SIZE_GB = 10.0

    # =========================================================================
    # Misc
    # =========================================================================
    GRAPH_MODELS = {
        'all_applications': True,
        'group_models': True,
    }
    DISABLE_SUBMISSIONS = False
    DEFAULT_UPPER_BOUND_MAX_SUBMISSION_SIZE_MB = 300

    @classmethod
    def pre_setup(cls):
        if hasattr(cls,'OPTIONAL_APPS'):
            cls.INSTALLED_APPS += cls.OPTIONAL_APPS
        if hasattr(cls, 'EXTRA_MIDDLEWARE_CLASSES'):
            cls.MIDDLEWARE_CLASSES += cls.EXTRA_MIDDLEWARE_CLASSES
        cls.STARTUP_ENV.update({ 'CONFIG_HTTP_PORT': cls.PORT,
                                 'CONFIG_SERVER_NAME': cls.SERVER_NAME })

    @classmethod
    def post_setup(cls):
        if not hasattr(cls,'PORT'):
            raise AttributeError("PORT environmenment variable required")
        if not hasattr(cls,'SERVER_NAME'):
            raise AttributeError("SERVER_NAME environment variable required")

        if cls.SERVER_NAME not in cls.ALLOWED_HOSTS:
            cls.ALLOWED_HOSTS.append(cls.SERVER_NAME)


class DevBase(Base):

    if _bool_from_env('DEBUG', False):
        OPTIONAL_APPS = [
            'debug_toolbar',
        ]
        ACCOUNT_EMAIL_VERIFICATION = None
        EXTRA_MIDDLEWARE_CLASSES = [
            'debug_toolbar.middleware.DebugToolbarMiddleware',
        ]

        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TEMPLATE_CONTEXT': True,
            'ENABLE_STACKTRACES': True,
            'SHOW_TOOLBAR_CALLBACK': lambda x: True,
        }

        if _bool_from_env('PIN_PASSCODE_ENABLED', False):
            EXTRA_MIDDLEWARE_CLASSES += ['pin_passcode.middleware.PinPasscodeMiddleware',]
            PIN_PASSCODE_PIN = os.environ.get('PIN_PASSCODE_PIN', 1234)
            PIN_PASSCODE_IP_WHITELIST = ['127.0.0.1', 'localhost',]

        # Increase amount of logging output in Dev mode.
        # for logger_name in ('codalab', 'apps'):
        #     Base.LOGGING['loggers'][logger_name]['level'] = 'DEBUG'
