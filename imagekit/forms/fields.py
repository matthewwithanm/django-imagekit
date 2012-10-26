from django.forms import ImageField
from ..specs import SpecHost


class ProcessedImageField(ImageField, SpecHost):

    def __init__(self, processors=None, format=None, options=None,
                 autoconvert=True, spec=None, spec_id=None, *args, **kwargs):

        if spec_id is None:
            spec_id = '??????'  # FIXME: Wher should we get this?

        SpecHost.__init__(self, processors=processors, format=format,
                          options=options, autoconvert=autoconvert, spec=spec,
                          spec_id=spec_id)
        super(ProcessedImageField, self).__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        data = super(ProcessedImageField, self).clean(data, initial)

        if data:
            spec = self.get_spec()  # HINTS?!?!?!?!?!
            data = spec.apply(data, data.name)

        return data
