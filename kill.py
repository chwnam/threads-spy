from spy.browser import Browser
from spy.config import Config

if '__main__' == __name__:
    Browser(Config.load('.env')).kill()
