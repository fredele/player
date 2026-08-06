from utils.string import to_unicode, clean
import json
import urllib.parse

def gettags(s):
    ids = []
    tags = []
    n= -1
    t = s[:]
    while(t.find('$') != -1):
        i = t.find('$')
        n+= i +1
        ids.append(n)
        t = t[i+1:len(s)]
    n=0
    for i in range(int(len(ids)/2)):
        tags.append(s[ids[n]+1:ids[n+1]])
        n+=2
    #tags = [item for sublist in [el.split(';') for el in tags] for item in sublist]
    return(tags)

def replacetags(display_str, tagsval_dic, separator):
    """
    :param display_str:
    :param tagsval_dic:
    :return:
    """

    tags = gettags(display_str)
    s = display_str[:]

    #Computed tags first
    dn = tagsval_dic.get('discnumber', '')[0]  if  isinstance(tagsval_dic.get('discnumber', ''), list)  else tagsval_dic.get('discnumber', '')
    tn = tagsval_dic.get('tracknumber', '')[0] if  isinstance(tagsval_dic.get('tracknumber', ''), list) else tagsval_dic.get('tracknumber', '')

    td = disc_track_str('/', dn, tn )

    s = s.replace('$trackdiscnumber$', td)


    repl = False
    for tag in tags:
        invert = False
        tt = tag.split(';')
        val = ""
        if len(tt) == 1:
            # No fallback tag
            t = tagsval_dic.get(tag, '')
            if t != '':
                if isinstance(t, list):
                    if separator == "json":
                        st =""
                        for v in sorted(t):
                            oc = ""
                            if tag == "album":
                                oc = f'onclick="browse_to({tagsval_dic.get("dirhash", "")})"'
                            st+=f'<span class="{tag}" {oc}>{v}</span>, '

                        s = s.replace('$'+tag+'$', st[:-2])
                    else:
                        val = separator.join(sorted(t))
                    val = to_unicode(val)
                else:
                    if separator == "json":
                        oc =""
                        if tag == "album":
                            oc = f'onclick="browse_to({tagsval_dic.get("dirhash", "")})"'
                        st = f'<span  class="{tag}" {oc}>{t}</span>'
                        s = s.replace('$'+tag+'$', st)
                    else:
                        val = to_unicode(t)


                val = str(val)
                #val = val.replace("'",'"') # ??
                s = s.replace('$' + str(tag) + '$', val)
            else:
                s = s.replace('$' + str(tag) + '$', '')

        else:
            #fallback tag
            for ti in tt:
                if repl == False:
                    t = tagsval_dic.get(ti, '')
                    if t != '':
                        if isinstance(t, list):
                            if t != []:
                                val = ', '.join(sorted(t))
                                val = to_unicode(val)
                                s = s.replace(ti + '$', val)
                                s = s.replace('$' + ti, val)
                                s = s.replace(ti, '')
                                repl = True
                            else:
                                s = s.replace('$' + ti + ';', '')
                                s = s.replace(';' + ti + '$', '')
                                s = s.replace(ti, '')
                                repl = False
                        else:
                            val = to_unicode(t)
                            # replace first found tag with the value
                            s = s.replace('$'+tag+'$', val)

                else:
                    break
            # if not found ...
            for ti in tt:
                s = s.replace('$' + ti + ';', '')
                s = s.replace(';' + ti + '$', '')

            s = s.replace('$' + tag + '$', '')
    #print(s)
    #print(clean(s))
    return(clean(s))




def disc_track_str(delimiter,d,t):
    d = to_unicode(d)
    t = to_unicode(t)
    delimiter =  to_unicode(delimiter)
    if d == 0 : d = None
    if t == 0: t = None
    if d == '' : d = None
    if t == '': t = None
    if d == '0' : d = None
    if t == '0': t = None
    if (d is not None) and (t is not None):
        return d + ' '+ delimiter + ' '+ t
    if (d is None) and (t is not None):
        return  t
    if (d is not None) and (t is None):
        return d
    if (d is None) and (t is None):
        return ''
