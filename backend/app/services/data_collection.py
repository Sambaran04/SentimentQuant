import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import tweepy
import asyncpraw
from app.core.config import settings
from app.db.mongodb import get_database
from app.services.sentiment_analysis import sentiment_analyzer

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.db = get_database()
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.news_api_key = settings.NEWS_API_KEY
        
        # Twitter API setup
        self.twitter_client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
        )
        
        # Reddit API setup
        self.reddit_client = asyncpraw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT
        )
        
        self.websocket_clients = set()
        self.rate_limits = {
            'alpha_vantage': {'calls': 0, 'last_reset': datetime.utcnow()},
            'news_api': {'calls': 0, 'last_reset': datetime.utcnow()},
            'twitter': {'calls': 0, 'last_reset': datetime.utcnow()},
            'reddit': {'calls': 0, 'last_reset': datetime.utcnow()}
        }

    async def check_rate_limit(self, api: str, limit: int, window: int = 60) -> bool:
        """
        Check if we're within rate limits for an API.
        """
        now = datetime.utcnow()
        if (now - self.rate_limits[api]['last_reset']).seconds >= window:
            self.rate_limits[api] = {'calls': 0, 'last_reset': now}
        
        if self.rate_limits[api]['calls'] >= limit:
            return False
        
        self.rate_limits[api]['calls'] += 1
        return True

    async def fetch_price_data(self, symbol: str, interval: str = '1d') -> Optional[Dict]:
        """
        Fetch price data from Alpha Vantage API.
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://www.alphavantage.co/query"
                params = {
                    "function": "TIME_SERIES_DAILY" if interval == '1d' else "TIME_SERIES_INTRADAY",
                    "symbol": symbol,
                    "apikey": self.alpha_vantage_key,
                    "outputsize": "compact"
                }
                if interval != '1d':
                    params["interval"] = interval

                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching price data: {response.status}")
                        return None

                    data = await response.json()
                    if "Error Message" in data:
                        logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                        return None

                    # Process and store the data
                    time_series_key = "Time Series (Daily)" if interval == '1d' else f"Time Series ({interval})"
                    if time_series_key not in data:
                        return None

                    price_data = []
                    for timestamp, values in data[time_series_key].items():
                        price_data.append({
                            'symbol': symbol,
                            'timestamp': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                            'open': float(values['1. open']),
                            'high': float(values['2. high']),
                            'low': float(values['3. low']),
                            'close': float(values['4. close']),
                            'volume': int(values['5. volume'])
                        })

                    # Store in database
                    if price_data:
                        await self.store_price_data(price_data)
                        return price_data[-1]  # Return latest data point

        except Exception as e:
            logger.error(f"Error in fetch_price_data: {str(e)}")
            return None

    async def fetch_news_data(self, symbol: str, days: int = 1) -> List[Dict]:
        """
        Fetch news data from News API.
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://newsapi.org/v2/everything"
                params = {
                    "q": symbol,
                    "apiKey": self.news_api_key,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "from": (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
                }

                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching news data: {response.status}")
                        return []

                    data = await response.json()
                    if data['status'] != 'ok':
                        return []

                    # Process and store news data
                    news_data = []
                    for article in data['articles']:
                        news_item = {
                            'symbol': symbol,
                            'title': article['title'],
                            'description': article['description'],
                            'content': article['content'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'published_at': datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                            'timestamp': datetime.utcnow()
                        }
                        
                        # Analyze sentiment
                        sentiment = await sentiment_analyzer.analyze_text(
                            f"{article['title']} {article['description']} {article['content']}"
                        )
                        news_item.update(sentiment)
                        
                        news_data.append(news_item)

                    # Store in database
                    if news_data:
                        await self.store_news_data(news_data)

                    return news_data

        except Exception as e:
            logger.error(f"Error in fetch_news_data: {str(e)}")
            return []

    async def fetch_twitter_data(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        Fetch tweets about a symbol using Twitter API v2.
        """
        try:
            if not await self.check_rate_limit('twitter', 450, 900):  # 450 requests per 15 minutes
                logger.warning("Twitter API rate limit reached")
                return []

            # Search for tweets containing the symbol
            query = f"${symbol} OR #{symbol} -is:retweet"
            tweets = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=limit,
                tweet_fields=['created_at', 'public_metrics', 'lang'],
                user_fields=['username', 'public_metrics']
            )

            if not tweets.data:
                return []

            twitter_data = []
            for tweet in tweets.data:
                # Get user data
                user = next((u for u in tweets.includes['users'] if u.id == tweet.author_id), None)
                
                # Analyze sentiment
                sentiment = await sentiment_analyzer.analyze_text(tweet.text)
                
                twitter_data.append({
                    'symbol': symbol,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'metrics': tweet.public_metrics,
                    'username': user.username if user else None,
                    'user_metrics': user.public_metrics if user else None,
                    'timestamp': datetime.utcnow(),
                    **sentiment
                })

            # Store in database
            if twitter_data:
                await self.store_social_data(twitter_data, 'twitter')

            return twitter_data

        except Exception as e:
            logger.error(f"Error in fetch_twitter_data: {str(e)}")
            return []

    async def fetch_reddit_data(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        Fetch Reddit posts and comments about a symbol.
        """
        try:
            if not await self.check_rate_limit('reddit', 60, 60):  # 60 requests per minute
                logger.warning("Reddit API rate limit reached")
                return []

            subreddits = ['stocks', 'investing', 'wallstreetbets', 'stockmarket']
            reddit_data = []

            for subreddit_name in subreddits:
                subreddit = await self.reddit_client.subreddit(subreddit_name)
                
                # Search for posts
                async for submission in subreddit.search(f"${symbol} OR {symbol}", limit=limit//len(subreddits)):
                    # Get comments
                    submission.comments.replace_more(limit=0)
                    comments = []
                    async for comment in submission.comments:
                        comments.append({
                            'text': comment.body,
                            'score': comment.score,
                            'created_at': datetime.fromtimestamp(comment.created_utc)
                        })

                    # Analyze sentiment for post and comments
                    post_sentiment = await sentiment_analyzer.analyze_text(submission.title + " " + submission.selftext)
                    comment_sentiments = [await sentiment_analyzer.analyze_text(c['text']) for c in comments]

                    reddit_data.append({
                        'symbol': symbol,
                        'type': 'post',
                        'title': submission.title,
                        'text': submission.selftext,
                        'score': submission.score,
                        'created_at': datetime.fromtimestamp(submission.created_utc),
                        'subreddit': subreddit_name,
                        'url': submission.url,
                        'comments': comments,
                        'timestamp': datetime.utcnow(),
                        **post_sentiment,
                        'comment_sentiments': comment_sentiments
                    })

            # Store in database
            if reddit_data:
                await self.store_social_data(reddit_data, 'reddit')

            return reddit_data

        except Exception as e:
            logger.error(f"Error in fetch_reddit_data: {str(e)}")
            return []

    async def store_price_data(self, price_data: List[Dict]) -> None:
        """
        Store price data in MongoDB.
        """
        try:
            collection = self.db.price_data
            await collection.insert_many(price_data)
        except Exception as e:
            logger.error(f"Error storing price data: {str(e)}")

    async def store_news_data(self, news_data: List[Dict]) -> None:
        """
        Store news data in MongoDB.
        """
        try:
            collection = self.db.news_data
            await collection.insert_many(news_data)
        except Exception as e:
            logger.error(f"Error storing news data: {str(e)}")

    async def store_social_data(self, social_data: List[Dict], source: str) -> None:
        """
        Store social media data in MongoDB.
        """
        try:
            collection = self.db.social_data
            for item in social_data:
                item['source'] = source
            await collection.insert_many(social_data)
        except Exception as e:
            self.websocket_clients.add(websocket)
            while True:
                # Fetch latest price data
                price_data = await self.fetch_price_data(symbol, interval='1min')
                if price_data:
                    await websocket.send_json({
                        'type': 'price',
                        'data': price_data
                    })

                # Fetch latest news
                news_data = await self.fetch_news_data(symbol, days=1)
                if news_data:
                    await websocket.send_json({
                        'type': 'news',
                        'data': news_data
                    })

                await asyncio.sleep(60)  # Update every minute

        except Exception as e:
            logger.error(f"Error in real-time streaming: {str(e)}")
        finally:
            self.websocket_clients.remove(websocket)

    async def stop_real_time_streaming(self, websocket) -> None:
        """
        Stop real-time data streaming for a websocket client.
        """
        if websocket in self.websocket_clients:
            self.websocket_clients.remove(websocket)

data_collector = DataCollector() 