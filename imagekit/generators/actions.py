def ensure_exists(file):
    file.ensure_exists()


try:
    from celery.task import task
except ImportError:
    pass
else:
    ensure_exists_task = task(ensure_exists)


def ensure_exists_deferred(file):
    try:
        import celery  # NOQA
    except:
        raise ImportError("Deferred validation requires the the 'celery' library")
    ensure_exists_task.delay(file)


def clear_now(file):
    file.clear()
