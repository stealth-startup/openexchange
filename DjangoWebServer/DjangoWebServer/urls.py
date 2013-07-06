from django.conf.urls import patterns, include, url
import server.urls as server_urls

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'DjangoWebServer.views.home', name='home'),
    # url(r'^DjangoWebServer/', include('DjangoWebServer.foo.urls')),

    url(r'', include(server_urls)),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
