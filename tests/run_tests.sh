#!/bin/bash
PYTHONPATH=$PWD:$PWD/..${PYTHONPATH:+:$PYTHONPATH}
export PYTHONPATH

echo "Running django-imagekit tests..."
django-admin.py test core --settings=settings
