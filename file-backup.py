import math
import arg_functions
import os
import shutil
import errno
import stat
from datetime import datetime
from time import time
from sys import exit, argv


class progress_bar:
    def __init__(self, total_size, length=20):
        self.total_size = total_size
        self.current_size = 0
        self.prev_file_name = ""
        self.length = length
        self.update(0, "")

    def update(self, size, file_name):
        """ Add data onto progress bar """
        self.current_size += size

        percentage = round(float(self.current_size) / self.total_size * self.length)
        filled = "█" * percentage
        empty = " " * (self.length - percentage)
        percentage *= 100 / self.length
        file_name = file_name.replace("\n", "")
        if len(file_name) > 50: file_name = file_name[:50] + "..."

        print(f"[{filled}{empty}] {round(percentage,1)}%\t{file_name}{' ' * len(self.prev_file_name)}", end="\r")

        self.prev_file_name = file_name

    def complete(self):
        """ Show completed bar """
        print(f"[{'█' * self.length}] 100%\tComplete!{' ' * len(self.prev_file_name)}")
        del self


def parse_args():
    # show help
    if '-h' in argv or "--help" in argv:
        arg_functions.show_help()

    # add backup location
    if '-addlocation' in argv:
        path = argv[argv.index('-addlocation') + 1]
        arg_functions.add_backup_location(path)

    # remove backup location
    if '-removelocation' in argv:
        path = argv[argv.index('-removelocation') + 1]
        arg_functions.remove_backup_location(path)

    # list backup locations
    if '-listlocations' in argv:
        arg_functions.list_backup_locations()

    # clear all paths
    if '-clearlocations' in argv:
        arg_functions.clear_backup_locations()

    # add path
    if '-addpath' in argv:
        path = argv[argv.index('-addpath') + 1]
        arg_functions.add_path(path)

    # remove path
    if '-removepath' in argv:
        path = argv[argv.index('-removepath') + 1]
        arg_functions.remove_path(path)

    # list paths
    if '-listpaths' in argv:
        arg_functions.list_paths()

    # clear all paths
    if '-clearpaths' in argv:
        arg_functions.clear_paths()

    # exit if any args
    if len(argv) != 1:
        exit()


def get_backup_locations():
    try:
        locations_file = open("backupLocations.txt", "r")

        locations = locations_file.read().split("\n")
        locations.remove("")
        if len(locations) == 0: raise FileNotFoundError

        locations_file.close()
        return locations

    except FileNotFoundError:
        print("No backup locations found! Add some using -addlocation PATH")
        exit()


def get_paths():
    try:
        paths_file = open("backupPaths.txt", "r")

        paths = paths_file.read().split("\n")
        paths.remove("")
        if len(paths) == 0: raise FileNotFoundError

        paths_file.close()
        return paths

    except FileNotFoundError:
        print("No paths found! Add some using -addpath PATH")
        exit()


def onerror(func, path, exc):
    """ handleRemoveReadonly.
    code from https://stackoverflow.com/questions/1213706/what-user-do-python-scripts-run-as-in-windows """
    excvalue = exc[1]

    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(path)
    else:
        raise


def get_backup_size(path=None):
    if path:
        sources = [path]
    else:
        sources = get_paths()
    backup_size = 0

    for source in sources:
        for root, dirs, files in os.walk(source):
            for file in files:
                file_path = os.path.join(root, file)
                if not os.path.islink(file_path):
                    backup_size += os.path.getsize(file_path)

    return backup_size


def backup():
    sources = get_paths()
    locations = get_backup_locations()
    create_time = datetime.now().strftime("%d%b%y_%H%M")
    total_size = get_backup_size()
    keep_versions = 2

    for location in locations:
        print(f"Backing up to {location}\n")
        bar = progress_bar(total_size, 30)

        for source in sources:
            for root, dirs, files in os.walk(source):
                if not os.path.exists(f"{location}\\{create_time}{root[2:]}"):
                    os.makedirs(f"{location}\\{create_time}{root[2:]}")

                for file in files:
                    file_path = os.path.join(root, file)
                    dest_path = f"{location}\\{create_time}{file_path[2:]}"
                    shutil.copyfile(file_path, dest_path)

                    bar.update(os.path.getsize(file_path), file_path)

        bar.complete()

        # remove old versions
        while len(os.listdir(location)) > keep_versions:
            oldest_version = None

            for version in os.listdir(location):
                path = os.path.join(location, version)
                create_date = os.stat(path).st_ctime

                if oldest_version is None or os.stat(oldest_version).st_ctime > create_date:
                    oldest_version = path

            print(
                f"Version limit reached! ({len(os.listdir(location))}/{keep_versions}) Removing old version {oldest_version}\n")
            shutil.rmtree(oldest_version, ignore_errors=False, onerror=onerror)

    return total_size


if __name__ == '__main__':
    try:
        backup_locations_file = open("backupLocations.txt", "x")
        backup_locations_file.close()
    except FileExistsError:
        pass

    try:
        backup_paths_file = open("backupPaths.txt", "x")
        backup_paths_file.close()
    except FileExistsError:
        pass

    parse_args()

    print("Starting backup\n")
    start_time = time()
    backup_size, failed_dirs = backup()
    backup_size = round(backup_size / 1000000.0, 2)

    minutes = f"{math.floor((time() - start_time) / 60.0)} {'minute' if int(time() - start_time) / 60 == 1 else 'minutes'}"
    print(f"Backup complete! took {minutes if time() - start_time >= 60 else ''} {int(time() - start_time) % 60} seconds")
    print(f"Backup size = {round(backup_size / 1000.0, 2) if backup_size > 1000 else backup_size} {'Mb' if backup_size <= 1000 else 'Gb'}")

    if failed_dirs:
        print("Unable to copy these directories")
        for path in failed_dirs:
            print(path)

    #  TODO: folders that were in previous backup but not in current
