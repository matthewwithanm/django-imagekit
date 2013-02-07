# A wrapper for Django's test runner.
# See http://ericholscher.com/blog/2009/jun/29/enable-setuppy-test-your-django-apps/
# and http://gremu.net/blog/2010/enable-setuppy-test-your-django-apps/
import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
test_dir = os.path.dirname(__file__)
sys.path.insert(0, test_dir)

from django.test.utils import get_runner
from django.conf import settings


def run_tests():
    cls = get_runner(settings)
    runner = cls()
    failures = runner.run_tests(['tests'])
    sys.exit(failures)
