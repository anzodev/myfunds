(function () {

  $.fn.daterangepicker.defaultOptions = {
    timePicker: true,
    timePicker24Hour: true,
    timePickerSeconds: true,
    cancelButtonClasses: 'btn btn-sm btn-light',
    applyButtonClasses: 'btn btn-sm btn-info',
  }


  const NOTIFY_CLOSING_DELAY = 8000;

  function closeNotifyAfter(ms) {
    setTimeout(function () {
      $(".alert").alert("close");
    }, ms);
  }

  function addNotify(message, category) {
    let markup = (
      '<div class="alert alert-' + category + ' alert-dismissible fade show d-flex justify-content-between align-items-center shadow-sm mb-3 px-3">'
      + '<p class="m-0 mr-4">' + message + '</p>'
      + '<button type="button" class="btn btn-transparent pr-0" data-dismiss="alert">'
      + '<i data-feather="x"></i>'
      + '</button>'
      + '</div>\n'
    );
    $("#alerts").append(markup);
    closeNotifyAfter(NOTIFY_CLOSING_DELAY);
  }

  closeNotifyAfter(NOTIFY_CLOSING_DELAY);


  function featherReplace() {
    feather.replace({
      width: 16,
      height: 16,
    });
  }

  featherReplace();

})();