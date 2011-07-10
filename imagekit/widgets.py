
from django import forms
from django.utils.safestring import mark_safe
from imagekit.utils import static

class RGBColorFieldWidget(forms.TextInput):
    """
    RGBColorFieldWidget -- edit a hex color.
    
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
        out = super(RGBColorFieldWidget, self).render(name, value, attrs)
        
        out += mark_safe("""
            <div id="swatch_%s" class="colorswatch"></div>
        """ % name)
        
        out += mark_safe(u"""
            
            <script type="text/javascript">
                $(document).ready(function () {
                    var elem = $('#id_%s');
                    var pickers = $('.colorfield');
                    var valid = "0123456789ABCDEF"
                    elem.ColorPicker({
                        livePreview: true,
                        onChange:function(hsb, hex, rgb, el) {
                            if (typeof(hex) !== "undefined") {
                                $('#swatch_%s').css('backgroundColor', '#' + hex);
                                $(el).val(hex.toUpperCase());
                            }
                        },
                        onSubmit:function(hsb, hex, rgb, el) {
                            $(el).val(hex.toUpperCase());
                            $('#swatch_%s').css('backgroundColor', '#' + hex);
                            $(el).ColorPickerHide();
                        },
                        onBeforeShow:function(hsb, hex, rgb, el) {
                            $(this).ColorPickerSetColor('#' + elem.val());
                            $('#swatch_%s').css('backgroundColor', '#' + elem.val());
                        },
                        onHide:function(hsb, hex, rgb, el) {
                            if (typeof(hex) !== "undefined") {
                                elem.val(hex.toUpperCase());
                                $('#swatch_%s').css('backgroundColor', '#' + hex);
                            }
                        }
                    }).bind('keypress', function(e) {
                        if (!e.ctrlKey && !e.altKey && !e.metaKey) {
                            e.preventDefault();
                        }
                        var pressed = String.fromCharCode(e.which).toUpperCase();
                        if (valid.indexOf(pressed) != -1) {
                            var currentval = elem.val();
                            if (currentval.length < 6) {
                                var newval = currentval + pressed;
                                elem.val(newval);
                            }
                        }
                    }).bind('focus', function() {
                        pickers.not("#id_%s").ColorPickerHide();
                        $(this).ColorPickerShow();
                    }).bind('blur', function () {
                        var newval = elem.val();
                        if (newval.length < 6) {
                            if (newval.length == 0) {
                                elem.val('');
                                $(this).ColorPickerSetColor('#FF0000');
                                $('#swatch_%s').css('backgroundColor', '#FFFFFF');
                            } else if (newval.length != 3) {
                                var padme = newval;
                                for (var idx = newval.length; idx < 6; idx++) {
                                    padme += "0";
                                }
                                elem.val(padme);
                                $(this).ColorPickerSetColor('#' + padme);
                                $('#swatch_%s').css('backgroundColor', '#' + padme);
                            } else {
                                var triple = newval;
                                var sextuple = '';
                                for (var idx = 0; idx < 6; idx++) {
                                    sextuple += triple.charAt(idx);
                                    sextuple += triple.charAt(idx);
                                }
                                elem.val(sextuple);
                                $(this).ColorPickerSetColor('#' + sextuple);
                                $('#swatch_%s').css('backgroundColor', '#' + sextuple);
                            }
                        }
                    });
                });
            </script>
            
        """ % (name, name, name, name, name, name, name, name, name))
        
        return out
