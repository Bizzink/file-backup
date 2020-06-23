import arg_functions
import os
import shutil
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
        self.prev_len = 0
        self.length = length
        self.update("")

    def update(self, file_name):
        """ Increase progress bar progress bar """
        self.current_size += 1

        percent = float(self.current_size) / self.total_size
        filled = "█" * int(percent * self.length)
        empty = " " * (self.length - int(percent * self.length))
        file_name = file_name.replace("\n", "")
        percent = percent * 100
        if len(file_name) > 50: file_name = file_name[:50] + "..."

        print(f"[{filled}{empty}] {round(percent, 1)}%\t{file_name}{' ' * max(0, 50 - self.prev_len)}", end="\r")

        self.prev_len = len(file_name)

    def complete(self):
        """ Show completed bar """
        print(f"[{'█' * self.length}] 100%  Complete!{' ' * self.prev_len}")
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


def backup():
    sources = get_paths("backupPaths.txt")
    locations = get_paths("backupLocations.txt")

    # Count total number of files in sources
    file_count = 0
    for source in sources:
        for root, dirs, files in os.walk(source):
            file_count += len(files)

    # Backup to each location
    for location in locations:
        print(f"{Colour.OKBLUE}Backing up to {location}{Colour.ENDC}\n")
        bar = ProgressBar(file_count)
        total_size = 0
        new_files = 0
        updated_files = 0

        # Copy files
        for source in sources:
            for root, dirs, files in os.walk(source):
                # Create directory if it isn't in backup
                if not os.path.exists(location + root[2:]):
                    os.makedirs(location + root[2:])

                for file in files:
                    src = os.path.join(root, file)
                    dst = location + src[2:]

                    # If file is not in backup, copy it
                    if not os.path.exists(dst):
                        shutil.copyfile(src, dst)
                        new_files += 1

                    # If file exists, but has been modified since last backup, copy it
                    elif os.stat(dst).st_mtime < os.stat(src).st_mtime:
                        shutil.copyfile(src, dst)
                        updated_files += 1

                    total_size += os.path.getsize(dst)
                    bar.update(src)

        bar.complete()

        print(f"\n{Colour.OKBLUE}New files added to backup: {Colour.ENDC}{new_files}")
        print(f"{Colour.OKBLUE}Updated existing files: {Colour.ENDC}{updated_files}")
        print(f"{Colour.OKBLUE}Total files: {Colour.ENDC}{file_count}")

        # display size of backup
        backup_size = round(total_size / 1000000.0, 2)
        size = round(backup_size / 1000.0, 2) if backup_size > 1000 else backup_size
        units = 'Mb' if backup_size <= 1000 else 'Gb'
        print(f"{Colour.OKGREEN}Backup size: {Colour.ENDC} {size} {units}\n")


if __name__ == '__main__':
    parse_args()
    start_time = time()
    backup()

    total_time = time() - start_time
    minutes = total_time // 60
    minutes = "" if minutes == 0 else "1 minute " if minutes == 1 else f"{minutes} minutes "
    seconds = "1 second" if int(total_time) % 60 == 1 else f"{int(total_time) % 60} seconds"
    print(f"{Colour.WARNING}Backup complete!{Colour.ENDC} took {minutes}{seconds}")

    # TODO: files in backup that no longer exist
