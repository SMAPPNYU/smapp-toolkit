# SMAPP Twitter Toolkit
This is an user-friendly python package for social media analytics.

## Installation
Using pip:

`pip install -e git+gitL//..#egg-info=smapp_toolkit`

Or locally

    git clone ...
    cd ..
    python setyp.py install


## Usage

#### Using MongoDB as the backend

    from smapp_toolkit.twitter import MongoTweetCollection
    collection = MongoTweetCollection('mongodb-address', 'mongodb-port',
        'mongodb-user', 'mongodb-password', 'database-name', 'collection-name')

#### Count occurences of keywords

    collection.mentioning('#bieber').count()
    texts = collection.mentioning('#bieber').texts()

#### Select tweets from a certain time span

    collection.since('2014-1-30').until('2014-2-17').count()
    collection.since('2014-2-16').until('2014-2-19').mentioning('obama').texts()

#### Find the 5 most retweeted tweets

    collection.top_retweeted_tweets(5).texts()

#### Find the 5% most retweeted users

    collection.top_retweeted_users(0.05)

#### Visualize the tweet volume

    collection.since('2014-10-1').plot_tpm()