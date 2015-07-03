import os
import time
import shutil
from multiprocessing import Process, Queue
import win32con
import win32file
import argparse
from balloontip import show_balloon_tip


def win32monitor(q, path_to_watch, monitor_subfolders=False):
    """
    Function that monitors a folder for changes. Based on Win32API.
    This function blocks its caller!
    :param q: Queue to put results (tuple (action, file)).
    :param path_to_watch: String path of the directory that will be watched.
    :param monitor_subfolders: boolean, True if subdirs should be watched.
    """
    FILE_LIST_DIRECTORY = 0x0001
    handle_dir = win32file.CreateFile(
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
        monitor_subfolders,                         # Watch subdirectories?
        # win32con.FILE_NOTIFY_CHANGE_FILE_NAME |     # Flags for WHAT should be notified
        # win32con.FILE_NOTIFY_CHANGE_DIR_NAME |      # Changes in DIR name
        # win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |    # Changes in files attributes
        win32con.FILE_NOTIFY_CHANGE_SIZE |          # Changes in files size
        win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,    # Changes in file modification timestamp
        # win32con.FILE_NOTIFY_CHANGE_SECURITY,       # changes in security attrs
        None,                                       # overlapped (for async)
        None                                        # completion routine
    )
    q.put(results)   # adds results to queue


# Program start
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='vigil')
    parser.add_argument('-s', '--source', help='Source file',required=True)
    parser.add_argument('-d', '--destination',help='Destination path/file', required=True)
    args = parser.parse_args()

    ACTIONS = {
        1: "Created",
        2: "Deleted",
        3: "Updated",
        4: "Renamed from",
        5: "Renamed to"
    }

    watched_file = args.source
    destination = args.destination

    # watched_file = "C:\\testfolder\\test.txt"
    # destination = "C:\\testfolder\\dest"
    source_path, source_file = os.path.split(watched_file)
    destination_folder, destination_file = os.path.split(destination)

    if os.path.splitext(destination_file)[1] == '':
        print "Your destination path contains no extension, and will be interpreted as a directory. " \
              "Original filename will be preserved. \n Enter A to abort, or anything else to continue."
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
            queue = Queue()
            proc = Process(target=win32monitor, args=(queue, source_path, False))
            proc.start()
            print "Process started. IS ALIVE: " + str(proc.is_alive())
            while queue.empty():
                time.sleep(5)
                # print "Still monitoring..."
            results = queue.get()
            for action, changed_file in results:
                # full_filename = os.path.join(source_path, changed_file)
                # print full_filename, ACTIONS.get(action, "Unknown")
                if changed_file == source_file and action == 3:
                    print 'A modification was detected in ' + changed_file
                    print 'Moving it to ' + destination_folder + ' as ' + destination_file
                    shutil.copy(watched_file, destination)
                    show_balloon_tip("vigil.py", "Moving " + watched_file + " to " + destination)

        except KeyboardInterrupt:
            print "Killing process..."
            proc.terminate()
            while not proc.is_alive():
                time.sleep(0.5)
            print "Process terminated."
            break
