import praw
import csv
import re
import json   
import requests
from textblob import TextBlob
import nltk
# Download VADER, if not downloaded
# nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
sia = SentimentIntensityAnalyzer()

client_ids="YkfkaYL9JKVtOw"

client_secrets="z5A3msQ3xWqvHq2a3-KF43tulAA94A"

user_agents="James"

reddit=praw.Reddit(client_id=client_ids,client_secret=client_secrets,user_agent=user_agents,username=usernames,password=passwords)

class StockPost(object):
    def __init__(self, postID, postURL, ups, text,downs, numComments, stock,positive,negative,neutral):
        self.postID = postID
        self.url = postURL
        self.stock = stock
        self.ups = ups
        self.text=text
        self.downs = downs
        self.numComments = numComments
        self.positive=positive
        self.negative=negative
        self.neutral=neutral

    
    def jsonEnc(self):
      return {'stock': self.stock, 'postID': self.postID, 'postURL': self.url, 'ups': self.ups, 'downs': self.downs, 'text':self.text, 'numComments': self.numComments,'positive':self.positive,'neutral':self.neutral,'negative':self.negative}

def jsonDefEncoder(obj):
    if hasattr(obj, 'jsonEnc'):
        return obj.jsonEnc()
    else: #some default behavior
        return obj.__dict__
def text_blob_sentiment(review, sub_entries_textblob,stockSentiment,stock):
    analysis = TextBlob(review)
    if analysis.sentiment.polarity >= 0.0001:
        if analysis.sentiment.polarity > 0:
            sub_entries_textblob['positive'] = sub_entries_textblob['positive'] + 1
            stockSentiment[stock]['positive']=stockSentiment[stock]['positive']+1
            return 'Positive'

    elif analysis.sentiment.polarity <= -0.0001:
        if analysis.sentiment.polarity <= 0:
            sub_entries_textblob['negative'] = sub_entries_textblob['negative'] + 1
            stockSentiment[stock]['negative']=stockSentiment[stock]['negative']+1

            return 'Negative'
    else:
        sub_entries_textblob['neutral'] = sub_entries_textblob['neutral'] + 1
        stockSentiment[stock]['neutral']=stockSentiment[stock]['neutral']+1
        return 'Neutral'
    
def merge(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
           for item in b[key]:
               a[key][item] = b[key][item]
    return a

# sentiment analysis function for VADER tool
def nltk_sentiment(review, sub_entries_nltk,stockSentiment,stock):
    vs = sia.polarity_scores(review)
    if not vs['neg'] > 0.05:
        if vs['pos'] - vs['neg'] > 0:
            sub_entries_nltk['positive'] = sub_entries_nltk['positive'] + 1
            stockSentiment[stock]['positive']=stockSentiment[stock]['positive']+1
            return 'Positive'
        else:
            sub_entries_nltk['neutral'] = sub_entries_nltk['neutral'] + 1
            stockSentiment[stock]['neutral']=stockSentiment[stock]['neutral']+1
            return 'Neutral'

    elif not vs['pos'] > 0.05:
        if vs['pos'] - vs['neg'] <= 0:
            sub_entries_nltk['negative'] = sub_entries_nltk['negative'] + 1
            stockSentiment[stock]['negative']=stockSentiment[stock]['negative']+1
            return 'Negative'
        else:
            sub_entries_nltk['neutral'] = sub_entries_nltk['neutral'] + 1
            stockSentiment[stock]['neutral']=stockSentiment[stock]['neutral']+1
            return 'Neutral'
    else:
        sub_entries_nltk['neutral'] = sub_entries_nltk['neutral'] + 1
        stockSentiment[stock]['neutral']=stockSentiment[stock]['neutral']+1
        return 'Neutral'
def update_stock(stockTickers,stock,post):
                        stockTickers[str(stock)]['postID'].append(post.id)
                        stockTickers[str(stock)]['postURL'].append(post.permalink)
                        stockTickers[str(stock)]['text'].append(post.selftext)
                        stockTickers[str(stock)]['ups']+=post.ups
                        stockTickers[str(stock)]['downs']+=post.downs
                        stockTickers[str(stock)]['numComments']+=post.num_comments

class SubredditScraper:

    def __init__(self, sub, sort='new', lim=900):
        self.sub = sub
        self.sort = sort
        self.lim = lim

        print(
            f'SubredditScraper instance created with values '
            f'sub = {sub}, sort = {sort}, lim = {lim}')

    def set_sort(self):
        if self.sort == 'new':
            return self.sort, reddit.subreddit(self.sub).new(limit=self.lim)
        elif self.sort == 'top':
            return self.sort, reddit.subreddit(self.sub).top(limit=self.lim)
        elif self.sort == 'hot':
            return self.sort, reddit.subreddit(self.sub).hot(limit=self.lim)
        else:
            self.sort = 'hot'
            print('Sort method was not recognized, defaulting to hot.')
            return self.sort, reddit.subreddit(self.sub).hot(limit=self.lim)

    def get_posts(self):
        sub_entries_textblob = {'negative': 0, 'positive' : 0, 'neutral' : 0}
        sub_entries_nltk = {'negative': 0, 'positive' : 0, 'neutral' : 0}
       
        stockSentiment={}
        stockTickers = {}
        with open('tickers.csv', mode='r') as infile:
            reader = csv.reader(infile)
            for row in reader:
                row[0]=row[0][:row[0].index(",")]
                stockTickers[row[0]] = {'stock': row[0], 'postID':[], 'postURL': [], 'ups': 0, 'downs': 0, 'text':[], 'numComments': 0,'positive':0,'neutral':0,'negative':0}

                stockSentiment[row[0]] = {'negative': 0, 'positive' : 0, 'neutral' : 0}
        """Get unique posts from a specified subreddit."""

        # Attempt to specify a sorting method.
        sort, subreddit = self.set_sort()

        print(f'Collecting information from r/{self.sub}.')
        mentionedStocks = []
        i = 0
        for post in subreddit:
            i = i + 1
            print(i,post.title,post.link_flair_text)
            if post.link_flair_text != 'Meme':
                for stock in stockTickers.keys():

                    if(re.search(r'\s+\$?' + stock + r'\$?\s+', post.selftext) or re.search(r'\s+\$?' + stock + r'\$?\s+',  post.title)):
                        print("/n",stock)

                        text_blob_sentiment(post.title, sub_entries_textblob,stockSentiment,stock)
                        nltk_sentiment(post.title, sub_entries_nltk,stockSentiment,stock)
                        update_stock(stockTickers,stock,post)
       # for stock in stockTickers:
        #    if (len(stockTickers[stock]) > 0):
         #       for post in stockTickers[stock]:
          #          mentionedStocks.append(stockTickers[stock][post]) 
        #json_object = json.dumps(mentionedStocks, default=jsonDefEncoder, indent = 4)   
       # print(json_object) 
        merge(stockTickers,stockSentiment)
        print(stockTickers['GME'])

        headers = {'Content-type':'application/json', 'Accept':'application/json' }
      #  r = requests.post("https://localhost:44360/api/RedditPostsAdmin", data=json_object,  verify=False, headers=headers)
       # print(r.status_code)
        



if __name__ == '__main__':
    SubredditScraper('wallstreetbets', lim=200, sort='hot').get_posts()
