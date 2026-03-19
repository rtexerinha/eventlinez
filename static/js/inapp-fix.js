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

    // Use clip (not hidden) on X so we don't accidentally kill vertical scroll.
    // overflow-x:hidden on <html> makes Safari treat the page as overflow:hidden
    // on BOTH axes — that's the root cause of the "can't scroll" bug in in-app browsers.
    [html, body].forEach(function (el) {
        if (!el) return;
        el.style.overflowX = 'clip';   // clip does NOT create a scroll container
        el.style.overflowY = 'auto';
        el.style.height = 'auto';
        el.style.position = '';        // never set position:fixed/relative on html/body
    });

    var style = document.createElement('style');
    style.textContent =
        // Allow touch gestures on all elements; individual carousels opt out via passive:false
        '.in-app-browser * { touch-action: pan-y !important; -ms-touch-action: pan-y !important; }' +
        // Page-level containers must remain scrollable
        '.in-app-browser body, .in-app-browser html { overflow-x: clip !important; overflow-y: auto !important; -webkit-overflow-scrolling: touch; }' +
        // main/.container must NOT become independent scroll containers
        '.in-app-browser main, .in-app-browser .container { overflow: visible !important; }' +
        // Ticket panel on event page: no height cap, natural flow
        '.in-app-browser .card-details { overflow-y: visible !important; max-height: none !important; height: auto !important; }';
    (document.head || document.getElementsByTagName('head')[0]).appendChild(style);
})();
