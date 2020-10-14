from import_export.admin import ImportExportModelAdmin
from django.utils.html import format_html
from django.contrib import admin
from .models import Category,Product

class CategoryAdmin(admin.ModelAdmin):
	list_display = ['name','slug']
	prepopulated_fields = {'slug':('name',)}
admin.site.register(Category,CategoryAdmin)

@admin.register(Product)

class ProductAdmin(admin.ModelAdmin):
   list_display = ['thumbnail','image','name','price','stock','available','created','updated']
   list_editable = ['price','stock','available']
   prepopulated_fields = {'slug':('name',)}
   list_per_page = 20
   def thumbnail(self, obj):
       return format_html('<img src="{}" style="width: 80px; height: 80px;"/>'.format(obj.image.url))
   thumbnail.description = 'thumbnail'
#admin.site.register(Product,ProductAdmin)

#class ProductAdmin(admin.ModelAdmin):
#	list_display = ['name','price','stock','available','created','updated']
#	list_editable = ['price','stock','available']
#	prepopulated_fields = {'slug':('name',)}
#	list_per_page = 20
#admin.site.register(Product,ProductAdmin)