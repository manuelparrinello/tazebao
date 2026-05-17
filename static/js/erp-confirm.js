(function () {
  'use strict';

  var resolveConfirm = null;

  function showModal(title, message, dangerLabel) {
    document.getElementById('erpConfirmTitle').textContent = title;
    document.getElementById('erpConfirmMessage').textContent = message;
    var btn = document.getElementById('erpConfirmButton');
    btn.innerHTML =
      '<i class="bi bi-trash3"></i>&nbsp;' +
      (dangerLabel || 'Conferma eliminazione');
    document.getElementById('erpConfirmOverlay').style.display = 'flex';
    btn.focus();
    document.body.style.overflow = 'hidden';
  }

  function hideModal() {
    document.getElementById('erpConfirmOverlay').style.display = 'none';
    document.body.style.overflow = '';
  }

  window.erpConfirm = function (message, options) {
    options = options || {};
    return new Promise(function (resolve) {
      resolveConfirm = resolve;
      showModal(
        options.title || 'Conferma azione',
        message,
        options.dangerLabel
      );
    });
  };

  function doConfirm() {
    if (resolveConfirm) resolveConfirm(true);
    resolveConfirm = null;
    hideModal();
  }

  function doDismiss() {
    if (resolveConfirm) resolveConfirm(false);
    resolveConfirm = null;
    hideModal();
  }

  document.addEventListener('submit', function (e) {
    var form = e.target;
    var msg = form.getAttribute('data-confirm-message');
    if (!msg) return;
    if (form.dataset.erpConfirming === 'true') return;
    e.preventDefault();
    var submitter = e.submitter || null;
    form.dataset.erpConfirming = 'true';
    window
      .erpConfirm(msg, {
        title: form.getAttribute('data-confirm-title') || undefined,
        dangerLabel:
          form.getAttribute('data-confirm-danger-label') || undefined,
      })
      .then(function (confirmed) {
        delete form.dataset.erpConfirming;
        if (confirmed) {
          form.removeAttribute('data-confirm-message');
          if (submitter) {
            form.requestSubmit(submitter);
          } else {
            form.submit();
          }
        }
      });
  });

  document.addEventListener('click', function (e) {
    var target = e.target.closest('[data-confirm-message]');
    if (!target) return;
    if (target.tagName === 'FORM') return;
    if (target.tagName === 'INPUT' && target.type === 'submit') return;

    var form = target.closest('form');
    if (form && form.hasAttribute('data-confirm-message')) return;

    e.preventDefault();
    window
      .erpConfirm(target.getAttribute('data-confirm-message'), {
        title: target.getAttribute('data-confirm-title') || undefined,
        dangerLabel:
          target.getAttribute('data-confirm-danger-label') || undefined,
      })
      .then(function (confirmed) {
        if (!confirmed) return;
        if (target.tagName === 'A') {
          window.location.href = target.href;
        } else if (target.tagName === 'BUTTON' && form) {
          form.requestSubmit(target);
        } else if (target.tagName === 'BUTTON') {
          var f = target.closest('form');
          if (f) f.requestSubmit(target);
        }
      });
  });

  document
    .getElementById('erpConfirmButton')
    .addEventListener('click', doConfirm);

  document.querySelectorAll('[data-erp-confirm-dismiss]').forEach(function (el) {
    el.addEventListener('click', doDismiss);
  });

  document
    .getElementById('erpConfirmOverlay')
    .addEventListener('click', function (e) {
      if (e.target === this) doDismiss();
    });

  document.addEventListener('keydown', function (e) {
    if (
      e.key === 'Escape' &&
      document.getElementById('erpConfirmOverlay').style.display === 'flex'
    ) {
      doDismiss();
    }
  });
})();
