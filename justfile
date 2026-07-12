publish:
    python -m build
    python -m twine upload dist/*

test:
    tox
