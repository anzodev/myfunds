(function ($) {

  $.fn.daterangepicker.defaultOptions = {
    locale: {
      applyLabel: "Выбрать",
      cancelLabel: "Отменить",
      fromLabel: "С",
      toLabel: "По",
      daysOfWeek: [
        "Вс",
        "Пн",
        "Вт",
        "Ср",
        "Чт",
        "Пт",
        "Сб"
      ],
      monthNames: [
        "Январь",
        "Февраль",
        "Март",
        "Апрель",
        "Май",
        "Июнь",
        "Июль",
        "Август",
        "Сентябрь",
        "Октябрь",
        "Ноябрь",
        "Декабрь"
      ]
    }
  };

  function featherReplace() {
    feather.replace({
      width: 16,
      height: 16,
    });
  }

  function closeAlertsAfter(ms) {
    setTimeout(function () {
      $(".alert").alert("close");
    }, ms);
  }

  function addAlert(message, category = "info") {
    let markup = (
      '<div class="alert alert-' + category + ' alert-dismissible fade show d-flex justify-content-between align-items-center shadow-sm mb-3 px-3">'
      + '<p class="m-0 mr-4">' + message + '</p>'
      + '<button type="button" class="btn btn-transparent pr-0" data-dismiss="alert">'
      + '<i data-feather="x"></i>'
      + '</button>'
      + '</div>\n'
    );
    $("#alerts").append(markup);
    closeAlertsAfter(3000);
  }

  closeAlertsAfter(3000);

  $('.display-toggler').on('click', function () {
    let targetId = $(this).attr('data-target');
    let target = $('#' + targetId);
    $(this).toggleClass('active');
    target.toggleClass('d-none');
  });

  class myfundAPI {
    constructor(url) {
      this.url = "/ajax/"
    }

    isOk(data) {
      return data.result === "ok"
    }

    sendParams(url, params) {
      return $.ajax({
        method: 'POST',
        url: url,
        contentType: 'application/json',
        data: JSON.stringify(params),
        timeout: 10000,
      });
    }

    getBalanceInfo(params) {
      return this.sendParams(this.url + 'getBalanceInfo', params);
    }
  }

  featherReplace();
  bsCustomFileInput.init();

  window.myfund = {
    API: myfundAPI,
    closeAlertsAfter: closeAlertsAfter,
    addAlert: addAlert,
    featherReplace: featherReplace,
  }

})(jQuery);