test:
	flake8 --ignore=E501,E126,E127,E128 imagekit tests
	export PYTHONPATH=$(PWD):$(PYTHONPATH); \
	django-admin.py test --settings=tests.settings tests


.PHONY: test
