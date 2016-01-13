#!/bin/bash

# bump and push to git
bash yvanbump.sh

# publish new version to pypi
python setup.py sdist upload
