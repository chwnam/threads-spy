from spy.browser import Browser
from spy.config import Config
from spy.post import Post
from json import dumps as json_dumps
from sys import argv

if '__main__' == __name__:
    if 2 > len(argv):
        print('Usage: python fetch.py <url>')
        exit(1)

    config = Config.load('.env')
    browser = Browser(config)
    post = Post(browser)

    output = post.fetch(argv[1])
    result = json_dumps(output, indent=2, ensure_ascii=False)
    print(result)
