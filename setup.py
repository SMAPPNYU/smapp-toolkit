from setuptools import setup

setup(name='smapp-toolkit',
      version='0.1.19',
      description='NYU SMaPP lab toolkit',
      author='NYU SMaPP',
      license='GPLv2',
      author_email='smapp_programmer-group@nyu.edu',
      url='http://smapp.nyu.edu',
      packages=['smapp_toolkit', 'smapp_toolkit.twitter'],
      install_requires=[
          'pymongo>=2.8',
          'smappPy>=0.1.12',
      ]
     )
