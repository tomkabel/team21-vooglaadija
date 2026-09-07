(() => {
  const Vooglaadija = window.Vooglaadija;

  const toolbar = document.querySelector('[data-bulk-toolbar]');
  const selectAll = document.querySelector('[data-select-all]');
  const countLabel = document.querySelector('[data-bulk-count]');
  const deleteBtn = document.querySelector('[data-bulk-delete]');

  function getCheckboxes() {
    return Array.from(document.querySelectorAll('[data-bulk-checkbox]'));
  }

  function getChecked() {
    return getCheckboxes().filter((cb) => cb.checked);
  }

  function updateBulkUI() {
    if (!deleteBtn) return;
    const checkboxes = getCheckboxes();
    const checked = getChecked();
    const checkedCount = checked.length;
    const total = checkboxes.length;

    if (countLabel) countLabel.textContent = `${checkedCount} selected`;
    deleteBtn.disabled = checkedCount === 0;

    if (selectAll) {
      selectAll.checked = total > 0 && checkedCount === total;
      selectAll.indeterminate = checkedCount > 0 && checkedCount < total;
    }
  }

  function toggleAll(checked) {
    for (const cb of getCheckboxes()) cb.checked = checked;
    updateBulkUI();
  }

  if (selectAll) {
    selectAll.addEventListener('change', () => toggleAll(selectAll.checked));
  }

  const rowsContainer = document.getElementById('download-rows');

  const EMPTY_STATE_HTML = `<div id="download-empty-state" class="text-center py-16">
    <div class="mx-auto h-16 w-16 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-5">
      <svg class="h-8 w-8 text-gray-400" aria-hidden="true"><use href="/static/icons/sprite.svg#icon-video" /></svg>
    </div>
    <h3 class="text-lg font-display font-semibold text-gray-400 mb-2">No downloads yet</h3>
    <p class="text-gray-400 max-w-sm mx-auto font-body text-sm">Paste a YouTube URL above to start downloading</p>
  </div>`;

  // Rows removed client-side (e.g. by bulk delete below) never re-render the
  // server's Jinja empty state, so mirror it here once the row list is empty,
  // and toggle it back off as soon as a row reappears (SSE insert, optimistic
  // create, htmx swap, ...).
  function refreshEmptyState() {
    if (!rowsContainer) return;
    const hasRows = rowsContainer.querySelector('.download-row') !== null;
    const emptyState = document.getElementById('download-empty-state');
    if (hasRows) {
      if (emptyState) emptyState.remove();
      if (toolbar) toolbar.style.display = '';
    } else {
      if (!emptyState) rowsContainer.insertAdjacentHTML('beforeend', EMPTY_STATE_HTML);
      if (toolbar) toolbar.style.display = 'none';
    }
  }

  if (rowsContainer) {
    rowsContainer.addEventListener('change', (evt) => {
      if (evt.target?.matches('[data-bulk-checkbox]')) updateBulkUI();
    });

    // Rows inserted by dashboard.js's SSE handling (insertRowSorted) don't go
    // through htmx, so htmx:afterSwap never fires for them. Observing the
    // container directly keeps the selection UI (and empty state) in sync
    // regardless of how rows are added or removed.
    if (window.MutationObserver) {
      const rowsObserver = new MutationObserver(() => {
        updateBulkUI();
        refreshEmptyState();
      });
      rowsObserver.observe(rowsContainer, { childList: true });
    }
  }

  document.body.addEventListener('htmx:afterSwap', () => updateBulkUI());
  document.body.addEventListener('htmx:afterRequest', (evt) => {
    if (evt.detail?.elt?.matches?.('[data-bulk-delete]')) {
      updateBulkUI();
    }
  });

  document.body.addEventListener('bulk-delete-complete', (evt) => {
    const detail = evt.detail || {};
    const deleted = Array.isArray(detail.deleted) ? detail.deleted : [];
    for (const id of deleted) {
      const row = document.querySelector(`[data-job-id="${CSS.escape(String(id))}"]`);
      if (row) row.remove();
    }
    updateBulkUI();
    refreshEmptyState();
    if (typeof Vooglaadija?.toast?.show === 'function') {
      const skipped = Array.isArray(detail.skipped) ? detail.skipped.length : 0;
      const requested =
        typeof detail.requested === 'number' ? detail.requested : deleted.length + skipped;
      if (skipped > 0) {
        Vooglaadija.toast.show(
          `Deleted ${deleted.length} of ${requested} selected downloads (${skipped} skipped).`,
          'info',
        );
      } else {
        Vooglaadija.toast.show(
          `Deleted ${deleted.length} download${deleted.length === 1 ? '' : 's'}.`,
          'success',
        );
      }
    }
  });

  updateBulkUI();
})();
