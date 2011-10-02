
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('My Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

import tempfile, os
from django import contrib
tempdata = tempfile.mkdtemp()
approot = os.path.dirname(os.path.abspath(__file__))
adminroot = os.path.join(contrib.__path__[0], 'admin')

DATABASES = {
    'default': {
        'NAME': os.path.join(tempdata, 'imagekit-test.db'),
        'TEST_NAME': os.path.join(tempdata, 'imagekit-test.db'),
        'ENGINE': 'django.db.backends.sqlite3',
        'USER': '',
        'PASSWORD': '',
    }
}

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False
MEDIA_ROOT = os.path.join(approot, 'static')
MEDIA_URL = '/face/'
STATIC_ROOT = os.path.join(adminroot, 'static', 'admin')[0]
STATIC_URL = '/staticfiles/'
ADMIN_MEDIA_PREFIX = '/admin-media/'
#ROOT_URLCONF = 'signalqueue.settings.urlconf'

from django.core.files.storage import FileSystemStorage
#STATICFILES_STORAGE = FileSystemStorage(location=STATIC_ROOT, base_url=STATIC_URL)
#STATICFILES_STORAGE = FileSystemStorage

TEMPLATE_DIRS = (
    os.path.join(approot, 'templates'),
    os.path.join(adminroot, 'templates'),
    os.path.join(adminroot, 'templates', 'admin'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.request",
    "django.core.context_processors.debug",
    #"django.core.context_processors.i18n", this is AMERICA
    "django.core.context_processors.media",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django_nose',
    'delegate',
    'imagekit',
    'signalqueue',
)

# Logging Configuration
import logging
GLOBAL_LOG_LEVEL = logging.DEBUG
LOGGING = dict(
    version=1,
    disable_existing_loggers=False,
    formatters={ 'standard': { 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s' }, },
    handlers={
        'default': { 'level':'INFO', 'class':'logging.StreamHandler', 'formatter':'standard' },
        'nil': { 'level':'INFO', 'class':'django.utils.log.NullHandler', },
    },
    loggers={
        'imagekit': { 'handlers': ['default'], 'level': logging.DEBUG, 'propagate': False },
        'signalqueue': { 'handlers': ['default'], 'level': logging.DEBUG, 'propagate': False },
        '': {  'handlers': ['default'], 'level': 'DEBUG', 'propagate': False },
        '*': {  'handlers': ['default'], 'level': 'DEBUG', 'propagate': False },
    },
)


SQ_QUEUES = {
    'default': {                                                # you need at least one dict named 'default' in SQ_QUEUES
        'ENGINE': 'signalqueue.worker.backends.RedisSetQueue',  # required - full path to a QueueBase subclass
        'INTERVAL': 30, # 1/3 sec
        'OPTIONS': dict(port=4332),
    },
    'sift': {
        'ENGINE': 'signalqueue.worker.backends.RedisQueue',
        'INTERVAL': 30, # 1/3 sec
        'OPTIONS': dict(port=4332),
    },
    'db': {
        'ENGINE': 'signalqueue.worker.backends.DatabaseQueueProxy',
        'INTERVAL': 30, # 1/3 sec
        'OPTIONS': dict(app_label='signalqueue', modl_name='EnqueuedSignal'),
    },
}

SQ_WORKER_PORT = 11201
SQ_RUNMODE = 'SQ_SYNC'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
