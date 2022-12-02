#!/usr/bin/env python

import json
import os
import time
from json import JSONDecodeError
from os import stat

import utils.desktop_parser as desktop_parser
from config import FILE_ENCODING, CONFIG_DIR, USER_PATCH_CONFIG_FILE, USER_APPLICATIONS_DIR, USER_BACKUP_DIR, \
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
if not os.path.exists(USER_BACKUP_DIR):
    os.makedirs(USER_BACKUP_DIR)

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

    target_not_link = True
    do_patch = True
    # get patch first
    patches = config_json[desktop]
    # fix filename
    if not desktop.endswith(".desktop"):
        desktop += ".desktop"

    sys_desktop_path = os.path.join(SYS_APPLICATIONS_DIR, desktop)
    user_desktop_path = os.path.join(USER_APPLICATIONS_DIR, desktop)
    user_backup_desktop_path = os.path.join(USER_BACKUP_DIR, desktop)

    print("Task %d -> %s:" % (task_cnt, desktop))
    if os.path.exists(sys_desktop_path):
        if os.path.islink(sys_desktop_path):
            print("WARN: Target .desktop file is a symbolic link, it's maybe patched")
            if os.path.exists(user_desktop_path):
                print("NOTE: Patched .desktop file found!")
                print("Use patched file to recreate link? [y/N(or empty)] ", end="")
                if not get_input_judgement():
                    print("Skipped")
                    continue
                else:
                    target_not_link = False
                print("Use config to re-patch file? [y/N(or empty)] ", end="")
                if not get_input_judgement():
                    do_patch = False
            else:
                print("WARN: Patched .desktop also not found, skipping")
                continue
        if target_not_link:
            print("Copying .desktop file")
            Cmdline.run("sudo cp -f %s %s" % (sys_desktop_path, user_desktop_path))
            is_backup_desktop_file = True
            if os.path.exists(user_backup_desktop_path):
                print("Found old backup file, overwritten it? [y/N(or empty)] ")
                if not get_input_judgement():
                    is_backup_desktop_file = False
            if is_backup_desktop_file:
                print("Backing up .desktop file")
                Cmdline.run("sudo cp -f %s %s" % (sys_desktop_path, user_backup_desktop_path))

        if do_patch:
            patched_user_desktop_str = patch_app(user_desktop_path, patches)
            # Get original owner info
            owner_grp, owner_usr = stat(user_desktop_path).st_gid, stat(user_desktop_path).st_uid
            # Set owner info, prepare to write
            Cmdline.run("sudo chown %d:%d %s" % (os.getgid(), os.getuid(), user_desktop_path))
            with open(user_desktop_path, "w", encoding=FILE_ENCODING) as f:
                f.write(patched_user_desktop_str)
            # Restore owner info
            Cmdline.run("sudo chown %d:%d %s" % (owner_grp, owner_usr, user_desktop_path))
            print("Patch successful at %s" % user_desktop_path)

        # Remove old .desktop file
        print("Removing old target .desktop file")
        Cmdline.run("sudo rm -rf %s" % sys_desktop_path)
        update_desktop_cache()

        # Create symbolic link
        print("Creating symbolic link:\n\t%s ->\n\t%s" % (user_desktop_path, sys_desktop_path))
        Cmdline.run("sudo ln -s %s %s" % (user_desktop_path, sys_desktop_path))
        print("Done")
    else:
        print("WARN: Target .desktop file is not exists, skipping")
    print()
