def MsToMMSS(value):
    q, s = divmod(value/1000, 60)
    h, m = divmod(q, 60)
    if h ==0 :
        return "%02d:%02d" % ( m, s)
    else :
        return "%02d:%02d:%02d" % (h, m, s)


def HHMMSSToMs(value):
    value = value.replace(".000","")
    if value.count(':') ==1 :
        try:
            m, s = value.split(':')
            return   (int(m) * 60 + int(s))*1000
        except:
            return 0

    if value.count(':') == 2:
        try:
            h, m, s = value.split(':')
            return   (int(h)*60*60 + int(m) * 60 + int(s))*1000
        except:
            return 0