from typing import List, Dict, Optional
import tweepy
import praw
import aiohttp
from datetime import datetime, timedelta
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class SocialMediaAnalyzer:
    def __init__(self):
        # Initialize Twitter client
        self.twitter_client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
        )
        
        # Initialize Reddit client
        self.reddit_client = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT
        )

    async def get_twitter_posts(self, symbol: str, count: int = 100) -> List[Dict]:
        """Fetch tweets about a symbol"""
        try:
            # Search for tweets containing the symbol
            tweets = self.twitter_client.search_recent_tweets(
                query=f"${symbol} OR {symbol}",
                max_results=count,
                tweet_fields=['created_at', 'public_metrics', 'lang']
            )
            
            return [{
                "text": tweet.text,
                "created_at": tweet.created_at,
                "metrics": tweet.public_metrics,
                "source": "twitter"
            } for tweet in tweets.data or []]
        except Exception as e:
            logger.error(f"Error fetching tweets: {str(e)}")
            return []

    async def get_reddit_posts(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Fetch Reddit posts about a symbol"""
        try:
            # Search in multiple subreddits
            subreddits = ['stocks', 'investing', 'wallstreetbets']
            posts = []
            
            for subreddit_name in subreddits:
                subreddit = self.reddit_client.subreddit(subreddit_name)
                search_results = subreddit.search(symbol, limit=limit//len(subreddits))
                
                for post in search_results:
                    posts.append({
                        "text": f"{post.title} {post.selftext}",
                        "created_at": datetime.fromtimestamp(post.created_utc),
                        "metrics": {
                            "score": post.score,
                            "num_comments": post.num_comments
                        },
                        "source": "reddit",
                        "subreddit": subreddit_name
                    })
            
            return posts
        except Exception as e:
            logger.error(f"Error fetching Reddit posts: {str(e)}")
            return []

    async def get_social_media_posts(self, symbol: str) -> List[Dict]:
        """Get posts from multiple social media platforms"""
        tasks = [
            self.get_twitter_posts(symbol),
            self.get_reddit_posts(symbol)
        ]
        
        results = await asyncio.gather(*tasks)
        all_posts = []
        
        # Combine and sort posts
        for platform_posts in results:
            all_posts.extend(platform_posts)
        
        all_posts.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        return all_posts

    async def get_social_media_summary(self, symbol: str) -> Dict:
        """Get a summary of social media activity for a symbol"""
        posts = await self.get_social_media_posts(symbol)
        
        # Calculate engagement metrics
        total_engagement = sum(
            post.get("metrics", {}).get("retweet_count", 0) +
            post.get("metrics", {}).get("like_count", 0) +
            post.get("metrics", {}).get("num_comments", 0)
            for post in posts
        )
        
        return {
            "symbol": symbol,
            "total_posts": len(posts),
            "total_engagement": total_engagement,
            "platforms": {
                "twitter": len([p for p in posts if p["source"] == "twitter"]),
                "reddit": len([p for p in posts if p["source"] == "reddit"])
            },
            "latest_posts": posts[:5] if posts else [],
            "timestamp": datetime.utcnow()
        }

social_media_analyzer = SocialMediaAnalyzer() 