import arg_functions
import os
import shutil
import threading
from time import time
from sys import exit, argv


class GetExistingFiles(threading.Thread):
    def __init__(self, location):
        threading.Thread.__init__(self)
        self.files = set()
        self.location = location

    def run(self):
        """ Get list of files currently in backup """
        for root, dirs, files in os.walk(self.location):
            for file in files:
                path = os.path.join(root, file)[len(self.location):]
                self.files.add(path)


class Colour:
    """ Colour text in console. From https://stackoverflow.com/questions/6537487/changing-shell-text-color-windows """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARN = '\033[93m'
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
        self.prev_len = 50
        self.length = length
        self.update(" " * 50)

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


def removed_files(files, location):
    """ Let user decide what to do with files that have been moved / deleted """
    print(f"{Colour.WARN}There are {Colour.FAIL}{len(files)}{Colour.WARN} files in this backup "
          f"that no longer exist!\n(These files may have been deleted or moved to a different location)")
    print(f"{Colour.ENDC}Keep all (1) | Delete all (2) | Choose individually (3)")

    kept = []

    choice = None
    while choice not in ["1", "2", "3"]:
        choice = input(f"{Colour.OKGREEN}>>>{Colour.ENDC} ")
        if choice not in ["1", "2", "3"]: print(f"{Colour.FAIL}Must enter 1, 2 or 3{Colour.ENDC}")

    # Choice 1: keep all files in difference
    if choice == "1":
        for file in files:
            path = location + file
            kept.append(path)

    # Choice 2: delete all files in difference
    elif choice == "2":
        clear_prev = ""
        for file in files:
            path = location + file
            os.remove(path)
            print(f"Deleting {'...' if len(path) > 60 else ''}{path[max(0, len(path) - 60):]}{clear_prev}", end="\r")
            clear_prev = " " * max(0, 60 - len(path))
        print("Deleted!" + " " * 70)

    # Choice 3: user decides
    elif choice == "3":
        print("Keep (1) | Remove (2)")

        for file in files:
            path = location + file
            action = input(("..." if len(path) > 60 else "") + path[max(0, len(path) - 60):] + " ")

            # delete file
            if action == "2":
                os.remove(path)
                print("Deleted!")

            # keep file
            else:
                kept.append(path)
                print("        ")

            # reset line
            print("\x1b[A\x1b[A" + " " * 70, end="\r")
        print()

    # always keep kept files?
    if kept:
        always_keep = input(f"{Colour.WARN}Kept {Colour.FAIL}{len(kept)} {Colour.WARN}files! Always keep these "
                            f"files? {Colour.ENDC}(Y / n) ")

        if always_keep.lower() == "y":
            arg_functions.ensure_exists("alwaysKeepFiles.txt")

            keep_list = open("alwaysKeepFiles.txt", "a")
            for file in kept:
                keep_list.write(file + "\n")
            keep_list.close()


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
        print(f"{Colour.HEADER}Backing up to {location}{Colour.ENDC}\n")
        bar = ProgressBar(file_count)
        start_time = time()
        total_size = 0
        new_files = 0
        updated_files = 0

        existing = GetExistingFiles(location)
        existing.start()
        current = set()

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

                    current.add(src[2:])

                    total_size += os.path.getsize(dst)
                    bar.update(src)

        bar.complete()

        # Stats for this backup location
        print(f"\n{Colour.OKBLUE}New files:\t{Colour.ENDC}{new_files}")
        print(f"{Colour.OKBLUE}Updated files:\t{Colour.ENDC}{updated_files}")
        print(f"{Colour.OKBLUE}Total files:\t{Colour.ENDC}{file_count}")

        # Display size of backup
        backup_size = round(total_size / 1000000.0, 2)
        size = round(backup_size / 1000.0, 2) if backup_size > 1000 else backup_size
        units = 'Mb' if backup_size <= 1000 else 'Gb'
        print(f"{Colour.OKGREEN}Backup size:\t{Colour.ENDC}{size} {units}")

        # Display time taken for backup
        total_time = time() - start_time
        minutes = total_time // 60
        minutes = "" if minutes == 0 else "1 minute " if minutes == 1 else f"{minutes} minutes "
        seconds = "1 second" if int(total_time) % 60 == 1 else f"{int(total_time) % 60} seconds"
        print(f"{Colour.OKGREEN}Time taken:\t{Colour.ENDC}{minutes}{seconds}\n")

        # Files that aren't in the backup anymore
        existing.join()
        existing = existing.files
        difference = existing.difference(current)

        try:
            # Check if files are in alwaysKeepFiles.txt before asking user
            keep_list = open("alwaysKeepFiles.txt", "r")
            files = keep_list.readlines()
            keep_list.close()

            keep_list = open("alwaysKeepFiles.txt", "w")

            for file in files:
                file_path = file.strip("\n")

                # only keep files in alwaysKeepFiles.txt if the are still in backup folder
                if os.path.exists(file_path):
                    keep_list.write(file)

                # remove file from differences if it's marked as always keep
                file_path = file_path[len(location):]
                if file_path in difference: difference.remove(file_path)

            keep_list.close()
        except FileNotFoundError:
            pass

        # finally, prompt users about any remaining files
        if len(difference) > 0:
            difference = list(difference)
            removed_files(difference, location)

        # Remove empty directories in backup location
        removed = 0
        for root, dirs, files in os.walk(location):
            for directory in dirs:
                directory = os.path.join(root, directory)
                if len(os.listdir(directory)) == 0:
                    try:
                        os.rmdir(directory)
                        removed += 1
                    except PermissionError:
                        pass
        
        if removed > 0:
            dirs = "directory" if removed == 1 else "directories"
            print(f"{Colour.WARN}Removed {Colour.FAIL}{removed}{Colour.WARN} empty {dirs} from {location}{Colour.ENDC}")


if __name__ == '__main__':
    parse_args()
    backup()
