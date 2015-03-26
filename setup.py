from setuptools import setup

setup(name='smapp-toolkit',
      version='0.1.17',
      description='NYU SMaPP lab toolkit',
      author='NYU SMaPP',
      license='GPLv2',
      author_email='smapp_programmer-group@nyu.edu',
      url='http://smapp.nyu.edu',
      package_dir={'': 'smapp_toolkit'},
      packages=['twitter'],
      install_requires=[
          'pymongo>=2.8',
          'smappPy>=0.1.12',
      ]
     )
