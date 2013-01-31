def generate(file):
    file.generate()


try:
    from celery.task import task
except ImportError:
    pass
else:
    generate_task = task(generate)


def generate_deferred(file):
    try:
        import celery  # NOQA
    except:
        raise ImportError("Deferred validation requires the the 'celery' library")
    generate_task.delay(file)


def clear_now(file):
    file.clear()
