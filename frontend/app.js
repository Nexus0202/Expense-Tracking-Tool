/* ═══════════════════════════════════════════════════════════════
   Expense Tracker — Vanilla JS frontend
   Talks to FastAPI backend at http://localhost:8000
   No authentication required.
═══════════════════════════════════════════════════════════════ */

const API = 'http://localhost:8000/api/v1';

// ── App State ─────────────────────────────────────────────────────────────────
const state = {
  page:     1,
  pageSize: 15,
  charts:   { category: null, monthly: null },
  selectedFile: null,
};

// ── API Helper ────────────────────────────────────────────────────────────────

async function api(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };

  if (!(opts.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res  = await fetch(`${API}${path}`, { ...opts, headers });
  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(data?.detail || `Error ${res.status}`);
  return data;
}

// ── Toast Notifications ───────────────────────────────────────────────────────

function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── Navigation ────────────────────────────────────────────────────────────────

function showView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
  document.getElementById(`view-${name}`).classList.remove('hidden');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelector(`[data-view="${name}"]`)?.classList.add('active');

  if (name === 'dashboard') loadDashboard();
  if (name === 'expenses')  { state.page = 1; loadExpenses(); }
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

async function loadDashboard() {
  const start = document.getElementById('dash-start').value;
  const end   = document.getElementById('dash-end').value;

  const params = [];
  if (start) params.push(`start_date=${start}T00:00:00`);
  if (end)   params.push(`end_date=${end}T23:59:59`);

  const qs = params.length ? '?' + params.join('&') : '';

  try {
    const data = await api(`/dashboard/summary${qs}`);
    renderDashboard(data);
  } catch (err) {
    toast(err.message, 'error');
  }
}

function renderDashboard(data) {
  const fmt = n => '₹' + Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2 });

  document.getElementById('dash-total').textContent   = fmt(data.total_expenses);
  document.getElementById('dash-count').textContent   = data.total_count;
  document.getElementById('dash-top-cat').textContent = data.by_category[0]?.category || '—';

  const avg = data.total_count ? data.total_expenses / data.total_count : 0;
  document.getElementById('dash-avg').textContent = fmt(avg);

  renderCategoryChart(data.by_category);
  renderMonthlyChart(data.by_month);
}

function renderCategoryChart(byCategory) {
  const ctx = document.getElementById('chart-category');
  if (state.charts.category) state.charts.category.destroy();

  const palette = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6',
                   '#06b6d4','#f97316','#ec4899','#6366f1'];

  state.charts.category = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels:   byCategory.map(r => r.category),
      datasets: [{ data: byCategory.map(r => r.total), backgroundColor: palette, borderWidth: 2 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 10 } },
        tooltip: { callbacks: { label: ctx => ` ₹${ctx.parsed.toLocaleString('en-IN')}` } },
      },
    },
  });
}

function renderMonthlyChart(byMonth) {
  const ctx = document.getElementById('chart-monthly');
  if (state.charts.monthly) state.charts.monthly.destroy();

  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  state.charts.monthly = new Chart(ctx, {
    type: 'bar',
    data: {
      labels:   byMonth.map(r => `${months[r.month - 1]} ${r.year}`),
      datasets: [{
        label: 'Total Spent (₹)',
        data: byMonth.map(r => r.total),
        backgroundColor: '#3b82f6',
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: v => '₹' + v.toLocaleString('en-IN') },
        },
      },
    },
  });
}

function clearDashboardFilter() {
  document.getElementById('dash-start').value = '';
  document.getElementById('dash-end').value   = '';
  loadDashboard();
}

// ── Expenses List ─────────────────────────────────────────────────────────────

async function loadExpenses() {
  const start    = document.getElementById('filter-start').value;
  const end      = document.getElementById('filter-end').value;
  const category = document.getElementById('filter-category').value;

  const params = [`page=${state.page}`, `page_size=${state.pageSize}`];
  if (start)    params.push(`start_date=${start}T00:00:00`);
  if (end)      params.push(`end_date=${end}T23:59:59`);
  if (category) params.push(`category=${encodeURIComponent(category)}`);

  try {
    const data = await api('/expenses/?' + params.join('&'));
    renderExpenseTable(data);
  } catch (err) {
    toast(err.message, 'error');
  }
}

