import base

from mylib import ConfigLoader


cfg = ConfigLoader(config_path="./config")

cfg.show_config()

cfg.show_config(simple=True)
