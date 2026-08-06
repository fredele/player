#!/usr/bin/python3
#-*- coding: utf-8 -*-

import datetime
import arrow
import os
import os.path

def convert(input):
    for k,v in enumerate(input):
        for i in v:
            i = i.encode('utf-8')
    return input

def DateToExcel(strdate, dateformat):
    date = datetime.datetime.strptime(strdate, dateformat)
    temp = datetime.datetime(1899, 12, 30)
    r = date-temp
    return str(r.days)

def ExcelToDate(xldate, dateformat):
    temp = datetime.datetime(1899, 12, 30)
    delta = datetime.timedelta(days=int(xldate))
    date = temp+delta
    return str(date.strftime(dateformat))

def Excel_Now():
    now = datetime.datetime.now()
    date = int(DateToExcel(str(now.day) + '/' + str(now.month) + '/'+ str(now.year) , "%d/%m/%Y"))
    return date

def Timestamp_modified(f):
    return int(arrow.get(os.path.getmtime(f)).to('local').timestamp())

def Timestamp_Now():
    a = arrow.utcnow()
    a= a.to('local').timestamp()
    return int(a) # UNIX epoch time



