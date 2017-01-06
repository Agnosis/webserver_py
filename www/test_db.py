#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'K.Lee'

from models import User, Blog, Comment

from transwarp import db

db.create_engine(user = 'klee',password = 'klee', database = 'kblog')

testUser= User(name = 'Test',email ='test@example.com',password='888888',image = 'about:blank')

testUser.insert()

print 'new user id:', testUser.id

user = User.find_first('where email=?','test@example.com')

print 'find user\'s name' ,user.name

user.delete()

user2 = User.find_first('where email=?','test@example.com')

print 'find user:', user2