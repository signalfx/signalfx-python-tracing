# Copyright (C) 2018-2019 SignalFx, Inc. All rights reserved.

instrumented_attr = '__sfx_instrumented'
traceable_libraries = ('django', 'elasticsearch', 'flask', 'psycopg2', 'pymongo', 'pymysql', 'redis', 'requests',
                       'tornado')
auto_instrumentable_libraries = ('elasticsearch', 'flask', 'psycopg2', 'pymongo', 'pymysql', 'redis', 'requests',
                                 'tornado')
