(function () {
    'use strict';
    var ua = navigator.userAgent || '';
    var isInApp = ua.indexOf('Instagram') > -1 || ua.indexOf('FBAN') > -1 ||
        ua.indexOf('FBAV') > -1 || ua.indexOf('LinkedInApp') > -1 || ua.indexOf('Twitter') > -1;
    if (!isInApp) return;

    var html = document.documentElement;
    var body = document.body;

    if (body) body.classList.add('in-app-browser');
    if (ua.indexOf('Instagram') > -1 && body) body.classList.add('instagram-browser');

    [html, body].forEach(function (el) {
        if (!el) return;
        el.style.overflow = 'auto';
        el.style.overflowX = 'hidden';
        el.style.overflowY = 'auto';
        el.style.height = 'auto';
        el.style.position = 'relative';
    });

    var style = document.createElement('style');
    style.textContent =
        '.in-app-browser *{touch-action:auto!important;-ms-touch-action:auto!important;}' +
        '.in-app-browser body,.in-app-browser html,.in-app-browser main,.in-app-browser .container{overflow-y:auto!important;overflow-x:hidden!important;-webkit-overflow-scrolling:touch!important;}' +
        '.in-app-browser .card-details{overflow-y:auto!important;max-height:none!important;height:auto!important;}';
    (document.head || document.getElementsByTagName('head')[0]).appendChild(style);
})();
