import multiprocessing

bind = ['127.0.0.1:8080']

pidfile = '/tmp/hbuoj/site.pid'

workers = multiprocessing.cpu_count() * 2 + 1
reload = True
reload_extra_files = ['templates', ]
check_config = False
statsd_host = '127.0.0.1:8081'

error_log = '-'

raw_env = ['DJANGO_SETTINGS_MODULE=dmoj.settings', ]