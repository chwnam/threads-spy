from os.path import basename
from time import sleep

from psutil import process_iter, ZombieProcess
from subprocess import call as subproc_call
from playwright.sync_api import sync_playwright

from spy.config import Config


class Browser:
    def __init__(self, config: Config):
        self.config = config

    def get_browser(self):
        if not self.is_running():
            self.launch()

        uri = 'http://localhost:{}'.format(self.config.port)
        playwright = sync_playwright().start()

        return playwright.chromium.connect_over_cdp(uri)

    def is_running(self):
        the_name = basename(self.config.chromium_path)
        the_arg = '--remote-debugging-port={}'.format(self.config.port)

        for proc in process_iter():
            try:
                if the_name == proc.name() and proc.cmdline().index(the_arg) >= 0:
                    return True
            except ValueError:
                continue
            except ZombieProcess:
                continue

        return False

    def kill(self):
        the_name = basename(self.config.chromium_path)
        the_arg = '--remote-debugging-port={}'.format(self.config.port)
        for proc in process_iter():
            try:
                if the_name == proc.name() and proc.cmdline().index(the_arg) >= 0:
                    proc.kill()
            except ValueError:
                continue
            except ZombieProcess:
                continue

    def launch(self):
        cmd = '{} {} --remote-debugging-port={} --user-data-dir={} > /dev/null 2>&1 &'.format(
            self.config.chromium_path,
            '--headless' if self.config.headless else '',
            self.config.port,
            self.config.user_data_dir,
        )
        print(cmd)
        subproc_call(cmd, shell=True)
        sleep(self.config.pause)

