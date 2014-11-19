"""
This example script finds all tweets sent by users who've set their location to ukraine or kiev,
and where the user's language is russian or ukrainian,
and saves them to a CSV file called ukraine_data.csv.


"""

from datetime import datetime
from smapp_toolkit.twitter import MongoTweetCollection

collection = MongoTweetCollection(address='ACTUAL DB ADDRESS',
                                  port=27011,
                                  username='ACTUAL DB USERNAME',
                                  password='ACTUAL DB PASSWORD',
                                  dbname='Ukraine')

columns = [
        'id_str',
        'timestamp',
        'coordinates.coordinates',
        'user.id_str',
        'user.lang',
        'lang',
        'text'
        ]

collection.since(datetime(2013,12,1)) \
               .until(datetime(2013,12,2)) \
               .user_location_containing('ukraine', 'kiev', 'kyiv', 'kiew') \
               .user_lang_containing('uk', 'ru') \
               .dump_csv('ukraine_data.csv', columns=columns)