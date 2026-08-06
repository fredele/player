my_template = \
'<html> \
<head> \
<title>Player Music Files</title>\
<style> \
.even-dir { background-color: #efe0ef } \
.even { background-color: #eee } \
.odd-dir {background-color: #f0d0ef } \
.odd { background-color: #dedede } \
.icon { text-align: center } \
.listing { \
    margin-left: auto; \
    margin-right: auto; \
    width: 50%%; \
    padding: 0.1em; \
    } \
\
body { border: 0; padding: 0; margin: 0; background-color: #efefef; } \
h1 {padding-left: 45px; background-color: #777; color: white; } \
img#icon { position: absolute; width: 20px; height: 20px; top: 10px;left: 10px;} \
</style> \
<link rel="icon" type="image/png" href="/assets/favicon.png">\
</head> \
\
<body> \
<h1>%(header)s</h1> \
<img src="/assets/favicon.png" id="icon">\
\
<table> \
    <thead> \
        <tr> \
            <th>Filename</th> \
            <th>Size</th> \
            <th>Content type</th> \
            <th>Content encoding</th> \
        </tr> \
    </thead> \
    <tbody> \
%(tableContent)s \
    </tbody> \
</table> \
\
</body> \
</html>'