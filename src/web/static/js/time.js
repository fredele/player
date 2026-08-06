/*

def HHMMSSToMs(value):
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

def MsToMMSS(value):
q, s = divmod(value/1000, 60)
h, m = divmod(q, 60)
if h ==0 :
    return "%02d:%02d" % ( m, s)
else :
    return "%02d:%02d:%02d" % (h, m, s)
*/


function HHMMSSToMs(value)
    {
    try {
            if(value.split(":").length - 1 == 1 ) 
            {
                var st = value.split(':')
                return   (parseInt(st[0]) * 60 + parseInt(st[1]))*1000
            }
        }
        catch (error) {return 0;}

    try {
            if(value.split(":").length - 1 == 2 ) 
            {
            var st = value.split(':')
            s=(parseInt(st[0])*60*60 + parseInt(st[1]) * 60 + parseInt(st[2]))*1000
            return s

            }
        }
        catch (error) {return 0;}       
    }

function MsToMMSS(value)
    {

        function pad(num) {
            num = num.toString();
            while (num.length < 2) num = "0" + num;
            return num;
        }
        
        function divmod(a,b)
        {
        var quotient = Math.floor(a/b);
        var remainder = a % b;
        return {q:quotient,r:remainder}
        }
        
        var q = divmod(value/1000,60).q
        var s = divmod(value/1000,60).r
        var h = divmod(q, 60).q
        var m = divmod(q, 60).r
        s = Math.round(s)
        if (s == 60) {s=00; m= m+1}
        if(isNaN(h)){h= 0}
        if(isNaN(m)){m= 0}
        if(isNaN(s)){s= 0}
        if(h<0){h= 0}
        if(m<0){m= 0}
        if(s<0){s= 0}
        res =pad(h)+":"+ pad(m) + ":"+ pad(Math.round(s))
        res = (res !== "00:00:00") ? res : "";
        return res
        
    }
