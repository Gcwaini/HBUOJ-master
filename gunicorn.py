import multiprocessing

bind = ['127.0.0.1:8080']
# pidfile = '/tmp/hbuoj/site.pid'
workers = multiprocessing.cpu_count() * 2 + 1
error_log = '-'
worker_class = 'gunicorn.workers.ggevent.GeventWorker'

# Debug
reload = True
reload_extra_files = ['templates', ]
check_config = True
statsd_host = '127.0.0.1:8081'
