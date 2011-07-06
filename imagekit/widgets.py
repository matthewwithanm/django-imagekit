
from django import forms
from imagekit.utils import static

class RGBColorFieldWidget(forms.TextInput):
    """
    ColorFieldWidget -- edit a hex color.
    
    The colorpicker is (minimally) adapted from here: from http://www.eyecon.ro/colorpicker/.
    
    """
    
    class Media:
        css = {'all': (
            static('css/colorpicker-admin.css'),
        )}
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js',
            'https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.13/jquery-ui.min.js',
            static('js/colorpicker-admin.js'),
        )
    
    def __init__(self, language=None, attrs={}):
        super(RGBColorFieldWidget, self).__init__(attrs=attrs)
    
    def render(self, name, value, attrs={}):
        out = super(ColorFieldWidget, self).render(name, value, attrs)
        
        out += mark_safe("""
            <div id="swatch_%s" class="colorswatch"></div>
        """ % name)
        
        out += mark_safe(u"""
            
            <script type="text/javascript">
                $('#id_%s').ColorPicker({
                    livePreview: true,
                    onChange:function(hsb, hex, rgb, el) {
                        $('#swatch_%s').css('backgroundColor', '#' + hex);
                    },
                    onSubmit:function(hsb, hex, rgb, el) {
                        $(el).val(hex.toUpperCase());
                        $(el).ColorPickerHide();
                    },
                    onBeforeShow:function() {
                        $(this).ColorPickerSetColor(this.value);
                    }
                }).bind('keyup', function() {
                    $(this).ColorPickerSetColor(this.value);
                });
            </script>
            
        """ % (name, name))
        
        return out
