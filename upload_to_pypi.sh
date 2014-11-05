#!/bin/sh
sed -r "s/version='([0-9]\.[0-9]\.)([0-9]+)'/echo '      version=\'\1\$((\2+1))\''/ge" setup.py > setup.py
git commit -am "Bump version number"
python setup.py sdist upload
