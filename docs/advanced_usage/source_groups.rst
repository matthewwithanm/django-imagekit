.. _source-groups:

ImageKit allows you to register objects—called *source groups*—which do two
things: 1) dispatch signals when a source is created, changed, or deleted, and
2) expose a generator method that enumerates source files. When these objects
are registered (using ``imagekit.register.source_group()``), their signals will
trigger callbacks on the generated file strategies associated with image specs
that use the source. In addition, the generator method is used (indirectly) to
create the list of files to generate with the ``generateimages`` management
command.

Currently, there is only one source group class bundled with ImageKit,
``imagekit.specs.sourcegroups.ImageFieldSourceGroup``, which represents an
ImageField on every instance of a particular model. In terms of the above
description, ``ImageFieldSourceGroup(Profile, 'avatar')`` 1) dispatches a signal
every time the image in Profile's avatar ImageField changes, and 2) exposes a
generator method that iterates over every Profile's "avatar" image.

ImageKit automatically creates and registers an instance of
ImageFieldSourceGroup every time you create an ImageSpecField; that's how the
field is connected (internally) to the spec you're defining, and therefore to
the generated file strategy responsible for generating the file. It's also how
the ``generateimages`` management command is able to know which sources to
generate files for.
