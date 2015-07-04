import os
import time
import shutil
from multiprocessing import Process, Queue
import win32con
import win32file
import argparse

def win32monitor(q, path_to_watch, monitor_subfolders=False):
    """
    Function that monitors a folder for changes. Based on Win32API.
    This function blocks its caller!
    :param q: Queue to put results (tuple (action, file)).
    :param path_to_watch: String path of the directory that will be watched.
    :param monitor_subfolders: boolean, True if subdirs should be watched.
    """
    FILE_LIST_DIRECTORY = 0x0001                # access
    handle_dir = win32file.CreateFile(          # This creates a handle to the directory to be watched
        path_to_watch,                          # dir path
        FILE_LIST_DIRECTORY,                    # access
        win32con.FILE_SHARE_READ |              # share modes
        win32con.FILE_SHARE_WRITE |             #
        win32con.FILE_SHARE_DELETE,             #
        None,                                   #
        win32con.OPEN_EXISTING,                 #
        win32con.FILE_FLAG_BACKUP_SEMANTICS,    # flags
        None                                    #
    )
    results = win32file.ReadDirectoryChangesW(
        handle_dir,                                 # handle
        1024,                                       # buffer size
        monitor_subfolders,                         # monitor subdirectories?
        win32con.FILE_NOTIFY_CHANGE_SIZE |          # Changes in files size
        win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,    # Changes in file modification timestamp
        None,                                       # overlapped (for async)
        None                                        # completion routine
    )
    q.put(results)   # adds results to queue


# Program start
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='vigil')
    parser.add_argument('-s', '--source', help='Source file',required=True)
    parser.add_argument('-d', '--destination', help='Destination path/file', required=True)
    parser.add_argument('-b', '--balloon', action="store_true", help='Use balloon notification. Requires balloontip.py')
    args = parser.parse_args()
    if args.balloon:
        try:
            from balloontip import show_balloon_tip
        except ImportError:
            print "\nballoontip.py not found. Ignoring option."
            args.balloon = False

    watched_file = args.source
    destination = args.destination

    source_path, source_file = os.path.split(watched_file)
    destination_folder, destination_file = os.path.split(destination)

    if os.path.splitext(destination_file)[1] == '':
        print "\nYour destination path contains no extension, and will be interpreted as a directory. " \
              "Original filename will be preserved. \nEnter A to abort, or anything else to continue."
        if raw_input().lower() == 'a':
            print 'Aborting...'
            raise SystemExit(0)
        else:
            destination_file = source_file
            destination_folder = destination

    # Main Loop
    while 1:
        print "Monitoring... Use CTRL + C to terminate anytime."
        try:
            """
            Queue + Process instead of threading because win32monitor is blocking.
            Without using join(), the user is able to get out of loop by CTRL + C,
            and the running process can be safely terminated.
            """
            modification_time = os.stat(watched_file).st_mtime
            queue = Queue()
            proc = Process(target=win32monitor, args=(queue, source_path, False))
            proc.start()
            print "Process started. IS ALIVE: " + str(proc.is_alive())
            while queue.empty():
                proc.join(5)
            #  Wait a bit before checking (in case the watched file is edited right after the triggering event)
            time.sleep(0.05)
            if os.stat(watched_file).st_mtime != modification_time:
                print 'A modification was detected in ' + source_file
                print 'Moving it to ' + destination_folder + ' as ' + destination_file
                shutil.copy(watched_file, destination)
                if args.balloon:
                    show_balloon_tip("vigil.py", "Moving " + watched_file + " to " + destination)
        except KeyboardInterrupt:
            print "Killing process..."
            proc.terminate()
            while not proc.is_alive():
                time.sleep(0.5)
            print "Process terminated."
            break
