#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

import re

EmptyValue = [ [""],[''],[" "],[' ']]

def char_position(string):
    string = string[0] if isinstance(string, list) else string
    l = string[0].lower()
    return ord(l) - 97

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def ReprInt(s):
    if isinstance(s, str):
        try:
            int(s)
        except ValueError:
            return s
        return int(s)
    else:
        return s


def keys_exists(element, *keys):
    '''
    Check if *keys (nested) exists in `element` (dict).
    '''
    if type(element) is not dict:
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True

def IfExistsDic(dictionnary, *vals, **kargs):
    if "default" in kargs:
        default = kargs["default"]
    else:
        default = None

    if type(dictionnary) is not dict:
        return default

    if len(vals) == 0:
        return default

    _dictionnary = dictionnary
    r = ''
    for val in vals:
        try:
            r = _dictionnary
            _dictionnary = _dictionnary[val]
        except KeyError:
            return default

    if isinstance(_dictionnary, dict):
        # raise Exception('value is still a dictionnary or something')
        return _dictionnary
    else:
        if _dictionnary is not None:
            return _dictionnary
        else:
            return default

def IfExistsListFirst(val):
    res = False
    if isinstance(val,list):
        if len(val) >0:
            return val
        else:
            return None
    else:
        return None

def BoolInt(val):
    """"
        Returns the boolean value of integer value 0-1

        Used to construct HTML query args.

        :param val: the int to convert
        :type val: int

        :return: The boolean value
        :rtype: bool
    """
    if int(val) == "1" :
        return True
    elif int(val) == "0" :
        return False

def StrBool(val):
    """"
        Returns the string representation of a boolean value

        Used to construct HTML query args.

        :param val: the boolean to convert
        :type val: bool

        :return: The result of the addition
        :rtype: str
    """
    if val == True:
        return "true"
    if val == False:
        return "false"

def BoolStr(val):
    """"
        Returns the boolean value from a string representation

        Used to convert HTML query args.

        :param val: the string to convert
        :type val: str

        :return: The result of the addition
        :rtype: bool
    """
    if val in ['true','True','on']:
        return True
    elif val in ['false','False','off']:
        return False
    else:
        return None

def clean(s):
    if s == None:
        return ''
    if s == '':
        return ''
    if s == "":
        return ''
    if s == "'":
        return ''
    if s == '"':
        return ''
    s = s.rstrip()
    s = s.lstrip()
    s = s.replace("]-", "]")
    s = s.replace("]/", "]")
    s = s.replace("-[", "[")
    s = s.replace("/[", "[")
    s = s.rstrip()
    s = s.lstrip()
    try:
        if len(s)>=1:
            if s[0] in ['-','/','\\']:
                s = s[1:]
                clean(s)
            if s[len(s)-1] in ['-','/','\\']:
                s = s[:-1]
                clean(s)
    except:
        return ''
    s = "\n".join([s1 for s1 in s.split("\n") if len(s1) > 1])
    s = s.replace("  /  ", "")
    s = s.replace("  -  ", "")
    s = s.replace("''", "'")
    s = re.sub(r'(<br\s*/?>){2,}', '<br>', s, flags=re.IGNORECASE)
    s = re.sub(r'/+', '/', s)
    s = s.replace("/ / /", "/")
    s = re.sub(r'/\s+/', '/', s)
    # s = s.replace("//", "/")
    # s = s.replace("/ /", "/")
    # s = s.replace("/  /", "/")
    # s = s.replace("/   /", "/")
    return (s)

def to_int(value):
    '''
    retunrs the integer value or 0
    :param value:
    :return:
    '''
    try:
        value = int(value)
    except:
        value = 0
    return value

def to_unicode(value):
    '''

    :param value: anything
    :return: the unicode representation
    '''
    if type(value) is list:
        value = [to_unicode(i) for i in value]
    elif type(value) is int:
        value= str(value)
    elif type(value) is float:
        value= str(value).decode("utf-8")
    elif type(value) is str:
        try:
            value= str(value).decode("utf-8")
        except:
            pass

    return value


def list_to_single(value):
    if isinstance(value, list):
        if len(value) == 1:
            value = value[0]
        elif len(value) == 0:
            value = None
    elif isinstance(value, basestring):
        if value == '':
            value = None
        else:
            value =value
    return value


def join_str(delimiter, s1, s2):
    """
    join 2 values with a separator or return only one
    if both are no there

    :param delimiter: delimiter between the two strings
    :param s1: string1
    :param s2: string2
    :return: separator or only one of both if None
    """
    v = ''
    if s1 == 0 : s1 = None
    if s2 == 0: s2 = None
    s1 = to_unicode(s1)
    s2 = to_unicode(s2)
    delimiter = to_unicode(delimiter)
    if (s1 is not None) and (s2 is not None):
        v = s1 + ' ' + '/' + ' ' + s2
    elif (s1 is None) and (s2 is not None):
        v =  s2
    elif (s1 is not None) and (s2 is None):
        v = s1
    elif (s1 is None) and (s2 is None):
        v = ''
    return v

def display(value):
    if isinstance(to_unicode(value), list):
        return ', '.join((x) for x in value)
    else:
        return to_unicode(value)

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [ atoi(c) for c in re.split('(\d+)', text) ]

def naturalsort(liste):
    '''
    Sort a list in a a natural order
    :param liste: a list
    :return: the sorted list
    '''
    liste.sort(key=natural_keys)
    return liste

if __name__ == '__main__':
    print(IfExistsDic({'volume': 23},"volume"))
