#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
__author__ = 'K.Lee'

import time, uuid, functools, threading, logging

class Dict(dict):
	"""docstring for Dict"""
	def __init__(self, names =(),values =(), **kw):
		super(Dict, self).__init__(**kw)
		for k,v in zip(names,values):
			self[k] = v

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Dict' object has no attribute" % key)

def next_id(t = None):
 	if t is None:
 	 	t = time.time() 
	return '%015d%s000' % (int(t * 1000), uuid.uuid4().hex)


def _profiling(start, sql =''):
	t = time.time() - start
	if t>0.1:
		logging.warning('[PROFILING] [DB] %s: %s' % (t,sql))
	else:
		logging.info('[PROFILING] [DB] %s: %s' % (t,sql))


class DBError(Exception):
	"""docstring for DBError"""
	pass

class MultiColumnsError(DBError):
    pass

class _LasyConnection(object):

    def __init__(self):
        self.connection = None

    def cursor(self):
        if self.connection is None:
            connection = engine.connect()
            logging.info('open connection <%s>...' % hex(id(connection)))
            self.connection = connection
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def cleanup(self):
        if self.connection:
            connection = self.connection
            self.connection = None
            logging.info('close connection <%s>...' % hex(id(connection)))
            connection.close()
		
# 持有数据库连接的上下文对象

class _DbCtx(threading.local):
	"""docstring for _DbCtx"""
	def __init__(self):
		self.connection = None
		self.transactions = 0

	def is_init(self):
		return not self.connection is None

	def init(self):
		self.connection = _LasyConnection()
		self.transactions = 0

	def cleanup(self):
		self.connection.cleanup()
		self.connection = None

	def cursor(self):
		return self.connection.cursor()

_db_ctx = _DbCtx()

# 数据库引擎对象
class _Engine(object):
	"""docstring for _Engine"""
	def __init__(self, connect):
		self._connect = connect
	def connect(self):
		return self._connect()

#全局数据库引擎对象
engine = None

def create_engine(user, password, database, host = '127.0.0.1', port = 3306, **kw):
	import mysql.connector
	global engine
	if engine is not None:
		raise DBError('Engine is already initialized.')
	params = dict(user = user, password = password, database = database, host = host, port = port)
	defaults = dict(use_unicode =True, charset='utf8',collation = 'utf8_general_ci',autocommit = False)

	for k,v in defaults.iteritems():
		params[k] = kw.pop(k,v)
	params.update(kw)
	params['buffered'] = True
	engine = _Engine(lambda: mysql.connector.connect(**params))
	# Testing
	logging.info('Init mysql engine<%s> ok.' % hex(id(engine)))


class _ConnectionCtx(object):
	"""docstring for _ConnectionCtx"""
	def __enter__(self):
		global _db_ctx
		self.should_cleanup = False
		if not _db_ctx.is_init():
			_db_ctx.init()
			self.should_cleanup = True
		return self

	def __exit__(self,exctype,excvalue,traceback):
		global _db_ctx
		if self.should_cleanup:
			_db_ctx.cleanup()

def connection():
	return _ConnectionCtx()

def with_connection(func):
	@functools.wraps(func)
	def _wrapper(*args, **kw):
		with _ConnectionCtx():
			return func(*args,**kw)
	return _wrapper

class _TransactionCtx(object):
	"""docstring for _TransactionCtx"""
	def __enter__(self):
		global _db_ctx
		self.should_close_conn = False
		if not _db_ctx.is_init():
			_db_ctx.is_init()
			self.should_close_conn = True
			_db_ctx.transactions = _db_ctx.transactions + 1
			return self

	def __exit__(self,exctype,excvalue,traceback):
		global _db_ctx
		_db_ctx.transactions = _db_ctx.transactions - 1
		try:
			if _db_ctx.transactions == 0:
				if exctype is None:
					self.commit()
				else:
					self.rollback()
				
		finally:
			if self.should_close_conn:
				_db_ctx.cleanup()

		
	def commit(self):
		global _db_ctx
		try:
			_db_ctx.connection.commit()
		except:
			_db_ctx.connection.rollback() 
			raise 

	def rollback(self):
		global _db_ctx
		_db_ctx.connection.rollback()
		
def transaction():
	return _TransactionCtx()

def with_transation(func):
	@functools.wraps(func)
	def _wrapper(*args,**kw):
		_start = time.time()
		with _TransactionCtx():
			return func(*args,**kw)
		_profiling(_start)
	return _wrapper

if __name__ == '__main__':
	logging.basicConfig(level = logging.DEBUG)
	create_engine('root','kaixinjiuhao','test')





























