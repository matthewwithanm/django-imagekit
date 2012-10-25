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
    'django_nose',
]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '-s',
    '--with-progressive',

    # When the tests are run --with-coverage, these args configure coverage
    # reporting (requires coverage to be installed).
    # Without the --with-coverage flag, they have no effect.
    '--cover-tests',
    '--cover-html',
    '--cover-package=imagekit',
    '--cover-html-dir=%s' % os.path.join(BASE_PATH, 'cover')
]

DEBUG = True
TEMPLATE_DEBUG = DEBUG
CACHE_BACKEND = 'locmem://'
