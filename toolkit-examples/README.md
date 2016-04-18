# smappexamples
This repository contains example scripts demonstrating how to use smapp tools.


## [toolkit examples](https://github.com/SMAPPNYU/smappexamples/tree/master/toolkitexamples)

This folder contains examples of how to query the [smapp-toolkit](https://github.com/SMAPPNYU/smapp-toolkit). 

###[count_all_tweets_from_db.py](https://github.com/SMAPPNYU/smappexamples/blob/master/toolkitexamples/count_all_tweets_from_db.py)

This script creates a collection by connecting to a database. It counts all the tweets on this database / collection. 

###[count_tweets_in_daterange_from_bson.py](https://github.com/SMAPPNYU/smappexamples/blob/master/toolkitexamples/count_tweets_in_daterange_from_bson.py)

This script creates a collection by hooking up to a BSON file. It counts all the tweets on this bson file / collection.

###[count_unique_users_from_bson.py](https://github.com/SMAPPNYU/smappexamples/blob/master/toolkitexamples/count_unique_users_from_bson.py)

This script creates a collection by hooking up to a BSON file. It then sets a date range datetime(2012, 1, 1) to datetime(2012,1, 8) using the [datetime module](https://pymotw.com/2/datetime/) (not included in the [smapp-toolkit](https://github.com/SMAPPNYU/smapp-toolkit)).It then counts all the tweets in a declared date range (January 1 2012 to January 8 2012).

###[count_unique_users_from_db.py](https://github.com/SMAPPNYU/smappexamples/blob/master/toolkitexamples/count_unique_users_from_db.py) 

This script creates a collection by connecting to a database. It counts all the unique users on that tweet collection by accessing each tweet object's 'id_str' field. It stores these id_str values in a dictionary where they are guaranteed to be unique. This dictionary can then be iterated through to check the unique ids or counted on with the len() method to get the number of unique users
