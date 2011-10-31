import os

ADMINS = (
    ('test@example.com', 'TEST-R'),
)

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

MEDIA_ROOT = os.path.normpath(os.path.join(BASE_PATH, 'media'))

# Django <= 1.2
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'imagekit.db'
TEST_DATABASE_NAME = 'imagekit-test.db'

# Django >= 1.3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'imagekit.db',
    },
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'imagekit',
    'core',
]

DEBUG = True
TEMPLATE_DEBUG = DEBUG
CACHE_BACKEND = 'locmem://'
