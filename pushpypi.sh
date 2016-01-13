# step one extract the version # from the old file
# step two increment the version number
# step three commit it
# step 4 push to pypi

# old script used sed which doesn't port to other systems - options change. often broke, 
# wiped the file, and didn't push new versions to pypi.

# we should use twine instead of standard upload to pypi, standard upload only uses TLS in later versions.