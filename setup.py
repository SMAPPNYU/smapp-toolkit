import sys
from setuptools import setup

# if python version is above 3 then throw a message and exit
if not sys.version_info.major < 3:
    print "Hello python pirate! smapp-toolkit is only for python versions below version 3.0!"
    print "You appear to hav python version:"
    print "{}".format(sys.version_info.major)
    sys.exit(1)

setup(name='smapp-toolkit',
      version='0.1.34',
      description='NYU SMaPP lab toolkit',
      author='NYU SMaPP',
      license='GPLv2',
      author_email='smapp_programmer-group@nyu.edu',
      url='http://smapp.nyu.edu',
      packages=['smapp_toolkit', 'smapp_toolkit.twitter'],
      install_requires=[
          'pymongo>=3.0.1',
          'smappPy>=0.1.16',
          'networkx>=1.9.1',
          'pandas>=0.16.1',
          'simplejson>=3.5.2'
      ]
     )
