(function () {
  'use strict';

  document.addEventListener('submit', function (e) {
    if (e.defaultPrevented) return;

    var form = e.target;
    if (!(form instanceof HTMLFormElement)) return;

    // OPT-IN: agisce solo su form con data-submit-guard="true"
    if (form.dataset.submitGuard !== 'true') return;

    if (form.hasAttribute('data-confirm-message')) return;

    if (form.dataset.erpSubmitting === 'true') {
      delete form.dataset.erpSubmitting;
      return;
    }

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    var submitter = e.submitter;
    if (!submitter) {
      submitter = form.querySelector(
        'button[type="submit"], input[type="submit"], button:not([type])'
      );
    }
    if (!submitter) return;
    if (submitter.hasAttribute('data-no-submit-guard')) return;

    e.preventDefault();
    form.dataset.erpSubmitting = 'true';
    submitter.disabled = true;
    submitter.dataset.erpOrigHtml = submitter.innerHTML;
    submitter.innerHTML =
      '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Salvataggio...';

    if (submitter.name && submitter.value) {
      var hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = submitter.name;
      hidden.value = submitter.value;
      form.appendChild(hidden);
    }

    HTMLFormElement.prototype.submit.call(form);
  });
})();
