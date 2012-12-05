from imagekit import ImageSpec, register


class TestSpec(ImageSpec):
    pass


register.spec('testspec', TestSpec)
