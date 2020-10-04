# Copyright (C) 2018-2019 SignalFx. All rights reserved.

instrumented_attr = '__sfx_instrumented'
traceable_libraries = (
    'celery', 'django', 'elasticsearch', 'falcon', 'flask', 'psycopg2', 'pymongo', 'pymysql', 'redis', 'requests',
    'tornado', 'logging'
)

auto_instrumentable_libraries = (
    'celery', 'elasticsearch', 'falcon', 'flask', 'psycopg2', 'pymongo', 'pymysql', 'redis', 'requests',
    'tornado', 'logging'
)

default_max_tag_value_length = 1200

logging_format = (
    '%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
    '[signalfx.trace_id=%(sfxTraceId)s signalfx.span_id=%(sfxSpanId)s] '
    '- %(message)s'
)
