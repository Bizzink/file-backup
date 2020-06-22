import math
import arg_functions
import os
import shutil
import errno
import stat
from datetime import datetime
from time import time
from sys import exit, argv


class Colour:
    """ Colour text in console. From https://stackoverflow.com/questions/6537487/changing-shell-text-color-windows """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# allows text to be colours using ANSI codes (for some reason), comment from ^
os.system('color')


class ProgressBar:
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
        percentage *= 100.0 / self.length
        file_name = file_name.replace("\n", "")
        if len(file_name) > 50: file_name = file_name[:50] + "..."

        print(f"[{filled}{empty}] {round(percentage, 1)}%\t{file_name}{' ' * max(0, 50 - len(self.prev_file_name))}", end="\r")

        self.prev_file_name = file_name

    def complete(self):
        """ Show completed bar """
        print(f"[{'█' * self.length}] 100%  Complete!{' ' * len(self.prev_file_name)}")
        del self


def parse_args():
    """ Parse command line arguments """
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


def get_paths(filename):
    """ Read file to get paths """
    try:
        paths_file = open(filename, "r")

        paths = paths_file.read().split("\n")
        paths.remove("")
        if len(paths) == 0: raise FileNotFoundError

        paths_file.close()
        return paths

    except FileNotFoundError:
        command = "-addpath" if filename == "backupPaths.txt" else "-addlocation"
        print(f"No paths found! Add some using {command} PATH")
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


def compare_prev_version(prev, current):
    """ Compare the previous backup with the current to see if there are any deleted files that may want to be kept """

    def get_files(root, sub_dir=None):
        """ Get path to each file from root """
        files = set()

        for path in os.listdir(root):
            full_path = os.path.join(root, path)
            if sub_dir: path = os.path.join(sub_dir, path)

            # get files from subdirectory
            if os.path.isdir(full_path):
                files.update(get_files(full_path, sub_dir=path))

            elif os.path.isfile(full_path):
                files.add(path)

        return files

    def copy(file):
        """ Copy file from prev to current """
        source = os.path.join(prev, file)
        dest = os.path.join(current, os.path.dirname(file))

        if not os.path.exists(dest):
            os.makedirs(dest)

        try:
            shutil.copy(source, dest)
        except PermissionError as e:
            source.replace('\\\\', '\\')
            return f"{Colour.FAIL}Unable to copy file! > {source}{Colour.ENDC}"

    prev_files = get_files(prev)
    current_files = get_files(current)

    if prev_files.issubset(current_files):
        return
    else:
        missing = list(prev_files.difference(current_files))

    print(f"{Colour.WARNING}There are {Colour.FAIL}{len(missing)}{Colour.WARNING} files in the previous backup that "
          f"are no longer in the current one!{Colour.ENDC}")

    if input("View files (Y) or ignore(n)? >>> ").lower() in ["y", ""]:
        print()
        for file in missing:
            print(file)
        print()

        choice = None
        while choice not in ["a", "n", "c"]:
            choice = input("Keep all(a) | Ignore all(n) | Choose individually(c) >>> ")
            if choice.lower() not in ["a", "n", "c"]:
                print(f"{Colour.WARNING}Invalid input! please enter a, n or c{Colour.ENDC}")

        print()

        failed_files = []

        if choice == "a":
            for file in missing:
                fail = copy(file)
                if fail: failed_files.append(fail)

        if choice == "c":

            for file in missing:
                print(file)
                choice = input("Keep (Enter) | Discard (n) >>> ")
                if choice.lower() != "n":
                    fail = copy(file)
                    if fail: failed_files.append(fail)

        if failed_files:
            for file in failed_files:
                print(file)


def get_size(path):
    total_size = 0

    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if not os.path.islink(file_path):
                total_size += os.path.getsize(file_path)

    return total_size


def backup():
    sources = get_paths("backupPaths.txt")
    locations = get_paths("backupLocations.txt")
    create_time = datetime.now().strftime("%d%b%y_%H%M")
    keep_versions = 2

    # get total size of all files
    print(f"{Colour.HEADER}Calculating size...{Colour.ENDC}")
    total_size = 0
    for source in sources:
        total_size += get_size(source)

    # backup to each location
    for location in locations:
        print(f"{Colour.OKBLUE}Backing up to {location}{Colour.ENDC}\n")
        bar = ProgressBar(total_size)
        prev_version = None

        # Find most recent backup in location
        for version in os.listdir(location):
            path = os.path.join(location, version)
            if prev_version is None or os.stat(path).st_ctime > os.stat(prev_version).st_ctime:
                prev_version = path

        # Copy files
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
        if prev_version: compare_prev_version(prev_version, f"{location}\\{create_time}")

        # remove old versions
        while len(os.listdir(location)) > keep_versions:
            oldest_version = None

            for version in os.listdir(location):
                path = os.path.join(location, version)
                create_date = os.stat(path).st_ctime

                if oldest_version is None or os.stat(oldest_version).st_ctime > create_date:
                    oldest_version = path

            version_count = len(os.listdir(location))
            print(f"{Colour.WARNING}Version limit reached! {Colour.FAIL}({version_count}/{keep_versions}){Colour.WARNING} Removing old version {oldest_version}{Colour.ENDC}\n")
            shutil.rmtree(oldest_version, ignore_errors=False, onerror=onerror)

        # calculate & display size of backup
        backup_size = round(get_size(f"{location}\\{create_time}") / 1000000.0, 2)
        size = round(backup_size / 1000.0, 2) if backup_size > 1000 else backup_size
        units = 'Mb' if backup_size <= 1000 else 'Gb'
        print(f"{Colour.OKGREEN}Backup size: {Colour.ENDC} {size} {units}")


if __name__ == '__main__':
    for file in ["backupLocations.txt", "backupPaths.txt"]:
        if not os.path.exists(file):
            path_file = open(file, "x")
            path_file.close()

    parse_args()

    start_time = time()
    backup()

    total_time = time() - start_time
    mins = math.floor(total_time / 60)
    mins = "" if mins == 0 else "1 minute " if mins == 1 else f"{mins} minutes "
    seconds = int(total_time) % 60
    seconds = "1 second" if seconds == 1 else f"{seconds} seconds"
    print(f"{Colour.OKGREEN}Backup complete!{Colour.ENDC} took {mins}{seconds}")
