import os, urlparse, numpy
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.signals import post_delete
from django.utils.html import conditional_escape as escape
from django.utils.translation import ugettext_lazy as _
from colorsys import rgb_to_hls, hls_to_rgb

from imagekit import specs
from imagekit.lib import *
from imagekit.options import Options
from imagekit.utils import img_to_fobj, md5_for_file

# Modify image file buffer size.
ImageFile.MAXBLOCK = getattr(settings, 'PIL_IMAGEFILE_MAXBLOCK', 256 * 2 ** 10)

# Choice tuples for specifying the crop origin.
# These are provided for convenience.
CROP_HORZ_CHOICES = (
    (0, _('left')),
    (1, _('center')),
    (2, _('right')),
)

CROP_VERT_CHOICES = (
    (0, _('top')),
    (1, _('center')),
    (2, _('bottom')),
)


class ImageModelBase(ModelBase):
    """
    ImageModel metaclass
    
    This metaclass parses IKOptions and loads the specified specification
    module.
    """
    def __init__(cls, name, bases, attrs):
        
        parents = [b for b in bases if isinstance(b, ImageModelBase)]
        if not parents:
            return
        
        user_opts = getattr(cls, 'IKOptions', None)
        opts = Options(user_opts)
        
        try:
            module = __import__(opts.spec_module,  {}, {}, [''])
        except ImportError:
            raise ImportError('Unable to load imagekit config module: %s' % opts.spec_module)
        for spec in [spec for spec in module.__dict__.values()]:
            if isinstance(spec, type):
                if issubclass(spec, specs.ImageSpec):
                    if spec != specs.ImageSpec:
                        setattr(cls, spec.name(), specs.Descriptor(spec))
                        opts.specs.append(spec)
        
        setattr(cls, '_ik', opts)


class ImageModel(models.Model):
    """
    Abstract base class implementing all core ImageKit functionality
    
    Subclasses of ImageModel are augmented with accessors for each defined
    image specification and can override the inner IKOptions class to customize
    storage locations and other options.
    """
    __metaclass__ = ImageModelBase
    
    class Meta:
        abstract = True
    
    class IKOptions:
        pass
    
    def admin_thumbnail_view(self):
        if not self._imgfield:
            return None
        prop = getattr(self, self._ik.admin_thumbnail_spec, None)
        if prop is None:
            return 'An "%s" image spec has not been defined.' % \
              self._ik.admin_thumbnail_spec
        else:
            if hasattr(self, 'get_absolute_url'):
                return u'<a href="%s"><img src="%s"></a>' % \
                    (escape(self.get_absolute_url()), escape(prop.url))
            else:
                return u'<a href="%s"><img src="%s"></a>' % \
                    (escape(self._imgfield.url), escape(prop.url))
    admin_thumbnail_view.short_description = _('Thumbnail')
    admin_thumbnail_view.allow_tags = True
    
    @property
    def _imgfield(self):
        return getattr(self, self._ik.image_field)
    
    @property
    def _storage(self):
        return getattr(self._ik, 'storage', self._imgfield.storage)
    
    def _clear_cache(self):
        for spec in self._ik.specs:
            prop = getattr(self, spec.name())
            prop._delete()
    
    def _pre_cache(self):
        for spec in self._ik.specs:
            if spec.pre_cache:
                prop = getattr(self, spec.name())
                prop._create()
    
    @property
    def pilimage(self):
        try:
            if self.image.file.name:
                filename = self.image.file.name
        except ValueError:
            return None
        else:
            return Image.open(filename)
    
    def _get_histogram(self):
        out = []
        if self.pilimage:
            tensor = numpy.array(self.pilimage.convert('L').histogram())
            histo,buckets = numpy.histogram(tensor, bins=255)
            return zip(xrange(len(histo)), histo.flatten().astype(int).tolist())
    histogram = property(_get_histogram)
    
    def _get_rgb_histogram(self):
        return ('r','g','b') # TOOOO DOOOO
    
    def dominantcolor(self):
        return self.pilimage.quantize(1).convert('RGB').getpixel((0, 0))
    def meancolor(self):
        return ImageStat.Stat(self.pilimage).mean
    def averagecolor(self):
        return self.pilimage.resize((1, 1), Image.ANTIALIAS).getpixel((0, 0))
    
    def mediancolor(self):
        return reduce((lambda x,y: x[0] > y[0] and x or y), self.pilimage.getcolors(self.pilimage.size[0] * self.pilimage.size[1]))
    
    def topcolors(self, numcolors=3):
        if self.pilimage:
            colors = self.pilimage.getcolors(self.pilimage.size[0] * self.pilimage.size[1])
            fmax = lambda x,y: x[0] > y[0] and x or y
            out = []
            out.append(reduce(fmax, colors))
            for i in range(1, numcolors):
                out.append(reduce(fmax, filter(lambda x: x not in out, colors)))
            return out
        return []
    
    def topsat(self, samplesize=10):
        try:
            return "#" + "".join(map(lambda x: "%02X" % int(x*255),
                map(lambda x: hls_to_rgb(x[0], x[1], x[2]), [
                    reduce(lambda x,y: x[2] > y[2] and x or y,
                        map(lambda x: rgb_to_hls(float(x[1][0])/255, float(x[1][1])/255, float(x[1][2])/255), self.topcolors(samplesize)))
                ])[0]
            ))
        except TypeError:
            return ""
    
    def dominanthex(self):
        return "#%02X%02X%02X" % self.dominantcolor()
    def meanhex(self):
        m = self.meancolor()
        return "#%02X%02X%02X" % (int(m[0]), int(m[1]), int(m[2]))
    def averagehex(self):
        return "#%02X%02X%02X" % self.averagecolor()
    def medianhex(self):
        return "#%02X%02X%02X" % self.mediancolor()[1]
    def tophex(self, numcolors=3):
        return [("#%02X%02X%02X" % tc[1]) for tc in self.topcolors(numcolors)]
    
    def save_image(self, name, image, save=True, replace=True):
        if self._imgfield and replace:
            self._imgfield.delete(save=False)
        if hasattr(image, 'read'):
            data = image.read()
        else:
            data = image
        content = ContentFile(data)
        self._imgfield.save(name, content, save)
    
    def save(self, clear_cache=True, *args, **kwargs):
        is_new_object = self._get_pk_val() is None
        super(ImageModel, self).save(*args, **kwargs)
        if is_new_object and self._imgfield:
            clear_cache = False
            spec = self._ik.preprocessor_spec
            if spec is not None:
                newfile = self._imgfield.storage.open(str(self._imgfield))
                img = Image.open(newfile)
                img, format = spec.process(img, self)
                if format != 'JPEG':
                    imgfile = img_to_fobj(img, format)
                else:
                    imgfile = img_to_fobj(img, format,
                                          quality=int(spec.quality),
                                          optimize=True)
                content = ContentFile(imgfile.read())
                newfile.close()
                name = str(self._imgfield)
                self._imgfield.storage.delete(name)
                self._imgfield.storage.save(name, content)
        
        if self._imgfield:
            if clear_cache:
                self._clear_cache()
            self._pre_cache()
    
    def clear_cache(self, **kwargs):
        assert self._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (self._meta.object_name, self._meta.pk.attname)
        self._clear_cache()


