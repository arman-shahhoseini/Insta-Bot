import logging
import time
from datetime import datetime, timedelta, timezone
from instagrapi import Client
import random


class InstagramBot:
    def __init__(self, username, password, session_file="session.json"):
        self.username = username
        self.password = password
        self.session_file = session_file
        self.client = Client(delay_range=[1,2])
        self._setup_logger()
        self.processed_posts = set()
        self.emojis = ["👌", "🔥", "😍", "💯", "👏", "✨", "❤️", "👍", "🤩", "🙌"]

    def _setup_logger(self):
        """تنظیم لاگ‌گیری"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("instagram_bot.log", encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def login(self):
        """ورود به حساب کاربری"""
        try:
            self.client.load_settings(self.session_file)
            self.client.login(username=self.username, password=self.password)
            self.logger.info("Login successful using session file.")
        except Exception as e:
            self.logger.warning(f"Failed to load session file: {e}")
            self.client.login(username=self.username, password=self.password)
            self.client.dump_settings(self.session_file)
            self.logger.info("Login successful and session file updated.")

    def fetch_explore_reels(self, count=1):
        """دریافت پست‌های اکسپلور (Reels)"""
        try:
            reels = self.client.explore_reels(count)
            self.logger.info(f"Fetched {len(reels)} reels from Explore.")
            return reels
        except Exception as e:
            self.logger.error(f"Failed to fetch explore reels: {e}")
            return []

    def generate_comment(self):
        """تولید کامنت با استفاده از ایموجی‌های تصادفی"""
        return " ".join(random.sample(self.emojis, 2))  # انتخاب دو ایموجی تصادفی

    def process_post(self, post):
        """پردازش هر پست"""
        post_pk = post.pk

        if post_pk in self.processed_posts:
            self.logger.info(f"Post {post_pk} already processed. Skipping...")
            self.logger.info("=" * 50)
            return

        post_caption = post.caption_text if post.caption_text else "بدون کپشن"
        post_url = post.video_url if post.video_url else "بدون ویدیو"

        # بررسی تعداد لایک و ویو
        if post.like_count < 100:  # اگر تعداد لایک یا ویو کم بود، کامنت نده
            self.logger.info(f"Skipping post {post_pk} due to low likes or views.")
            self.logger.info("=" * 50)
            return

        self.logger.info(f"Processing Post - PK: {post_pk}")
        self.logger.info(f"Caption: {post_caption}")
        self.logger.info(f"URL: {post_url}")

        # لایک کردن
        try:
            media_id = self.client.media_id(post_pk)
            self.client.media_like(media_id)
            self.logger.info("Liked successfully.")
        except Exception as e:
            self.logger.error(f"Failed to like the post: {e}")

        # ارسال کامنت
        try:
            generated_comment = self.generate_comment()
            if generated_comment.strip():
                self.client.media_comment(media_id, text=generated_comment)
                self.logger.info(f"Comment sent successfully: {generated_comment}")
        except Exception as e:
            self.logger.error(f"Failed to comment: {e}")

        self.processed_posts.add(post_pk)

    def filter_recent_posts(self, posts, days=7):
        """فیلتر کردن پست‌هایی که در بازه زمانی اخیر (تعداد روز مشخص) ارسال شده‌اند"""
        one_week_ago = datetime.now(timezone.utc) - timedelta(days=days)  # تاریخ 7 روز قبل با توجه به UTC
        recent_posts = [
            post for post in posts
            if post.taken_at and post.taken_at.replace(tzinfo=timezone.utc) > one_week_ago
        ]
        self.logger.info(f"Filtered {len(recent_posts)} posts from the last {days} days.")
        return recent_posts

    def run(self, explore_count=1, delay=60):
        """اجرای بات"""
        self.login()
        posts = self.fetch_explore_reels(count=explore_count)
        recent_posts = self.filter_recent_posts(posts, days=7)  # فیلتر کردن پست‌های 7 روز اخیر
        for post in recent_posts:
            self.process_post(post)
            time.sleep(delay)
            self.logger.info("=" * 50)


if __name__ == "__main__":
    bot = InstagramBot(username="your_username", password="your_password")
    bot.run(explore_count=5, delay=60)
