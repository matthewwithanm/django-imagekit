def validate_now(file):
    file.validate()


try:
    from celery.task import task
except ImportError:
    pass
else:
    validate_now_task = task(validate_now)


def deferred_validate(file):
    try:
        import celery
    except:
        raise ImportError("Deferred validation requires the the 'celery' library")
    validate_now_task.delay(file)


def clear_now(file):
    file.clear()
