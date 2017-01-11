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

SECRET_KEY = '_uobce43e5osp8xgzle*yag2_16%y$sf*5(12vfg25hpnxik_*'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'imagekit',
    'tests',
    'django_nose',
]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '-s',

    # When the tests are run --with-coverage, these args configure coverage
    # reporting (requires coverage to be installed).
    # Without the --with-coverage flag, they have no effect.
    '--cover-tests',
    '--cover-html',
    '--cover-package=imagekit',
    '--cover-html-dir=%s' % os.path.join(BASE_PATH, 'cover')
]

if os.getenv('TERM'):
    NOSE_ARGS.append('--with-progressive')

CACHE_BACKEND = 'locmem://'

# Django >= 1.8
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
