(function($, window, undefined) {
  'use strict';

  var $doc = $(document),
      Modernizr = window.Modernizr;

  $(document).ready(function() {
    if ($.fn.foundationAlerts) $doc.foundationAlerts();
    if ($.fn.foundationButtons) $doc.foundationButtons();
    if ($.fn.foundationAccordion) $doc.foundationAccordion();
    if ($.fn.foundationNavigation) $doc.foundationNavigation();
    if ($.fn.foundationTopBar) $doc.foundationTopBar();
    if ($.fn.foundationCustomForms) $doc.foundationCustomForms();
    if ($.fn.foundationMediaQueryViewer) $doc.foundationMediaQueryViewer();
    if ($.fn.foundationTabs) $doc.foundationTabs({callback: $.foundation.customForms.appendCustomMarkup});
    if ($.fn.foundationTooltips) $doc.foundationTooltips();
    if ($.fn.foundationMagellan) $doc.foundationMagellan();
    if ($.fn.foundationClearing) $doc.foundationClearing();

    if ($.fn.placeholder) $('input, textarea').placeholder();
  });

  // UNCOMMENT THE LINE YOU WANT BELOW IF YOU WANT IE8 SUPPORT AND ARE USING .block-grids
  // $('.block-grid.two-up>li:nth-child(2n+1)').css({clear: 'both'});
  // $('.block-grid.three-up>li:nth-child(3n+1)').css({clear: 'both'});
  // $('.block-grid.four-up>li:nth-child(4n+1)').css({clear: 'both'});
  // $('.block-grid.five-up>li:nth-child(5n+1)').css({clear: 'both'});

  // Hide address bar on mobile devices (except if #hash present, so we don't mess up deep linking).
  if (Modernizr.touch && !window.location.hash) {
    $(window).on('load',function() {
      setTimeout(function() {
        window.scrollTo(0, 1);
      }, 0);
    });

  }

})(jQuery, this);
