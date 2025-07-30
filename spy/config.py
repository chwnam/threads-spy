from dataclasses import dataclass
from os.path import exists as path_exists

from dotenv import dotenv_values


@dataclass
class Config:
    chromium_path: str
    headless: bool
    port: int
    user_data_dir: str
    pause: int = 1

    @staticmethod
    def load(env_path):
        env = dotenv_values(env_path)

        chromium_path = env['CHROMIUM_PATH'] if 'CHROMIUM_PATH' in env else 'chromium'
        headless = bool(int(env['HEADLESS'])) if 'HEADLESS' in env else True
        port = int(env['PORT']) if 'PORT' in env else 9222
        user_data_dir = env['USER_DATA_DIR'] if 'USER_DATA_DIR' in env else None
        pause = int(env['PAUSE']) if 'PAUSE' in env else 5

        if not user_data_dir:
            raise ValueError('user_data_dir is required')
        if not path_exists(user_data_dir):
            raise ValueError('user_data_dir not found')

        return Config(
            chromium_path=chromium_path,
            headless=headless,
            port=port,
            user_data_dir=user_data_dir,
            pause=pause,
        )
