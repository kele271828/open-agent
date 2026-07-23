import os
import json

class ConfigManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._config_file = "config.json"
            cls._instance._data = {}
            cls._instance.reload()
        return cls._instance

    def reload(self):
        """从 JSON 加载配置到内存"""
        if os.path.exists(self._config_file):
            with open(self._config_file, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        else:
            self._data = {
                "base": {}, "api": {}, "security": {},
                "system": {}, "locations": {}
            }

    def save(self):
        """将内存中的配置持久化到 JSON"""
        with open(self._config_file, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=4, ensure_ascii=False)

    # --- 1. 基础设置 (Base) ---
    @property
    def MODEL_NAME(self):
        return self._data.get("base", {}).get("MODEL_NAME", "qwen3.5-plus")
    @MODEL_NAME.setter
    def MODEL_NAME(self, value):
        self._data["base"]["MODEL_NAME"] = value

    @property
    def AI_NAME(self):
        return self._data.get("base", {}).get("AI_NAME", "AI助手")
    @AI_NAME.setter
    def AI_NAME(self, value):
        self._data["base"]["AI_NAME"] = value

    # --- 2. API 设置 (API) ---
    @property
    def TODO_BASE_URL(self):
        return self._data.get("api", {}).get("TODO_BASE_URL", "http://localhost:5001")
    @TODO_BASE_URL.setter
    def TODO_BASE_URL(self, value):
        self._data["api"]["TODO_BASE_URL"] = value

    @property
    def TODO_USER_ID(self):
        return self._data.get("api", {}).get("TODO_USER_ID", "")
    @TODO_USER_ID.setter
    def TODO_USER_ID(self, value):
        self._data["api"]["TODO_USER_ID"] = value

    @property
    def TODO_PASSWORD(self):
        return self._data.get("api", {}).get("TODO_PASSWORD", "")
    @TODO_PASSWORD.setter
    def TODO_PASSWORD(self, value):
        self._data["api"]["TODO_PASSWORD"] = value

    @property
    def LLM_BASE_URL(self):
        return self._data.get("api", {}).get(
            "LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    @LLM_BASE_URL.setter
    def LLM_BASE_URL(self, value):
        self._data["api"]["LLM_BASE_URL"] = value

    @property
    def LLM_API_KEY(self):
        key = self._data.get("api", {}).get("LLM_API_KEY", "")
        if not key or key == "YOUR_ALIYUN_API_KEY_HERE":
            key = os.getenv("ALI_API_KEY", "")
        return key
    @LLM_API_KEY.setter
    def LLM_API_KEY(self, value):
        self._data["api"]["LLM_API_KEY"] = value

    # --- 3. 文件系统安全设置 (Security) ---
    @property
    def ALLOWED_DRIVE(self):
        return os.path.abspath(self._data.get("security", {}).get("ALLOWED_DRIVE", "D:\\"))
    @ALLOWED_DRIVE.setter
    def ALLOWED_DRIVE(self, value):
        self._data["security"]["ALLOWED_DRIVE"] = value

    @property
    def ALLOWED_EXTENSIONS(self):
        return set(self._data.get("security", {}).get("ALLOWED_EXTENSIONS", []))
    @ALLOWED_EXTENSIONS.setter
    def ALLOWED_EXTENSIONS(self, value_set):
        self._data["security"]["ALLOWED_EXTENSIONS"] = list(value_set)

    @property
    def ALLOWED_IMAGE_EXTENSIONS(self):
        return set(self._data.get("security", {}).get("ALLOWED_IMAGE_EXTENSIONS", []))
    @ALLOWED_IMAGE_EXTENSIONS.setter
    def ALLOWED_IMAGE_EXTENSIONS(self, value_set):
        self._data["security"]["ALLOWED_IMAGE_EXTENSIONS"] = list(value_set)

    @property
    def WHITELIST_PATHS(self):
        paths = self._data.get("security", {}).get("WHITELIST_PATHS", [])
        return {os.path.abspath(p) for p in paths}
    @WHITELIST_PATHS.setter
    def WHITELIST_PATHS(self, path_set):
        self._data["security"]["WHITELIST_PATHS"] = list(path_set)

    @property
    def BLACKLIST_PATHS(self):
        paths = self._data.get("security", {}).get("BLACKLIST_PATHS", [])
        return {os.path.abspath(p) for p in paths}
    @BLACKLIST_PATHS.setter
    def BLACKLIST_PATHS(self, path_set):
        self._data["security"]["BLACKLIST_PATHS"] = list(path_set)

    @property
    def ALLOWED_WRITE_EXTENSIONS(self):
        return set(self._data.get("security", {}).get("ALLOWED_WRITE_EXTENSIONS", []))
    @ALLOWED_WRITE_EXTENSIONS.setter
    def ALLOWED_WRITE_EXTENSIONS(self, value_set):
        self._data["security"]["ALLOWED_WRITE_EXTENSIONS"] = list(value_set)

    @property
    def MAX_WRITE_SIZE(self):
        mb_size = self._data.get("security", {}).get("MAX_WRITE_SIZE_MB", 5)
        return mb_size * 1024 * 1024
    @MAX_WRITE_SIZE.setter
    def MAX_WRITE_SIZE(self, bytes_size):
        self._data["security"]["MAX_WRITE_SIZE_MB"] = bytes_size / (1024 * 1024)

    # --- 4. 应用与系统设置 (System) ---
    @property
    def APP_REGISTRY(self):
        return self._data.get("system", {}).get("APP_REGISTRY", {})
    @APP_REGISTRY.setter
    def APP_REGISTRY(self, registry_dict):
        self._data["system"]["APP_REGISTRY"] = registry_dict

    @property
    def ALLOWED_PROCESSES(self):
        return set(self._data.get("system", {}).get("ALLOWED_PROCESSES", []))
    @ALLOWED_PROCESSES.setter
    def ALLOWED_PROCESSES(self, process_set):
        self._data["system"]["ALLOWED_PROCESSES"] = list(process_set)

    # --- 5. 位置 (Locations) ---
    @property
    def MY_LOCATIONS(self):
        locs = self._data.get("locations", {}).get("MY_LOCATIONS", {})
        return {k: tuple(v) for k, v in locs.items()}
    @MY_LOCATIONS.setter
    def MY_LOCATIONS(self, locs_dict):
        self._data["locations"]["MY_LOCATIONS"] = {k: list(v) for k, v in locs_dict.items()}


# 向后兼容别名（旧代码可能引用）
class _CompatProxy:
    """代理：将旧的 YS_* 属性名映射到新的 TODO_* 属性"""
    _target = None

    @property
    def _cfg(self):
        if self._target is None:
            self._target = ConfigManager()
        return self._target

    @property
    def YS_BASE_URL(self):
        return self._cfg.TODO_BASE_URL
    @YS_BASE_URL.setter
    def YS_BASE_URL(self, value):
        self._cfg.TODO_BASE_URL = value

    @property
    def YS_USER_ID(self):
        return self._cfg.TODO_USER_ID
    @YS_USER_ID.setter
    def YS_USER_ID(self, value):
        self._cfg.TODO_USER_ID = value

    @property
    def YS_PASSWORD(self):
        return self._cfg.TODO_PASSWORD
    @YS_PASSWORD.setter
    def YS_PASSWORD(self, value):
        self._cfg.TODO_PASSWORD = value

    def __getattr__(self, name):
        return getattr(self._cfg, name)

config = _CompatProxy()
