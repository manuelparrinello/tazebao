(function () {
  'use strict';

  document.addEventListener('submit', function (e) {
    if (e.defaultPrevented) return;

    var form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.hasAttribute('data-confirm-message')) return;
    if (form.hasAttribute('data-no-submit-guard')) return;
    if (form.dataset.erpSubmitting === 'true') {
      delete form.dataset.erpSubmitting;
      return;
    }

    if (!form.checkValidity()) return;

    var submitter = e.submitter;
    if (!submitter) {
      submitter = form.querySelector(
        'button[type="submit"], input[type="submit"], button:not([type])'
      );
    }
    if (!submitter) return;

    e.preventDefault();
    submitter.disabled = true;
    submitter.dataset.erpOrigHtml = submitter.innerHTML;
    submitter.innerHTML =
      '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Salvataggio...';

    form.dataset.erpSubmitting = 'true';
    if (form.requestSubmit) {
      form.requestSubmit(submitter);
    } else {
      form.submit();
    }
  });
})();
