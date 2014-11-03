# SMAPP Twitter Toolkit
This is an user-friendly python package for interfacing with large collections of tweets. Developped at the SMaPP lab at New York University.

## Installation
Using pip:

`pip install -e git+https://github.com/SMAPPNYU/smapp-toolkit#egg=smapp_toolkit`

Or locally

    git clone https://github.com/SMAPPNYU/smapp-toolkit
    cd smapp-toolkit
    python setyp.py install

#### Dependencies
The `smapp-toolkit` depends on the following packages, which will be automatically installed when installing `smapp-toolkit`:
* [pymongo](http://api.mongodb.org/python/current/), the Python MongoDB driver
* [smappPy](https://github.com/SMAPPNYU/smappPy), a utility library from SMaPP

## Usage

#### Using MongoDB as the backend

    from smapp_toolkit.twitter import MongoTweetCollection
    collection = MongoTweetCollection(address='mongodb-address',
                                      port='mongodb-port',
                                      username='mongodb-user',
                                      password='mongodb-password',
                                      dbname='database-name',
                                      collection_name='collection-name')

#### Count occurences of keywords

    collection.containing('#bieber').count()
    texts = collection.containing('#bieber').texts()

#### Tweets containing one of several keywords (#bieber OR #sexy)

    collection.containing('#bieber', '#sexy')

#### Random sample of tweets

    collection.containing('#bieber').sample(0.33).texts()

#### Select tweets from a certain time span

    from datetime import datetime
    collection.since(datetime(2014,1,30)).count()
    collection.since(datetime(2014,2,16)).until(datetime(2014,2,19)).containing('obama').texts()

#### Select tweets authored in a certain language

    collection.language('en').texts()

#### Exclude retweets

    collection.excluding_retweets().count()

#### Visualizing the volume of tweets

    bins, counts = collection.containing('#sexy').histogram(bins='minutes')
    plt.plot(bins,counts)

-----------
Code and documentation &copy; 2014 New York University. Released under [the GPLv2 license](LICENSE).
