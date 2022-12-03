#!/usr/bin/env python

import json
import os
import time
from json import JSONDecodeError

import utils.desktop_parser as desktop_parser
from config import FILE_ENCODING, CONFIG_DIR, USER_PATCH_CONFIG_FILE, USER_APPLICATIONS_DIR, \
    SYS_APPLICATIONS_DIR
from utils.cmd import Cmdline


def write_config_json(d: dict):
    with open(USER_PATCH_CONFIG_FILE, "w", encoding=FILE_ENCODING) as _f:
        json.dump(d, _f, sort_keys=True, indent=4, separators=(', ', ': '))


def read_config_json():
    with open(USER_PATCH_CONFIG_FILE, "r", encoding=FILE_ENCODING) as f:
        try:
            loaded = json.load(f)
        except JSONDecodeError:
            print("Json parse error, some typo maybe in your config file, please check it: %s" % USER_PATCH_CONFIG_FILE)
        else:
            return loaded


def get_input_judgement():
    choose = input().strip().lower()
    if choose == 'y' or choose == 'yes':
        return True
    return False


def update_desktop_cache():
    print("Refreshing desktop cache, waiting for 10s")
    Cmdline.run("sudo update-desktop-database --quiet")
    time.sleep(10)


def patch_app(app_desktop_path: str, _patches: dict):
    parser = desktop_parser.load(app_desktop_path)
    for section in _patches.keys():
        if len(_patches[section].keys()) == 0:
            continue
        if section.startswith('[') and section.endswith('['):
            section = section.removeprefix('[').removesuffix(']')
        print("Patching entry: [%s]" % section)
        parser.add_section(section)
        for k in _patches[section].keys():
            print("\tPatching attribute: %s=%s" % (k, _patches[section][k]))
            parser.set_pair(section, k, _patches[section][k])
    return parser.to_string()


# make sure config dir is exists
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

config_json = {}

# Create needing directory
if not os.path.exists(USER_APPLICATIONS_DIR):
    os.makedirs(USER_APPLICATIONS_DIR)

# Read config or create default config
if os.path.exists(USER_PATCH_CONFIG_FILE):
    config_json = read_config_json()
else:
    write_config_json(config_json)

if len(config_json.keys()) == 0:
    print("No patch found, exiting...")
    print("Let's add a new patch into config file: %s" % USER_PATCH_CONFIG_FILE)
    exit(0)

task_cnt = 0
for desktop in config_json.keys():
    task_cnt += 1
    # get patch first
    patches = config_json[desktop]
    # fix filename
    if not desktop.endswith(".desktop"):
        desktop += ".desktop"

    sys_desktop_path = os.path.join(SYS_APPLICATIONS_DIR, desktop)
    user_desktop_path = os.path.join(USER_APPLICATIONS_DIR, desktop)

    print("Task %d -> %s:" % (task_cnt, desktop))
    if os.path.exists(sys_desktop_path):
        print("Copying .desktop file")
        Cmdline.run("sudo cp -f %s %s" % (sys_desktop_path, user_desktop_path))

        patched_user_desktop_str = patch_app(user_desktop_path, patches)
        # Set owner info, prepare to write
        Cmdline.run("sudo chown %d:%d %s" % (os.getgid(), os.getuid(), user_desktop_path))
        with open(user_desktop_path, "w", encoding=FILE_ENCODING) as f:
            f.write(patched_user_desktop_str)
        print("Done")
    else:
        print("WARN: Target .desktop file is not exists, skipping")
    print()
