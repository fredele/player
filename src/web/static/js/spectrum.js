
function drawspectrum(vals){
        function equa(band,value)
        {
        x = band * bandwidth
        y = (spectrumcanvas.clientHeight - value)
        width = bandwidth
        height = spectrumcanvas.clientHeight - y
        ctx.fillStyle = 'rgb(500, 500, 500)';
        ctx.fillRect(x, y, width,height);
        }
    
    vals = vals.split(";")    
    
    var ctx = spectrumcanvas.getContext('2d');
    ctx.clearRect(0, 0, spectrumcanvas.width, spectrumcanvas.height);
    bandscount = vals.length
    bandwidth = spectrumcanvas.clientWidth/ bandscount; 
    for(let i = 0; i <= bandscount; i++){equa(i,vals[i]);}     
    
}


function drawlevel(vals){
    // level : from -60 to 0
    
    vals = vals.split(";")
    var xoffset = 2;
    var r = parseInt(vals[0], 10) +60;
    var l = parseInt(vals[1], 10) +60;

 
    var ctx = levelcanvas.getContext('2d');
    ctx.clearRect(0, 0, levelcanvas.width, levelcanvas.height);
    ctx.fillStyle = 'rgb(500, 500, 500)';
    
    band = levelcanvas.clientWidth/ 2;
    var rh = r*(levelcanvas.clientHeight)/60;
    var lh = l*(levelcanvas.clientHeight)/60;
    ctx.fillRect(0, levelcanvas.clientHeight - rh , band- xoffset,rh );
    ctx.fillRect(band, levelcanvas.clientHeight - lh, band -xoffset,lh);
    
}


