from django.conf.urls import patterns, handler403, handler404, handler500, url
from server.views import \
    home, market, help, account, asset, \
    auth, recent_trades, asset_order_book, chart_data, asset_page_login, \
    page_not_found_404, server_error_500, forbidden_403

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

handler404 = page_not_found_404
handler500 = server_error_500
handler403 = forbidden_403

urlpatterns = patterns('',
       url(r'^$', home, name='home'),
       url(r'^market$', market, name='market'),
       url(r'^help$', help, name='help'),
       url(r'^account/(?P<asset_name>[A-Z]+)/(?P<user_address>[A-Za-z0-9]+)$', account, name='account'),
       (r'^asset/(?P<asset_name>[A-Z]+)$', asset),
       #############################################################   apis
       #change from_time pattern to only use digits
       (r'^chart-data/(?P<asset_name>[A-Z]+)$', chart_data),
       (r'^orderbook/(?P<asset_name>[A-Z]+)$', asset_order_book),
       (r'^asset-page-login/(?P<asset_name>[A-Z]+)/(?P<user_address>[A-Za-z0-9]+)$', asset_page_login),
       (r'^user/auth$', auth),
       (r'^asset/(?P<asset_name>[A-Z]+)/recent-trades$', recent_trades),
       ##################### for local testing, delete or comment out these handlers in production
        (r'^403$', handler403),
        (r'^404$', handler404),
        (r'^500$', handler500),
       ############################################################# DO NOT DELETE
       (r'^.*$', handler404)
)
