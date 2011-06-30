"""
Django ImageKit

Author: Justin Driscoll <justin.driscoll@gmail.com>
Version: 0.3.6

"""
__author__ = 'Justin Driscoll, Bryan Veloso, Greg Newman, Chris Drackett'
__version__ = (0, 3, 6)

IK_SYNC = 0             # synchronous operation -- fire imagekit signals concurrently with save() and IK cache methods
IK_ASYNC_MGMT = 1       # async operation -- we are running from the command line, fire imagekit signals concurrently
IK_ASYNC_DAEMON = 2     # async operation -- deque images from cache, fire imagekit signals but don't save
IK_ASYNC_REQUEST = 3    # async operation -- queue up images (in leu of sending imagekit signals) on save() and IK cache methods
