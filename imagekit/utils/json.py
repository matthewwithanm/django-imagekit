
# To consistently use the best-available JSON serializer, use:
#   from imagekit.utils import json
# ... so if you need to swap a library, do it there once.
# ... you can also import imagekit.utils.json directly to avoid
# circular references and the like.

try:
    import ujson as json
except ImportError:
    logg.info("--- Loading yajl in leu of ujson")
    try:
        import yajl as json
    except ImportError:
        logg.info("--- Loading simplejson in leu of yajl")
        try:
            import simplejson as json
        except ImportError:
            logg.info("--- Loading stdlib json module in leu of simplejson")
            import json

