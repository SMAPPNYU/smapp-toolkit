#!/bin/bash
# yvan

# yvanbump.sh is the new script
# old script used sed which doesn't port to other systems - options change. often broke, 
# wiped the file, and didn't push new versions to pypi.

# we should use twine instead of standard upload to pypi, standard upload only uses TLS in later versions.

# bump and push to git
bash yvanbump.sh

# publish new version to pypi
python setup.py sdist upload
