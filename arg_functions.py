import os


def show_help():
    print("""
    Backup files to various locations.
    Each backup location serves as a root directory, so file structure will be preserved
    
    PATH:   path to desired location (ex. C:\\Users\\YourName\\Documents)
            can be either a folder or individual file.

    optional arguments:
      -h, --help            show this help message
      
      -addpath PATH         add path that will be backed up
      -removepath PATH      remove path from backup list
      -listpaths            show all backup paths
      -clearpaths           remove all backup paths
      
      -addlocation PATH     add location where files will be backed up to
      -removelocation PATH  remove backup location
      -listlocations        show all backup locations
      -clearlocations       remove all backup locations
    """)


def ensure_exists(file):
    """ If the file does not exist, create it """
    if not os.path.exists(file):
        path_file = open(file, "x")
        path_file.close()


def add_path(path):
    ensure_exists("backupPaths.txt")

    paths_file = open("backupPaths.txt", "r")
    paths = paths_file.readlines()
    paths_file.close()

    if not os.path.exists(path):
        print(f"path '{path}' does not exist!")
        exit()

    if path + "\n" not in paths:
        paths_file = open("backupPaths.txt", "a")
        paths_file.write(path + "\n")
        paths_file.close()

        print("Added path to backup paths.")
        list_paths()
    else:
        print(f"path '{path}' already in paths!")
        exit()


def remove_path(rpath):
    ensure_exists("backupPaths.txt")

    paths_file = open("backupPaths.txt", "r")
    paths = paths_file.readlines()
    paths_file.close()

    paths_file = open("backupPaths.txt", "w")
    for path in paths:
        if path.strip("\n") != rpath:
            paths_file.write(path)
    paths_file.close()

    print("Removed path from backup paths.")
    list_paths()


def list_paths():
    ensure_exists("backupPaths.txt")

    backup_paths = open("backupPaths.txt", "r")
    print("Paths:\n")
    print(backup_paths.read())
    print("--------")
    backup_paths.close()


def clear_paths():
    ensure_exists("backupPaths.txt")

    backup_paths = open("backupPaths.txt", "w")
    backup_paths.close()


def add_backup_location(location):
    ensure_exists("backupLocations.txt")

    locations_file = open("backupLocations.txt", "r")
    locations = locations_file.readlines()
    locations_file.close()

    if not os.path.exists(location):
        if input(f"path '{location}' does not exist!\n Create directory? (y/N) ").lower() in ["y", "yes"]:
            try:
                os.mkdir(location)
                print("Directory creation succeeded!")
            except OSError:
                print("Directory creation failed!")
        else:
            exit()

    if location + "\n" not in locations:
        locations_file = open("backupLocations.txt", "a")
        locations_file.write(location + "\n")
        locations_file.close()

        print("Added path to backup locations.")
        list_backup_locations()
    else:
        print(f"path '{location}' already in backup locations!")
        exit()


def remove_backup_location(remove_location):
    ensure_exists("backupLocations.txt")

    locations_file = open("backupLocations.txt", "r")
    locations = locations_file.readlines()
    locations_file.close()

    locations_file = open("backupLocations.txt", "w")
    for location in locations:
        if location.strip("\n") != remove_location:
            locations_file.write(location)
    locations_file.close()

    print("Removed path from backup locations.")
    list_backup_locations()


def list_backup_locations():
    ensure_exists("backupLocations.txt")

    locations = open("backupLocations.txt", "r")
    print("Locations:\n")
    print(locations.read())
    print("--------")
    locations.close()


def clear_backup_locations():
    ensure_exists("backupLocations.txt")

    backup_locations = open("backupLocations.txt", "w")
    backup_locations.close()