function renderExpenseTable(data) {
  const tbody = document.getElementById('expense-tbody');
  const fmt   = n => '₹' + Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2 });

  if (!data.items.length) {
    tbody.innerHTML = `
      <tr><td colspan="6">
        <div class="empty-state">
          <div class="empty-icon">📭</div>
          <p>No expenses found. Add one or upload a PDF!</p>
        </div>
      </td></tr>`;
  } else {
    tbody.innerHTML = data.items.map(exp => `
      <tr>
        <td>${formatDate(exp.date)}</td>
        <td>${exp.category}</td>
        <td style="max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
            title="${escHtml(exp.description || '')}">${escHtml(exp.description || '—')}</td>
        <td><strong>${fmt(exp.amount)}</strong></td>
        <td><span class="badge badge-${exp.source}">${exp.source}</span></td>
        <td style="white-space:nowrap;">
          <button class="btn btn-outline btn-sm" onclick="openEditModal('${exp.id}')">✏️ Edit</button>
          <button class="btn btn-danger btn-sm"  onclick="deleteExpense('${exp.id}')" style="margin-left:6px;">🗑️</button>
        </td>
      </tr>
    `).join('');
  }

  const total      = data.total;
  const totalPages = data.total_pages;
  const from       = total ? (state.page - 1) * state.pageSize + 1 : 0;
  const to         = Math.min(state.page * state.pageSize, total);

  document.getElementById('pagination-info').textContent =
    total ? `Showing ${from}–${to} of ${total} expenses` : 'No results';

  document.getElementById('btn-prev').disabled = state.page <= 1;
  document.getElementById('btn-next').disabled = state.page >= totalPages;
}

function applyFilters() { state.page = 1; loadExpenses(); }

function clearFilters() {
  document.getElementById('filter-start').value    = '';
  document.getElementById('filter-end').value      = '';
  document.getElementById('filter-category').value = '';
  state.page = 1;
  loadExpenses();
}

function changePage(delta) {
  state.page += delta;
  loadExpenses();
}

// ── Add / Edit Expense Modal ──────────────────────────────────────────────────

function openAddModal() {
  document.getElementById('modal-title').textContent      = 'Add Expense';
  document.getElementById('modal-submit-btn').textContent = 'Save';
  document.getElementById('exp-id').value                 = '';
  document.getElementById('expense-form').reset();
  document.getElementById('exp-date').value = new Date().toISOString().slice(0, 10);
  document.getElementById('expense-modal').classList.remove('hidden');
}

async function openEditModal(id) {
  try {
    const exp = await api(`/expenses/${id}`);

    document.getElementById('modal-title').textContent      = 'Edit Expense';
    document.getElementById('modal-submit-btn').textContent = 'Update';
    document.getElementById('exp-id').value          = exp.id;
    document.getElementById('exp-amount').value      = exp.amount;
    document.getElementById('exp-date').value        = exp.date.slice(0, 10);
    document.getElementById('exp-category').value    = exp.category;
    document.getElementById('exp-description').value = exp.description || '';

    document.getElementById('expense-modal').classList.remove('hidden');
  } catch (err) {
    toast(err.message, 'error');
  }
}

function closeModal() {
  document.getElementById('expense-modal').classList.add('hidden');
}

function closeModalOnBackdrop(e) {
  if (e.target === document.getElementById('expense-modal')) closeModal();
}

