import json
import copy
from typing import Any, Callable, Dict, Iterator, List, Optional

from aqt import mw
from aqt.qt import *

from .window import ConfigWindow


class ConfigManager:
    def __init__(self) -> None:
        self.config_window: Optional[ConfigWindow] = None
        self.config_tabs: List[Callable] = []
        self._config: Optional[Dict] = None
        addon_dir = mw.addonManager.addonFromModule(__name__)
        self.addon_dir = addon_dir
        self.addon_name = mw.addonManager.addon_meta(addon_dir).human_name()
        self._default = mw.addonManager.addonConfigDefaults(addon_dir)
        self.load()

    def load(self) -> None:
        "Loads config from disk"
        self._config = mw.addonManager.getConfig(__name__)

    def save(self) -> None:
        "Writes its config data to disk."
        mw.addonManager.writeConfig(__name__, self._config)

    def load_defaults(self) -> None:
        "call .save() afterwards to restore defaults."
        self._config = copy.deepcopy(self._default)

    def to_json(self) -> str:
        return json.dumps(self._config)

    def get_from_dict(self, dict_obj: dict, key: str) -> Any:
        "Raises KeyError if config doesn't exist"
        levels = key.split('.')
        return_val = dict_obj
        for level in levels:
            if isinstance(return_val, list):
                level = int(level)
            return_val = return_val[level]
        return return_val

    def copy(self) -> Dict:
        return copy.deepcopy(self._config)

    def get(self, key: str, default: Any = None) -> Any:
        "Returns default or None if config dones't exist"
        try:
            return self.get_from_dict(self._config, key)
        except KeyError:
            return default

    def get_default(self, key: str) -> Any:
        return self.get_from_dict(self._default, key)

    def set(self, key: str, value: Any) -> None:
        levels = key.split('.')
        conf_obj = self._config
        for i in range(len(levels) - 1):
            level = levels[i]
            if isinstance(conf_obj, list):
                level = int(level)
            try:
                conf_obj = conf_obj[level]
            except KeyError:
                conf_obj[level] = {}
                conf_obj = conf_obj[level]
        conf_obj[levels[-1]] = value

    def pop(self, key: str) -> Any:
        levels = key.split('.')
        conf_obj = self._config
        for i in range(len(levels) - 1):
            level = levels[i]
            if isinstance(conf_obj, list):
                level = int(level)
            try:
                conf_obj = conf_obj[level]
            except KeyError:
                return None
        return conf_obj.pop(levels[-1])

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        "This function only modifies the internal config data. Call conf.save() to actually write to disk"
        self.set(key, value)

    def __iter__(self) -> Iterator:
        return iter(self._config)

    def __delitem__(self, key: str) -> Any:
        self.pop(key)

    def __contains__(self, key: str) -> bool:
        try:
            self.get_from_dict(self._config, key)
            return True
        except KeyError:
            return False
        # Config Window

    def use_custom_window(self) -> None:
        def open_config() -> bool:
            config_window = ConfigWindow(self)
            for tab in self.config_tabs:
                tab(config_window)
            config_window.on_open()
            config_window.exec_()
            self.config_window = config_window
            return True
        mw.addonManager.setConfigAction(__name__, open_config)

    def add_config_tab(self, tab: Callable[["ConfigWindow"], None]) -> None:
        self.config_tabs.append(tab)
