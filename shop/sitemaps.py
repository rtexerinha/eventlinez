from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from event.models import Event


class EventSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'

    def items(self):
        return Event.objects.filter(available=True).select_related('category')

    def lastmod(self, obj):
        return obj.updated

    def location(self, obj):
        return obj.get_url()


class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5
    protocol = 'https'

    def items(self):
        return ['index', 'about', 'contact', 'shop:gallery_home']

    def location(self, item):
        return reverse(item)


class HomeSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0
    protocol = 'https'

    def items(self):
        return ['index']

    def location(self, item):
        return reverse(item)
