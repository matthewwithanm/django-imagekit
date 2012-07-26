from django.db.models.signals import post_init, post_save, post_delete
from ..utils import ik_model_receiver


def update_source_hashes(instance):
    """
    Stores hashes of the source image files so that they can be compared
    later to see whether the source image has changed (and therefore whether
    the spec file needs to be regenerated).

    """
    instance._ik._source_hashes = dict((f.attname, hash(f.source_file)) \
            for f in instance._ik.spec_files)
    return instance._ik._source_hashes


@ik_model_receiver
def post_save_receiver(sender, instance=None, created=False, raw=False, **kwargs):
    if not raw:
        old_hashes = instance._ik._source_hashes.copy()
        new_hashes = update_source_hashes(instance)
        for attname in instance._ik.spec_fields:
            if old_hashes[attname] != new_hashes[attname]:
                getattr(instance, attname).invalidate()


@ik_model_receiver
def post_delete_receiver(sender, instance=None, **kwargs):
    for spec_file in instance._ik.spec_files:
        spec_file.clear()


@ik_model_receiver
def post_init_receiver(sender, instance, **kwargs):
    update_source_hashes(instance)


def configure_receivers():
    # Connect the signals. We have to listen to every model (not just those
    # with IK fields) and filter in our receivers because of a Django issue with
    # abstract base models.
    # Related:
    #     https://github.com/jdriscoll/django-imagekit/issues/126
    #     https://code.djangoproject.com/ticket/9318
    uid = 'ik_spec_field_receivers'
    post_init.connect(post_init_receiver, dispatch_uid=uid)
    post_save.connect(post_save_receiver, dispatch_uid=uid)
    post_delete.connect(post_delete_receiver, dispatch_uid=uid)
