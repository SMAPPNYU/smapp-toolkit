# SMAPP Twitter Toolkit
This is an user-friendly python package for interfacing with large collections of tweets. Developped at the SMaPP lab at New York University.

**Supports Python 2.7**

## Installation
Simplest: using `pip`:
```bash
pip install smapp-toolkit
```

To update to the latest version, if you have an older one installed:
```bash
pip install -U smapp-toolkit
```

Or download the source code using git
```bash
git clone https://github.com/SMAPPNYU/smapp-toolkit
cd smapp-toolkit
python setup.py install
```

or download [the tarball](https://github.com/SMAPPNYU/smapp-toolkit/tarball/master) and install.

#### Dependencies
The `smapp-toolkit` depends on the following packages, which will be automatically installed when installing `smapp-toolkit`:
* [pymongo](http://api.mongodb.org/python/current/), the Python MongoDB driver
* [smappPy](https://github.com/SMAPPNYU/smappPy), a utility library from SMaPP

## Usage

#### Using MongoDB as the backend
```python
from smapp_toolkit.twitter import MongoTweetCollection
collection = MongoTweetCollection(address='mongodb-address',
                                  port='mongodb-port',
                                  username='mongodb-user',
                                  password='mongodb-password',
                                  dbname='database-name')
```

#### Count occurences of keywords
```python
collection.containing('#bieber').count()
texts = collection.containing('#bieber').texts()
```

#### Tweets containing one of several keywords (#bieber OR #sexy)

```python
collection.containing('#bieber', '#sexy')
```

#### Random sample of tweets
```python
collection.containing('#bieber').sample(0.33).texts()
```

#### Select tweets from a certain time span
```python
from datetime import datetime
collection.since(datetime(2014,1,30)).count()
collection.since(datetime(2014,2,16)).until(datetime(2014,2,19)).containing('obama').texts()
```

#### Select tweets authored in a certain language
```python
collection.language('en').texts()
```

#### Exclude retweets
```python
collection.excluding_retweets().count()
```

#### Visualizing the volume of tweets
```python
bins, counts = collection.containing('#sexy').histogram(bins='minutes')
plt.plot(bins,counts)
```

-----------
Code and documentation &copy; 2014 New York University. Released under [the GPLv2 license](LICENSE).
