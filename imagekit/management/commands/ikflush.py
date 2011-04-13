import sys, os
from pprint import pprint
from django.db.models import Q
from django.db.models.loading import cache
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from optparse import make_option
from imagekit.models import ImageModel
from imagekit.specs import ImageSpec


class Command(BaseCommand):
	
	option_list = BaseCommand.option_list + (
		make_option('--ids', '-i', dest='ids',
			help="Optional range of IDs like low:high",
		),
	)
	
	help = ('Clears all ImageKit cached image files.')
	args = '[apps]'
	requires_model_validation = True
	can_import_settings = True

	def handle(self, *args, **options):
		return flush_image_cache(args, options)

def flush_image_cache(apps, options):
	"""
	Clears the image cache
	
	"""
	
	apps = [a.strip(',') for a in apps]
	
	if apps:
		for app_label in apps:
			
			app_parts = app_label.split('.')
			models = list()
			
			
			try:
				app = cache.get_app(app_parts[0])
			except ImproperlyConfigured:
				print "WTF: no app with label %s found" % app_parts[0]
			else:
			
				if not len(app_parts) == 2:
					models = [m for m in cache.get_models(app) if issubclass(m, ImageModel)]
				else:
					putativemodel = cache.get_model(app_parts[0], app_parts[1])
					if issubclass(putativemodel, ImageModel):
						models.append(putativemodel)
				
				for model in models:
					
					if not options.get('ids'):
						objs = model.objects.all()
					else:
						if options.get('ids').find(':') == -1:
						
							objs = model.objects.filter(
								Q(id__gte=0) & Q(id__lte=int(options.get('ids')))
							)
						
						else:
							
							bottom, top = options.get('ids').split(':')
							if not bottom:
								bottom = '0'
							if not top:
								objs = model.objects.filter(
									Q(id__gte=int(bottom))
								)
							else:
								objs = model.objects.filter(
									Q(id__gte=int(bottom)) & Q(id__lte=int(top))
								)
					
					print 'Flushing image file cache for %s objects in "%s.%s"' % (objs.count(), app_parts[0], model.__name__)
					for obj in objs.order_by('modifydate'):
						
						if int(options.get('verbosity', 1)) > 1:
							if obj._imgfield.name:
								print ">>>\t %s" % obj._imgfield.name or "(NO NAME)"
							else:
								print "---\t (None)"
						
						obj._clear_cache()
						obj._pre_cache()
	else:
		print 'Please specify on or more app names'
