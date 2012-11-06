test:
	export PYTHONPATH=$(PWD):$(PYTHONPATH); \
	django-admin.py test --settings=tests.settings tests


.PHONY: test
