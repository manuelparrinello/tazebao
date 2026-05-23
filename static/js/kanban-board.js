(function () {
  'use strict'

  function debug(msg) {
    if (window.ERP_DEBUG_KANBAN) {
      console.debug('[kanban]', msg)
    }
  }

  debug('init start')

  if (typeof Sortable === 'undefined') {
    console.warn(
      '[kanban] SortableJS non caricato — il drag & drop della board non sarà disponibile.'
    )
    debug('Sortable non definito — fermo')
    return
  }
  debug('Sortable disponibile')

  var wrapper = document.querySelector('.kanban-wrapper')
  if (!wrapper) {
    debug('wrapper .kanban-wrapper non trovato — fermo')
    return
  }
  debug('wrapper trovato')

  if (wrapper.dataset.canDrag !== 'true') {
    debug('data-can-drag!="true" (' + wrapper.dataset.canDrag + ') — fermo')
    return
  }
  debug('canDrag = true')

  var containers = wrapper.querySelectorAll('.kanban-cards')
  debug('container .kanban-cards trovati: ' + containers.length)
  if (!containers.length) {
    debug('nessun container — fermo')
    return
  }

  var initCount = 0
  containers.forEach(function (el) {
    var column = el.closest('.kanban-column')
    if (!column) {
      debug('container senza .kanban-column padre — skip')
      return
    }
    var status = column.dataset.status
    if (status === 'altro') {
      debug('colonna altro — skip Sortable')
      return
    }
    debug('init Sortable su status=' + status)

    new Sortable(el, {
      group: {
        name: 'kanban-board',
        put: function (to) {
          var toCol = to.el.closest('.kanban-column')
          return toCol && toCol.dataset.status !== 'altro'
        },
      },
      handle: '.kanban-drag-handle',
      filter: 'a, button',
      preventOnFilter: false,
      animation: 150,
      ghostClass: 'kanban-ghost',
      chosenClass: 'kanban-chosen',
      dragClass: 'kanban-dragging',
      delay: 200,
      delayOnTouchOnly: true,
      onEnd: handleDrop,
    })
    initCount++
  })
  debug('Sortable inizializzati: ' + initCount)

  function handleDrop(evt) {
    debug('handleDrop taskId=' + evt.item.dataset.taskId + ' from=' + (evt.from ? evt.from.closest('.kanban-column').dataset.status : '?') + ' to=' + (evt.to ? evt.to.closest('.kanban-column').dataset.status : '?'))

    var taskId = evt.item.dataset.taskId
    if (!taskId) return

    var toColumn = evt.to.closest('.kanban-column')
    var newStatus = toColumn ? toColumn.dataset.status : null
    if (!newStatus || newStatus === 'altro') {
      debug('drop rifiutato: status=' + newStatus)
      revertCard(evt)
      return
    }

    var payload = { status: newStatus }

    fetch('/api/tasks/' + taskId, {
      method: 'PATCH',
      headers: csrfHeaders({
        'Content-Type': 'application/json',
        Accept: 'application/json',
      }),
      body: JSON.stringify(payload),
    })
      .then(function (r) {
        return r.json().then(function (d) {
          return { ok: r.ok, data: d }
        })
      })
      .then(function (res) {
        if (!res.ok || res.data.success === false) {
          throw new Error(
            res.data.error || 'Errore aggiornamento task'
          )
        }
        refreshCounts()
        showFeedback(
          'success',
          'Task spostata in ' + statusLabel(newStatus)
        )
      })
      .catch(function (err) {
        console.error('Drag & drop error:', err)
        revertCard(evt)
        showFeedback(
          'error',
          err.message || 'Errore durante lo spostamento'
        )
      })
  }

  function revertCard(evt) {
    if (evt.from && evt.item) {
      evt.from.appendChild(evt.item)
    }
    refreshCounts()
  }

  function refreshCounts() {
    wrapper.querySelectorAll('.kanban-column').forEach(function (col) {
      var el = col.querySelector('.kanban-col-count')
      if (!el) return
      el.textContent = col.querySelectorAll('.kanban-card').length
    })
  }

  function statusLabel(status) {
    var map = {
      da_fare: 'Da fare',
      in_corso: 'In corso',
      in_revisione: 'In revisione',
      completata: 'Completata',
      annullata: 'Annullata',
    }
    return map[status] || status.replace(/_/g, ' ')
  }

  function showFeedback(type, msg) {
    var container = document.querySelector('.erp-toast-container')
    if (!container) return

    var toast = document.createElement('div')
    toast.className =
      'toast align-items-center text-bg-' +
      (type === 'success' ? 'success' : 'danger') +
      ' border-0'
    toast.setAttribute('role', 'alert')
    toast.innerHTML =
      '<div class="d-flex">' +
      '<div class="toast-body">' +
      escapeHtml(msg) +
      '</div>' +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Chiudi"></button>' +
      '</div>'

    container.appendChild(toast)
    var bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 3000 })
    bsToast.show()
    toast.addEventListener('hidden.bs.toast', function () {
      toast.remove()
    })
  }
})()
