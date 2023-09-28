from django.forms import ImageField

from ..specs import SpecHost
from ..utils import generate


class ProcessedImageField(ImageField, SpecHost):

    def __init__(self, processors=None, format=None, options=None,
                 autoconvert=True, spec_id=None, spec=None, *args, **kwargs):

        if spec_id is None:
            # Unlike model fields, form fields are never told their field name.
            # (Model fields are done so via `contribute_to_class()`.) Therefore
            # we can't really generate a good spec id automatically.
            raise TypeError('You must provide a spec_id')

        SpecHost.__init__(self, processors=processors, format=format,
                          options=options, autoconvert=autoconvert, spec=spec,
                          spec_id=spec_id)
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        data = super().clean(data, initial)

        if data and data != initial:
            spec = self.get_spec(source=data)
            f = generate(spec)
            # Name is required in Django 1.4. When we drop support for it
            # then we can directly return the result from `generate(spec)`
            f.name = data.name
            return f

        return data