post_delete.connect(ImageModel.clear_cache, sender=ImageModel)


class ICCImageModel(ImageModel):
    """
    This subclass is a horrible mess. Frankly all this logic should move to
    an ImageModelBase subclass so ICCImageModel can be a stubby little nothing.
    I have no idea why I thought all these underscored and poorly-named methods
    would be cool. Yeah. I'll change it toot sweet.
    """
    __metaclass__ = ImageModelBase

    class Meta:
        abstract = True
    
    class IKOptions:
        pass
    
    def _pre_cache(self):
        super(ICCImageModel, self)._pre_cache()
        self._save_iccprofile()
    def _clear_cache(self):
        super(ICCImageModel, self)._clear_cache()
        self._clear_iccprofile()
    
    @property
    def _iccdir(self):
        return getattr(self._ik, 'icc_dir')
    
    @property
    def _iccfilename(self):
        return "%s.icc" % os.path.basename(self._imgfield.name)
    
    @property
    def _iccurl(self):
        return urlparse.urljoin(self._storage.base_url, os.path.join(self._iccdir, self._iccfilename))
    
    def _get_iccfilepath(self):
        """
        FIXME: this will blindly overwrite anything
        """
        if not self._iccdir:
            return ""
        if not self._imgfield:
            return ""
        return os.path.join(self._storage.location, self._iccdir, self._iccfilename)
    
    def _get_iccstr(self):
        if not self.pilimage:
            return None
        return self.pilimage.info.get('icc_profile', None)
    
    def _get_icc(self):
        iccstr = self._get_iccstr()
        if not iccstr:
            return None
        return ImageCms.ImageCmsProfile(ImageCms.core.profile_fromstring(iccstr))
    
    def _save_iccprofile(self, svpth=None):
        savepath = svpth and svpth or self._get_iccfilepath()
        if not savepath:
            return None
        if os.path.exists(savepath): # FIXME: will need to do some FileSystemStorage nonsense and not fail quietly
            return None
        iccstrout = self._get_iccstr()
        if not iccstrout:
            return None
        iccfile = self._storage.open(savepath, mode="wb")
        iccfile.write(iccstrout)
        iccfile.flush()
        iccfile.close()
        return iccfile.name
    
    @property
    def _iccpath(self):
        return os.path.exists(self._get_iccfilepath()) and self._get_iccfilepath() or ""
    
    def _clear_iccprofile(self):
        if self._iccpath:
            self._storage.delete(self._iccpath)
    
    # icc profile properties
    @property
    def _icc_filehash(self):
        if self._iccpath:
            iccfile = self._storage.open(self._iccpath, mode="rb")
            out = md5_for_file(iccfile)
            iccfile.close()
            return out
        return None
    @property
    def _icc_productname(self):
        return self._get_icc().product_name
    @property
    def _icc_profilename(self):
        return self._get_icc().product_info.split('\r\n\r\n')[0]
    @property
    def _icc_copyright(self):
        return self._get_icc().product_info.split('\r\n\r\n')[1]
    @property
    def _icc_whitepoint(self):
        try:
            return self._get_icc().product_info.split('\r\n\r\n')[2].split(' : ')[1]
        except IndexError:
            try:
                return self._get_icc().product_info.split('\r\n\r\n')[2]
            except IndexError:
                return "n/a"



