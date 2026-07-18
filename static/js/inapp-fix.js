(function () {
  'use strict';
  var ua = navigator.userAgent || '';
  var isInApp =
    ua.indexOf('Instagram') > -1 ||
    ua.indexOf('FBAN') > -1 ||
    ua.indexOf('FBAV') > -1 ||
    ua.indexOf('LinkedInApp') > -1 ||
    ua.indexOf('Twitter') > -1;
  if (!isInApp) return;

  // document.body is null while parsing <head> — add classes to <html> so CSS
  // selectors apply immediately, before a single pixel is painted.
  var html = document.documentElement;
  html.classList.add('in-app-browser');
  if (ua.indexOf('Instagram') > -1) html.classList.add('instagram-browser');

  html.style.overflowX = 'clip';
  html.style.overflowY = 'auto';
  html.style.height = 'auto';

  var style = document.createElement('style');
  style.textContent =
    'html.in-app-browser,html.in-app-browser body{overflow-x:clip !important;overflow-y:auto !important;height:auto !important;}' +
    'html.in-app-browser *{touch-action:pan-y !important;-ms-touch-action:pan-y !important;}' +
    // main/.container must NOT become independent scroll containers
    'html.in-app-browser main,html.in-app-browser .container{overflow:visible !important;}' +
    // Ticket panel: no height cap, natural flow
    'html.in-app-browser .card-details{overflow-y:visible !important;max-height:none !important;height:auto !important;overscroll-behavior:auto !important;}';
  (document.head || document.getElementsByTagName('head')[0]).appendChild(style);
})();