async function handleExpenseSubmit(e) {
  e.preventDefault();
  const id     = document.getElementById('exp-id').value;
  const btn    = document.getElementById('modal-submit-btn');
  const isEdit = Boolean(id);

  const payload = {
    amount:      parseFloat(document.getElementById('exp-amount').value),
    category:    document.getElementById('exp-category').value,
    description: document.getElementById('exp-description').value,
    date:        document.getElementById('exp-date').value + 'T00:00:00',
  };

  btn.innerHTML = '<span class="spinner"></span>';
  btn.disabled  = true;

  try {
    if (isEdit) {
      await api(`/expenses/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
      toast('Expense updated!', 'success');
    } else {
      await api('/expenses/', { method: 'POST', body: JSON.stringify({ ...payload, source: 'manual' }) });
      toast('Expense added!', 'success');
    }
    closeModal();
    loadExpenses();
    loadDashboard();
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.textContent = isEdit ? 'Update' : 'Save';
    btn.disabled    = false;
  }
}

async function deleteExpense(id) {
  if (!confirm('Delete this expense? This cannot be undone.')) return;
  try {
    await api(`/expenses/${id}`, { method: 'DELETE' });
    toast('Expense deleted.', 'info');
    loadExpenses();
    loadDashboard();
  } catch (err) {
    toast(err.message, 'error');
  }
}

// ── PDF Upload ────────────────────────────────────────────────────────────────

function onFileSelected(e) {
  const file = e.target.files[0];
  if (file) setSelectedFile(file);
}

function onDragOver(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.add('drag-over');
}

function onDragLeave() {
  document.getElementById('drop-zone').classList.remove('drag-over');
}

function onDrop(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.name.endsWith('.pdf')) {
    setSelectedFile(file);
  } else {
    toast('Please drop a PDF file.', 'error');
  }
}

function setSelectedFile(file) {
  state.selectedFile = file;
  document.getElementById('upload-filename').textContent =
    `📎 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  document.getElementById('upload-btn').disabled = false;
  document.getElementById('upload-result').classList.add('hidden');
}

async function uploadPDF() {
  if (!state.selectedFile) return;

  const btn = document.getElementById('upload-btn');
  btn.innerHTML = '<span class="spinner"></span> Extracting with AI…';
  btn.disabled  = true;

  const form = new FormData();
  form.append('file', state.selectedFile);

  try {
    const expenses = await api('/upload/pdf', { method: 'POST', body: form });
    renderUploadResult(expenses);
    toast(`${expenses.length} expense(s) extracted and saved!`, 'success');
    state.selectedFile = null;
    document.getElementById('upload-filename').textContent = '';
    document.getElementById('pdf-input').value = '';
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.textContent = '🚀 Extract Expenses with AI';
    btn.disabled    = true;
  }
}

function renderUploadResult(expenses) {
  const el  = document.getElementById('upload-result');
  const fmt = n => '₹' + Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2 });

  if (!expenses.length) {
    el.innerHTML = '<p style="color:var(--text-muted);">No expenses were detected in this PDF.</p>';
    el.classList.remove('hidden');
    return;
  }

  el.innerHTML = `
    <p style="font-weight:700;margin-bottom:12px;color:var(--success);">
      ✅ ${expenses.length} expense(s) extracted and saved
    </p>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead><tr>
        <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #bbf7d0;">Date</th>
        <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #bbf7d0;">Category</th>
        <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #bbf7d0;">Description</th>
        <th style="text-align:right;padding:6px 8px;border-bottom:1px solid #bbf7d0;">Amount</th>
      </tr></thead>
      <tbody>${expenses.map(exp => `
        <tr>
          <td style="padding:6px 8px;">${formatDate(exp.date)}</td>
          <td style="padding:6px 8px;">${exp.category}</td>
          <td style="padding:6px 8px;">${escHtml(exp.description || '—')}</td>
          <td style="padding:6px 8px;text-align:right;font-weight:600;">${fmt(exp.amount)}</td>
        </tr>`).join('')}
      </tbody>
    </table>
    <button class="btn btn-outline btn-sm" style="margin-top:12px;" onclick="showView('expenses')">
      View All Expenses →
    </button>
  `;
  el.classList.remove('hidden');
}

// ── Utility Helpers ───────────────────────────────────────────────────────────

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Start ─────────────────────────────────────────────────────────────────────
loadDashboard();
