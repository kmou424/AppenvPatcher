import os

FILE_ENCODING = "utf-8"

SYS_APPLICATIONS_DIR = f"/usr/share/applications"

HOME_PATH = os.getenv("HOME")

CONFIG_DIR = os.path.join(HOME_PATH, ".config/appenv_patcher")

USER_PATCH_CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
USER_APPLICATIONS_DIR = os.path.join(CONFIG_DIR, "applications")
USER_BACKUP_DIR = os.path.join(CONFIG_DIR, "backup")
