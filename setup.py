from setuptools import setup

setup(name='smapp-toolkit',
      version='0.1.26',
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
      ]
     )
