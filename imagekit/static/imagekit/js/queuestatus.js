var sys = require('sys');
var render = require('render');
var WebSocket = require('websocket-client').WebSocket;


sys.puts("YO DOGG --");

//var wsurl = 'ws://localhost:11231/sock/status';
//var wsurl = 'ws://asio-otus.local:11231/sock/status';
var wsurl = 'ws://objectsinspaceandtime.com:11231/sock/status';


var ws = new WebSocket(wsurl, 'sockstatus');

/*
ws.addListener('data', function(buf) {
    sys.debug('Got data: ' + sys.inspect(buf));
});
*/

ws.onmessage = function(m) {
    //sys.debug('Got message: ' + m);
    sys.debug('JSON: '+ render.json(JSON.parse(m.data)));
}

sys.puts("YO DOGG --");

var interv = setInterval(function () {
    ws.send(JSON.stringify({ status: 'default' }));
}, 1000);