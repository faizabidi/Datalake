'''
Dependencies:

1. Tweepy should be installed - https://github.com/tweepy/tweepy
2. Python modules including csv, json, argparse, unidecode

Description:

This script assumes that all keys and secrets are set in the environment. These 
are the keys and secrets that you get from your Twitter developer account. 

We use the tweepy library to get Tweets from Twitter, store it locally, and 
then move them into a Hive database on HDFS. 
'''

import sys
import argparse 
import os
import tweepy
import json
import csv
from unidecode import unidecode

__author__ = 'Faiz Abidi'

# Print some information on how to use this script and take in arguments
def inputArguments():
    parser = argparse.ArgumentParser(description=
        '\
        This script is used to pull in tweets since 2018-07-01 using some \
        hashtag. If you do not provide any of the 5 arguments needed, this \
        script will assume that the hashtag to search is #donaldtrump \
        and will look for 4 environment variables:  CONSUMER_KEY, \
        CONSUMER_SECRET, ACCESS_TOKEN, and ACCESS_TOKEN_SECRET. Make sure you \
        have them in your .bashrc file or something equivalent.'
        )
    parser.add_argument('--hashtag', type=str, help='the hashtag to search')
    parser.add_argument('--consumerKey', type=str, help='your Twitter account\'s consumer key.')
    parser.add_argument('--consumerSecret', type=str, help='your Twitter account\'s consumer secret.')
    parser.add_argument('--accessToken', type=str, help='your Twitter account\'s access token.')
    parser.add_argument('--accessSecret', type=str, help='your Twitter account\'s access token secret.')
    args = parser.parse_args()

    return args

# Check the arguments passed to the script. If keys and access tokens are not
# passed, check the environment variables
def inspectArguments():
    args = inputArguments()

    hashtag = args.hashtag
    consumerKey = args.consumerKey
    consumerSecret = args.consumerSecret
    accessToken = args.accessToken
    accessSecret = args.accessSecret

    if hashtag is None:
        hashtag = "#donaldtrump"
    else:
        hashtag = "#" + hashtag

    if consumerKey is None:
        consumerKey = os.environ.get('CONSUMER_KEY')

    if consumerSecret is None:
        consumerSecret = os.environ.get('CONSUMER_SECRET')

    if accessToken is None:
        accessToken = os.environ.get('ACCESS_TOKEN')

    if accessSecret is None:
        accessSecret = os.environ.get('ACCESS_TOKEN_SECRET')

    if (consumerKey is None) or (consumerSecret is None) or (accessToken is None)\
        or (accessSecret is None):
        print('You have not provided one or more of the arguments needed to run this script.\
            \nPlease run this script with the --help flag to see your options.')
        sys.exit(1)
   
    arguments_list = [hashtag, consumerKey, consumerSecret, accessToken, accessSecret]

    return arguments_list 

# Remove double quotes, single quotes, commas, newlines, tabs
def dataCleaning(input):
    input = input\
                .replace('\n', '') \
                .replace('\r', '') \
                .replace('\t', '') \
                .replace(',', '') \
                .replace('\"', '') \
                .replace('\'', '')
    return input

