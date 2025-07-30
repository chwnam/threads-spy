from json import loads as json_loads
from typing import Dict

from jmespath import search as jmespath_search
from nested_lookup import nested_lookup
from parsel import Selector
from playwright.sync_api import sync_playwright, ViewportSize
from re import compile as re_compile

from spy.browser import Browser


class Post(object):
    def __init__(self, browser: Browser):
        self.browser = browser
        self.regex = re_compile(r"^https://www\.threads\.com/@([^/]+)/post/([^/]+)$")
        self.user = ''
        self.post = ''

    @staticmethod
    def parse_thread(data: Dict) -> Dict:
        """Parse Twitter tweet JSON dataset for the most important fields"""
        result = jmespath_search(
            """{
            text: post.caption.text,
            published_on: post.taken_at,
            id: post.id,
            pk: post.pk,
            code: post.code,
            username: post.user.username,
            user_pic: post.user.profile_pic_url,
            user_verified: post.user.is_verified,
            user_pk: post.user.pk,
            user_id: post.user.id,
            has_audio: post.has_audio,
            reply_count: view_replies_cta_string,
            like_count: post.like_count,
            images: post.carousel_media[].image_versions2.candidates[1].url,
            image_count: post.carousel_media_count,
            videos: post.video_versions[].url
        }""",
            data,
        )

        single_image = jmespath_search('{image: post.image_versions2.candidates[0].url}', data)
        if not result['images'] and single_image and single_image['image']:
            result["images"] = [single_image['image']]
            result["image_count"] = 1

        result["videos"] = list(set(result["videos"] or []))

        if result["reply_count"] and type(result["reply_count"]) != int:
            result["reply_count"] = int(result["reply_count"].split(" ")[0])

        result["url"] = f"https://www.threads.com/@{result['username']}/post/{result['code']}"

        return result

    def validate_url(self, url: str):
        match = self.regex.search(url)

        if not match:
            raise ValueError("Invalid url. Only thread single post urls are supported.")

        self.user = match.group(1)
        self.post = match.group(2)

    def fetch(self, url: str):
        self.validate_url(url)

        browser = self.browser.get_browser()

        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = browser.new_context(viewport=ViewportSize(width=1024, height=768))

        if context.pages:
            page = context.pages[0]
        else:
            page = context.new_page()

        page.goto(url)

        # wait for page to finish loading
        page.wait_for_selector("[data-pressable-container=true]")

        # find all hidden datasets
        selector = Selector(page.content())
        hidden_datasets = selector.css('script[type="application/json"][data-sjs]::text').getall()

        # find datasets that contain threads data
        for hidden_dataset in hidden_datasets:
            # skip loading datasets that clearly don't contain threads data
            if '"ScheduledServerJS"' not in hidden_dataset:
                continue
            if "thread_items" not in hidden_dataset:
                continue

            data = json_loads(hidden_dataset)

            # datasets are heavily nested, use nested_lookup to find
            # the thread_items key for thread data
            thread_items = nested_lookup("thread_items", data)
            if not thread_items:
                continue

            # use our jmespath parser to reduce the dataset to the most important fields
            threads = [self.parse_thread(t) for thread in thread_items for t in thread]

            # filter only targeted object
            if self.user == threads[0]['username'] and self.post == threads[0]['code']:
                return {
                    "post": threads[0],
                    "replies": threads[1:],
                }

        raise ValueError("could not find thread data in page")
