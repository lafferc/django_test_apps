$(function() {
    var x = document.getElementsByClassName("toLocalTime");
    var offset = new Date().getTimezoneOffset()*60*1000 ;
    for (i = 0; i < x.length; ++i) {
        var d = new Date(0);
        var t = Date.parse(x[i].innerHTML);
        d.setUTCMilliseconds(t - offset);
        x[i].innerHTML = d.toString().replace(/GMT.*/g,"");
    }
    var tz = document.getElementById("tz_str");
    if (tz) {
        tz.innerHTML = new Date().toString().match(/\(([A-Za-z\s].*)\)/)[1];
    }
});

