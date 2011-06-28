# Required PIL classes may or may not be available from the root namespace
# depending on the installation method used.
try:
    import Image
    import ImageFile
    import ImageFilter
    import ImageEnhance
    import ImageColor
    import ImageCms
    import ImageStat
except ImportError:
    try:
        from PIL import Image
        from PIL import ImageFile
        from PIL import ImageFilter
        from PIL import ImageEnhance
        from PIL import ImageColor
        from PIL import ImageCms
        from PIL import ImageStat
        
    except ImportError:
        raise ImportError('ImageKit was unable to import the Python Imaging Library. Please confirm it`s installed and available on your current Python path.')


"""
it ain't where you from,
it's where you at.
"""
import os
IK_ROOT = os.path.dirname(os.path.realpath(__file__))

"""
set RUNMODE for sync/async operation
TODO: put this in settings.py, maybe like:

    try:
        IK_RUNMODE = settings.IK_RUNMODE
    except AttributeError:
        IK_RUNMODE = ... # I don't know yet.

"""

IK_SYNC = 0             # synchronous operation -- fire imagekit signals concurrently with save() and IK cache methods
IK_ASYNC_MGMT = 1       # async operation -- we are running from the command line, fire imagekit signals concurrently
IK_ASYNC_DAEMON = 2     # async operation -- deque images from cache, fire imagekit signals but don't save
IK_ASYNC_REQUEST = 3    # async operation -- queue up images (in leu of sending imagekit signals) on save() and IK cache methods

IK_RUNMODE = IK_SYNC


