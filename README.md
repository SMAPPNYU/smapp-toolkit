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
* [networkx](https://github.com/networkx/networkx), a library for building and analyzing graphs
* [pandas](http://pandas.pydata.org/), a Python data analysis library
* [simplejson](https://simplejson.readthedocs.org/en/latest/)

## Usage

### Using MongoDB as the backend
```python
from smapp_toolkit.twitter import MongoTweetCollection
collection = MongoTweetCollection(address='mongodb-address',
                                  port='mongodb-port',
                                  username='mongodb-user',
                                  password='mongodb-password',
                                  dbname='database-name')
```

### Using a BSON file as the backend
```python
from smapp_toolkit.twitter import BSONTweetCollection
collection = BSONTweetCollection("path/to/file.bson")
```

#### Count occurences of keywords
```python
collection.containing('#bieber').count()
texts = collection.containing('#bieber').texts()
```

#### Apply a filter that adds labels to BSONTweetCollection or MongoTweetCollection and outputs the result to a bson file
```python
collection.apply_labels(
  list_of_labels
  ,list_of_fields
  ,list_for_values
  ,bsonoutputpath
)
```

The method applies a set of named labels and attaches them to objects from a collection if the certain fields
in the collection meet certain criteria.



```python
collection.apply_labels(
  [['religious_rank', 'religious_rank', 'political_rank'], ['imam', 'cleric', 'politician']]
  ,['user.screen_name', 'user.id']
  ,[['Obama', 'Hillary'], ['1234567', '7654321']]
  ,'outputfolder/bsonoutput.bson'
)
```
NOTE: ['1234567', '7654321'] are not the actual ids of any twitter users they are just dummy numbers.

`list_of_labels` is a list with two lists inside it where the first list contains names for labels and the second list
contains the labels themselves. For example: `religious_rank` and `imam` would be a label called religious_rank for the label value imam.

Each field in the `list_of_fields` array is a string that takes dot notation. user.screen_name would be the screen_name 
entry in the user entry in the collection object. You can nest these for as many levels as you have in the collection
object. 

`list_for_values` is a list that contains as many lists as there are fields to match. Each of these lists (inside list_for_
values) is a list of the values you would like that field to match. So if you want the user.screen_name to match "obama" 
"hillary" or "lessig" then you would use:

```python
list_of_fields = ['user.screen_name']
list_for_values = [['obama', 'hillary', 'lessig']]
```
as inputs.

`bsonoutputpath` is the path realtive to where you run the script that will be the output file with the new labels.

After you run this method each tweet object in your output BSON will now have a field called "labels" like so:
```
{
.
.
.
"labels" : {
  "1": {name: “religious_rank”, type: “cleric”},
  "2": {name: ”religious_rank”, type: ”imam"},
  "3": {name: “eye_color”, type :”brown"}
}
.
.
.
}
```

#### Tweets containing one of several keywords (#bieber OR #sexy)
```python
collection.containing('#bieber', '#sexy')
```

#### Count occurences of multiple keywords over time
```python
collection.term_counts(['justin', 'miley'], count_by='days', plot=False)
Out[]:
{'2015-04-01': {'justin': 1312, 'miley': 837},
 '2015-04-02': {'justin': 3287, 'miley': 932}}
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

Note that both 'since(...)' and 'until(...)' are exclusive (ie, they are GT/> and LT/<, respectively, not GTE/>= or LTE/<=)
This means that since(datetime(2014, 12, 24)) will return tweets after EXACTLY 12/24/2014 00:00:00 (M/D/Y H:M:S).
Datetimes may be specified to the second: datetime(2014, 12, 24, 6, 30, 25) is 6:30 and 25 seconds AM Universal Timezone.
If time (hours, minutes, etc) is not specified, time defaults 00:00:00.

#### Select tweets authored in a certain language
```python
collection.language('en').texts()
```

#### Tweets in Russian OR Ukrainian
```python
collection.language('ru', 'uk')
```

#### Tweets from users with their stated language preference to French OR German
```python
collection.user_lang_contains('de', 'fr')
```

#### Exclude retweets
```python
collection.excluding_retweets().count()
```

#### Only tweets where the user location indicates they are from new york
```python
collection.user_location_containing('new york', 'nyc')
```

#### Only tweets where the user cares about python data analysis
```python
collection.field_containing('user.description', 'python', 'data', 'analysis')
```

#### Only get geotagged tweets
```python
collection.geo_enabled()
```

#### Only get non-geotagged tweets
```python
collection.non_geo_enabled()
```

#### Sorting by time
```python
collection.sort('timestamp',-1)
```

#### Only get the latest 10 tweets
```python
collection.sort('timestamp',-1).limit(10).texts()
```

#### Counting top entities
#####top 10 hashtags on a given day
```python
counts = collection.since(datetime(2015,1,1)).until(datetime(2015,1,2)).top_hashtags(n=10)
```

#####top bigrams in the last hour
```python
counts = collection.since(datetime.utcnow()-timedelta(hours=1)).top_bigrams(n=5)
```

#####top urls
```python
counts = collection.top_urls(n=10)
```

#####other `top_x` methods
* `top_unigrams()`
* `top_trigrams()`
* `top_images()`
* `top_mentions()`
* `top_links()`
* `top_user_locations()`
* `top_geolocation_names()`

#####Multiple top_x methods in one go
The function `top_entities(...)` returns a dictionary object with `pandas.Series` objects for each top entity list

```python
In []: col = BSONTweetCollection('/home/yablee/Projects/SMAPP/tmp/arabevents_sample.bson')
In []: top_things = col.top_entities(ngrams=(1,2,3))
In []: top_things['2-grams']
Out[]: 
فيديو قوات          350
الطوارى السعودية    330
قوات الطوارى        305
#السعودية #saudi    266
#ksa #السعودية      244
قوات الطوارئ        236
الطوارئ السعودية    236
#saudi #الرياض      226
يقبضون على          185
السعودية يقبضون     185
dtype: int64
```

#####writing `top_x()` results to a csv file

All `top_x()` methods return `pandas.DataFrame` objects. They may be easily exported to a csv file, as follows:
```python
hashtags = collection.top_hashtags(n=5)
hashtags.to_csv('/path/to/my/output.csv', encoding='utf8')
```

#####top retweets

To get the top retweets for a certain collection, use the `top_retweets()` method. Specify which columns (of the original tweet) to include in the result, by passing thr `rt_columns` argument, as follows:
```python
top_rts = collection.since(datetime.utcnow()-timedelta(hours=1)).top_retweets(n=10, rt_columns=['user.screen_name', 'user.location', 'created_at', 'text'])
```
The default columns included are `['user.screen_name', 'created_at', 'text']`.

### Grouping by time slice
Use the `collection.group_by(time_unit)` method to group tweets by time slices. Supported time slices are `days`, `hours`, `minutes`, and `seconds`. Here's a basic example:

```python
for time, tweets in collection.group_by('hours'):
    print("{time}: {count}".format(time=time, count=len(list(tweets))))
```
which outputs:
```
2015-01-12 17:00:00: 13275
2015-01-12 18:00:00: 23590
```

#### Counting tweets per time slice
```python
In []: col.since(datetime(2015,6,18,12)).until(datetime(2015,6,18,15)).group_by('hours').count()
Out[]:
                      count
2015-06-18 12:00:00  164181
2015-06-18 13:00:00  167129
2015-06-18 14:00:00  165057
```

#### top_x methods grouped by time slice
The framework also supports `top_x` methods with results grouped by time slice.

Example:
```python
collection.since(datetime(2015,6,1)).group_by('days').top_user_locations(n=5)

  #            London  London, UK  Manchester  Scotland  UK
  # 2015-06-1       4           2           1         1   2
  # 2015-06-2      11           4           9         3   3
  # 2015-06-3      14           1           5       NaN   4
  # 2015-06-4      17           1           5         1   6
  # 2015-06-5      10           3           3         3   3
```

#### counting entities in tweets by time slice
```python
In []: col.group_by('hours').entities_counts()
Out[]:
                     _total   url  image  mention  hashtag  geo_enabled  retweet
2015-01-12 17:00:00   13275   881   1428     6612     2001        10628       15 
2015-01-12 18:00:00   23590  1668   2509    12091     3575        19019       36
```

#### Counting tweet languages over time slice
```python
In []: col.since(datetime.utcnow()-timedelta(minutes=10)).until(datetime.utcnow()).group_by('minutes').language_counts(langs=['en', 'es', 'other'])   
Out[]:
                       en   es  other
2015-06-18 21:23:00   821   75    113
2015-06-18 21:24:00  2312  228    339
2015-06-18 21:25:00  2378  196    339
2015-06-18 21:26:00  2352  233    295
2015-06-18 21:27:00  2297  239    344
2015-06-18 21:28:00  1776  173    247
2015-06-18 21:29:00  1825  162    269
2015-06-18 21:30:00  2317  237    326
2015-06-18 21:31:00  2305  233    342
2015-06-18 21:32:00  2337  235    308
2015-06-18 21:33:00  1508  136    228
```

#### Counting number of unique users per time slice
```python
In []: from smapp_toolkit.twitter import BSONTweetCollection
In []: col = BSONTweetCollection('arabevents_sample.bson')
In []: unique_users = col.group_by('minutes').unique_users()
In []: tweets = col.group_by('minutes').count()
In []: unique_users['total tweets'] = tweets['count']
In []: unique_users
Out[]: 
                     unique_users  total tweets
2015-04-16 17:01:00           377           432
2015-04-16 17:02:00           432           582
2015-04-16 17:03:00           442           610
2015-04-16 17:04:00           393           531
2015-04-16 17:05:00           504           756
2015-04-16 17:06:00           264           365
```

### Visualizations
The `smapp_toolkit.plotting` module has functions that can make canned visualizations of the data generated by the functions above.
For more examples, see the [examples](https://github.com/SMAPPNYU/smapp-toolkit/tree/master/examples) folder.

#### Tweets volume with vertical annotation lines
See examples in the [gallery](http://philosoraptor.bio.nyu.edu:82/figure-gallery/#annotated-tweets-oer-time-unit).

#### Stacked bar plots

##### Plotting the proportion of retweets:
```python
from smapp_toolkit.plotting import stacked_bar_plot
data = col.since(datetime(2015,6,18,12)).until(datetime(2015,6,18,12,10)).group_by('minutes').entities_counts()
data['original tweet'] = data['_total'] - data['retweet']

plt.figure(figsize=(10,10))
stacked_bar_plot(data, ['retweet', 'original tweet'], x_tick_date_format='%H:%M', colors=['salmon', 'lightgrey'])
plt.title('Retweet proportion', fontsize=24)
plt.tight_layout()
```

##### Plotting top user locations:
```python
data = col.since(datetime(2015,6,18,12)).until(datetime(2015,6,18,12,10)).group_by('minutes').top_user_locations()

stacked_bar_plot(data, ['London', 'New York'], x_tick_date_format='%H:%M')
plt.title('Tweets from London and New York users', fontsize=18)
plt.tight_layout()
```

See more examples in the [gallery](http://philosoraptor.bio.nyu.edu:82/figure-gallery/#stacked-bar-plots).

### Other visualization functions
The following functions make plots by first getting data from collection and then making the plots. Their use is discouraged as getting the data can sometimes be slow. Always prefer to get the data and make plots separately, saving the data first.

#### Visualizing the volume of tweets
```python
bins, counts = collection.containing('#sexy').tweets_over_time_figure(
    start_time,
    step_size=timedelta(minutes=1),
    num_steps=60,
    show=False)
plt.title('Tweets containing "#sexy"')
plt.show()
```

#### Visualizing volume of selected terms over time
```python
collection.term_counts(['justin', 'miley'], count_by='days', plot=True, plot_total=True)
plt.show()
```

#### Visualize the retweet proportion over time
```python
collection.since(datetime(2015,6,1)).tweet_retweet_figure(group_by='days')
```
you may set `group_by=` to `days`, `hours`, `minutes`, or `seconds`.

#### Visualize proportion of geocoded tweets over time
```python
collection.since(datetime(2015,6,1)).geocoded_tweets_figure()
```

#### Visualize tweets with links, images, mentions
* `collection.tweets_with_urls_figure()`
* `collection.tweets_with_images_figure()`
* `collection.tweets_with_mentions_figure()`
* `collection.tweets_with_hashtags_figure()`


### Iterate over the full tweet objects
```python
for tweet in collection.containing('#nyc'):
    print(tweet['text'])
```
## Exporting
Here are functions for exporting data from collections to different formats.

### Dumping tweets to a CSV file
```python
collection.dump_csv('my_tweets.csv')
```
This will dump a CSV with the following columns:

    'id_str', 'user.screen_name', 'timestamp', 'text'

The desired columns may be specified in the `columns=` named argument:

```python
collection.dump_csv('my_tweets.csv', columns=['id_str', 'user.screen_name', 'user.location', 'user.description', 'text'])
```

### Dumping tweets to a BSON file
```python
dump_bson_topath ('output.bson')
```
This will dump a bson file of tweets. Once you have this bson you can convert it to JSON format with the
bsondump tool (if you have it) like so:

 ```sh
 bsondump output.bson > output.json
 ```

The full list of available fields from a tweet may be found on [the twitter REST-API documentation](https://dev.twitter.com/overview/api/tweets). In order to get nested fields (such as the user's location or the user's screen_name), use `user.location`, `user.screen_name`.

##### tweet coordinates
For geolocated tweets, in order to get the geolocation out in the csv, add `coordinates.coordinates` to the columns list. This will put the coordinates in [GeoJSON](http://geojson.org/geojson-spec.html#positions) (long, lat) in the column.
*Alternatively*¸ add `coordinates.coordinates.0` and `coordinates.coordinates.1` to the columns list. This will add two columns with the longitude and latitude in them respectively.

##### gzip compression
If the filename specified ends with `.gz`, the output file will be gzipped. This typically takes about a 1/3 as much space as a non-compressed file.

```python
collection.dump_csv('my_tweets.csv.gz')
```

### Dumping tweets to JSON file
This will dump whole tweets in JSON format into a specified file, one tweet per line.
```python
collection.dump_json("my_json.json")
```

Available options are:
* append=True, to append tweets in the collection to an existing file
* pretty=True, to write JSON into pretty, line-broken and properly indented format (this takes up much more space, so is not recommended for large collections)

### Dumping tweets to raw BSON file
This will dump whole tweets in MongoDB's BSON format into a specified file. Note that BSON is a "binary" format (it will look a little funny if opened in a text editor). This is the native format for MongoDB's mongodump program. The file is NOT line-separated.

```python
collection.dump_bson("my_bson.bson")
```

Available options are:
* append=True, to append BSON tweets to the given filename (if file already has tweets)

### Exporting a retweet graph
The toolkit supports exporting a retweet graph using the `networkx` library. In the exported graph users are nodes, retweets are directed edges.

If the collection result includes non-retweets as well, users with no retweets
will also appear in the graph as isolated nodes. Only retweets are edges in the resulting graph.

Exporting a retweet graph is done as follows:
```python
import networkx as nx
digraph = collection.containing('#AnyoneButHillary').only_retweets().retweet_network()
nx.write_graphml(digraph, '/path/to/outputfile.graphml')
```

Nodes and edges have attributes attached to them, which are customizable using the `user_metadata` and `tweet_metadata` arguments.

* `user_metadata` is a list of fields from the User object that will be included as attributes of the nodes.
* `tweet_metadata` is a list of the fields from the Tweet object that will be included as attributes of the edges.

The defaults are
* `user_metadata=['id_str', 'screen_name', 'location', 'description']`
* `tweet_metadata=['id_str', 'retweeted_status.id_str', 'timestamp', 'text', 'lang']`

For large graphs where the structure is interesting but the tweet text itself is not, it is advisable to ommit most of the metadata. This will make the resulting file smaller, and is done as follows:
```python
import networkx as nx
digraph = collection.containing('#AnyoneButHillary').only_retweets().retweet_network(user_metadata=['screen_name'], tweet_metadata=[''])
nx.write_graphml(digraph, '/path/to/outputfile.graphml')
```

The `.graphml` file may then be opened in graph analysis/visualization programs such as [Gephi](http://gephi.github.io/) or [Pajek](http://vlado.fmf.uni-lj.si/pub/networks/pajek/).

The `networkx` library also provides algorithms for [vizualization](http://networkx.github.io/documentation/networkx-1.9.1/reference/drawing.html) and [analysis](http://networkx.github.io/documentation/networkx-1.9.1/reference/algorithms.html).

## Figures
Smapp-toolkit has some built-in plotting functionality. See the [example scripts](https://github.com/SMAPPNYU/smapp-toolkit/tree/master/examples), and check out the [gallery](http://philosoraptor.bio.nyu.edu:82/figure-gallery/)!

Currently implemented:
* barchart of tweets per time-unit (`tweets_over_time_figure(...)`)
* barchart by language by day (`languages_per_day_figure(...)`)
* line chart (tweets per day) with vertical event annotations (`tweets_per_day_with_annotations_figure(...)`)
* geolocation names by time (`geolocation_names_by_day_figure(...)`)
* user locations by time (`user_locations_by_day_figure(...)`)

In order to get these to work, some extra packages (not automatically installed) need to be installed:
* `matplotlib`
* `seaborn`

## The MongoDB Data Model
SMAPP stores tweets in MongoDB databases, and splits the tweets across multiple MongoDB collections, because this gives better performance than a single large MongoDB collection. The MongoDB Database needs to have a `smapp_metadata` collection with a single `smapp-tweet-collection-metadata` document in it, which specifies the names of the tweet collections.

The `smapp-tweet-collection-metadata` document has the following form:

```json
{
  "document": "smapp-tweet-collection-metadata",
  "tweet_collections": [
    "tweets_1",
    "tweets_2",
    "tweets_3",
  ]
}
```

### Customization
The `MongoTweetCollection` object may still be used if the metadata collection and document have different names:

```python
collection = MongoTweetCollection(..., metadata_collection='smapp_metadata', metadata_document='smapp-tweet-collection-metadata')
```

#### Already have tweets in your own mongo and want to use the smapp-toolkit?
All you need to do is insert the following collection and document into your MongoDB database:

(from the mongo shell)

```
db.smapp_metadata.save({
  "document": "smapp-tweet-collection-metadata",
  "tweet_collections": [ "tweets" ]
})
```

and the default behavior will work as advertised.

-----------
Code and documentation &copy; 2014 New York University. Released under [the GPLv2 license](LICENSE).