def searchTweets(arguments_list):
    HASHTAG = arguments_list[0]
    CONSUMER_KEY = arguments_list[1]
    CONSUMER_SECRET = arguments_list[2]
    ACCESS_TOKEN = arguments_list[3]
    ACCESS_TOKEN_SECRET = arguments_list[4]

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth,wait_on_rate_limit=True)

    '''
    We are using the cursor API to make sure that we get more than the tweets
    shown on one page (can't be more than 100 as per Twitter API's limitations.)
    '''
    tweet_number = 0
    for tweet in tweepy.Cursor(api.search, 
                    q=HASHTAG, 
                    count=100, 
                    tweet_mode='extended',
                    since='2018-07-01').items():
        
        # Increment the tweet number
        tweet_number += 1

        # Get the json part
        tweet = json.dumps(tweet._json)

        # Load the tweets
        tweet = json.loads(tweet)

        # We only need selected parts of the json
        tweet_date = str(tweet['created_at'])
        tweet_date = dataCleaning(tweet_date)

        tweet_id = str(tweet['id'])
        tweet_id = dataCleaning(tweet_id)

        tweet_text = str(tweet['full_text'].encode('utf-8'))
        tweet_text = dataCleaning(tweet_text)

        tweet_meta_result_type = str(tweet['metadata']['result_type'])
        tweet_meta_result_type = dataCleaning(tweet_meta_result_type)

        tweet_language = str(tweet['metadata']['iso_language_code'].encode('UTF-8'))
        tweet_language = dataCleaning(tweet_language)

        tweet_user_id = str(tweet['user']['id'])
        tweet_user_id = dataCleaning(tweet_user_id)

        tweet_user_name = str(tweet['user']['name'].encode('UTF-8'))
        tweet_user_name = dataCleaning(tweet_user_name)

        tweet_user_screen_name = str(tweet['user']['screen_name'].encode('UTF-8'))
        tweet_user_screen_name = dataCleaning(tweet_user_screen_name)

        tweet_user_location = str(tweet['user']['location'].encode('UTF-8'))
        tweet_user_location = dataCleaning(tweet_user_location)
        # If there's no location set
        if tweet_user_location == "":
            tweet_user_location = "NULL"
        
        tweet_user_friends_count = str(tweet['user']['friends_count'])
        tweet_user_friends_count = dataCleaning(tweet_user_friends_count)
        # If there are not friends
        if tweet_user_friends_count is "":
            tweet_user_friends_count = 0

        tweet_retweet = str(tweet['retweeted'])
        tweet_retweet = dataCleaning(tweet_retweet)

        tweet_retweet_count = str(tweet['retweet_count'])
        tweet_retweet_count = dataCleaning(tweet_retweet_count)
        # If no retweets
        if tweet_retweet_count is "":
            tweet_retweet_count = 0

        tweet_followers_count = str(tweet['user']['followers_count'])
        tweet_followers_count = dataCleaning(tweet_followers_count)
        # If no followers       
        if tweet_followers_count is "":
            tweet_followers_count = 0

        tweet_url = "https://twitter.com/" + tweet_user_screen_name + \
                "/status/" + tweet_id

        # Print number of tweets found so far. This is only informational data
        if tweet_number == 1:
            print "%d tweet found. Adding to the CSV file." %tweet_number
        else:
            print "%d tweets found. Adding to the CSV file." %tweet_number

        # Store it in a CSV file locally that we'll move to HDFS later
        filename = HASHTAG[1:]
        with open('%s-tweets.csv' %filename, mode='a') as tweet_file:
            tweet_writer = csv.writer(tweet_file, delimiter=',', \
                quotechar='"', \
                quoting=csv.QUOTE_MINIMAL)
            tweet_writer.writerow([tweet_date, 
                                tweet_id, \
                                tweet_text,\
                                tweet_meta_result_type,\
                                tweet_language,\
                                tweet_user_id,\
                                tweet_url,\
                                tweet_user_name,\
                                tweet_user_screen_name,\
                                tweet_user_location,\
                                tweet_user_friends_count,\
                                tweet_retweet,\
                                tweet_retweet_count,\
                                tweet_followers_count])

def main():
    args = inputArguments()
    arguments_list = inspectArguments()
    print "Starting to search Tweets. Hang on..."

    try:
        searchTweets(arguments_list)
        HASHTAG = args.hashtag
        if HASHTAG is None:
            HASHTAG = "donaldtrump"
        print "Tweets saved in the file %s-tweets.csv" %HASHTAG
    except:
        print "Something went wrong, tweets coudn't be downloaded. Please check the logs."
    
if __name__ == "__main__":
    main()
