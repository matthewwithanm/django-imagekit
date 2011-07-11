
(function ($) {
    
    /*
    
    JQuery plugin encapsulating an ImageKit queue's status readout.
    
    You can bind an element or group of elements to a queue like so:
    
        $('#elem').queuestatus({ queuename: 'somequeue' });
    
    Or if you only want to monitor the default queue, omit the name for simplicity:
    
        $('#elem').queuestatus();
    
    Start monitoring with the 'start' call and stop, predictibly, with 'stop':
    
        $('#elem').queuestatus('start');
        $('#elem').queuestatus('stop');
    
    */
    
    var JSON = JSON || {};
    
    /// Stringifier from http://www.sitepoint.com/javascript-json-serialization/
    JSON.stringify = JSON.stringify || function (obj) {
        
        var t = typeof(obj);
        
        if (t != "object" || obj === null) {
            
            // simple data type
            if (t == "string") obj = '"'+obj+'"';
            return String(obj);
            
        } else {
            
            // recurse array or object
            var n, v, json = [], arr = (obj && obj.constructor == Array);
            
            for (n in obj) {
                v = obj[n]; t = typeof(v);
                
                if (t == "string") v = '"'+v+'"';
                else if (t == "object" && v !== null) v = JSON.stringify(v);
                
                json.push((arr ? "" : '"' + n + '":') + String(v));
            }
            
            return (arr ? "[" : "{") + String(json) + (arr ? "]" : "}");
        }
    };
    
    $.fn.queuestatus = function () {
        var _defaults = {
            interval: 500,
            endpoint: "ws://localhost:11231/sock/status",
            queuename: 'default'
        };
        
        var options = this.data('options') || _defaults;
        
        var methods = {
            init: function (_options) {
                options = $.extend(options, _options);
                var self = this;
                
                self.data('recently', [0,0,0,0,0,0,0,0,0]);
                self.data('options', options);
                
                var sock = null;
                if ('endpoint' in options && options['endpoint']) {
                    sock = new WebSocket(options['endpoint']);
                    sock.onopen = function () {};
                    sock.onclose = function () {};
                    sock.onmessage = function (e) {
                        var d = $.parseJSON(e.data);
                        if (options.queuename in d) {
                            var qlen = d[options.queuename]
                            lastvalues = self.data('recently');
                            lastvalues.shift();
                            lastvalues.push(qlen);
                            if (lastvalues.every(function (itm) { return itm == 0; })) {
                                self.each(function () {
                                    var elem = $(this);
                                    elem.html("<b>Currently Idle</b>");
                                });
                            } else {
                                self.each(function () {
                                    var elem = $(this);
                                    elem.html("<b>" + qlen + "</b> Queued Signals");
                                });
                            }
                            self.data('recently', lastvalues);
                        }
                    }
                }
                self.data('sock', sock);
                return self.each(function () {
                    var elem = $(this);
                    elem.data('sock', sock);
                });
            },
            start: function () {
                return this.each(function () {
                    var elem = $(this);
                    var interval_id = elem.data('interval_id');
                    var sock = elem.data('sock');
                    if (!interval_id) {
                        interval_id = window.setInterval(function () {
                            if (sock) {
                                var out = { status: options['queuename'] };
                                sock.send(JSON.stringify(out));
                            }
                        }, 500);
                    }
                    elem.data('interval_id', interval_id);
                });
            },
            stop: function () {
                return this.each(function () {
                    var elem = $(this);
                    var interval_id = elem.data('interval_id');
                    if (interval_id) {
                        window.clearInterval(interval_id);
                    }
                    elem.data('interval_id', null);
                });
            }
        };
        
        var method = arguments[0];
        
        if (typeof(methods[method]) !== 'undefined') {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else {
            return methods.init.apply(this, arguments);
        }
    };
})(jQuery);