(function () {
  'use strict'

  var checkboxes = document.querySelectorAll('.task-checkbox')
  if (!checkboxes.length) return

  checkboxes.forEach(function (cb) {
    cb.addEventListener('change', function () {
      var taskId = this.dataset.taskId
      if (!taskId) return

      var newStatus = this.checked ? 'completata' : 'da_fare'
      var csrfEl = document.querySelector('input[name="csrf_token"]')
      var csrfToken = csrfEl ? csrfEl.value : ''

      fetch('/api/tasks/' + taskId, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ status: newStatus }),
      })
        .then(function (r) {
          return r.json().then(function (d) {
            return { ok: r.ok, data: d }
          })
        })
        .then(function (res) {
          if (!res.ok || res.data.success === false) {
            throw new Error(res.data.error || 'Errore aggiornamento task')
          }
          showFeedback('success', newStatus === 'completata' ? 'Task completata' : 'Task riaperta')
        })
        .catch(function (err) {
          console.error('[tasks-list]', err)
          showFeedback('error', err.message || 'Errore durante l\'aggiornamento')
          this.checked = !this.checked
        }.bind(this))
    })
  })

  function showFeedback(type, msg) {
    var container = document.querySelector('.erp-toast-container')
    if (!container) {
      container = document.createElement('div')
      container.className = 'erp-toast-container position-fixed bottom-0 end-0 p-3'
      document.body.appendChild(container)
    }
    var toast = document.createElement('div')
    toast.className = 'toast align-items-center text-bg-' + (type === 'success' ? 'success' : 'danger') + ' border-0'
    toast.setAttribute('role', 'alert')
    toast.innerHTML = '<div class="d-flex">' +
      '<div class="toast-body">' + escapeHtml(msg) + '</div>' +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Chiudi"></button>' +
      '</div>'
    container.appendChild(toast)
    var bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 2500 })
    bsToast.show()
    toast.addEventListener('hidden.bs.toast', function () { toast.remove() })
  }
})()
