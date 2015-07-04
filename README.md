# vigil.py
Windows tool that monitors a file and copies it to another location when it is updated.

This little script uses the pywin32 (aka win32api) to monitor the specified file for changes. When a change is detected, it copies the file to another location. Straight-forward stuff.

I created this to automate the process of moving my dev builds to a local Dropbox folder for testing in several devices.

# Usage:
```
python vigil.py -s C:/sourcefolder/sourcefile.txt -d C:/destinationfolder/destinationfile.txt
```
Alternatively, to maintain the file name, simply ommit it in the destination, as in:
```
python vigil.py -s C:/sourcefolder/sourcefile.txt -d C:/destinationfolder
```

To show a notification in the Windows notification area include flag `-b` when calling `vigil.py` (requires `balloontip.py`). 

And that's it. Even though the used API is blocking, it is running in a separate process. So feel free to interrupt the program at anytime (KeyboardInterrupt/CTRL+C).

# Dependencies
A Windows operating system, obvisouly. Mostly because of pywin32. Get it at: http://sourceforge.net/projects/pywin32/ or:
```
pip install pypiwin32
```

If using flag `-b`, `balloontip.py` is required.

# Thanks to
Tim Golden for his incredibly useful post: http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html
