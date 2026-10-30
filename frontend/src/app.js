// ==============================================================================
// Sistema de Captacion, Prospeccion y CRM Local - Frontend Application
// Version: 5.0.0
// Pipeline Comercial de 12 Fases, Kanban, Ficha Integral y Doble Confirmacion
// Estilo: Notion / Obsidian Slate Neutro (Cero Emojis, Iconos Lucide SVG)
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    stages: [],
    board: {},
    leads: [],
    trashLeads: [],
    activeCategory: '',
    searchQuery: '',
    currentView: 'leads',       // 'leads', 'map', 'calendar', 'metrics', 'settings'
    leadViewMode: 'kanban',     // 'kanban', 'table', 'trash'
    activeMobileStage: 'EXTRACTED',
    selectedLead: null,
    draggedLeadId: null,
    pendingStageTransition: null,
    pendingDestructiveAction: null,
    activeMapZone: 'zona-rio',
    activeMapCategory: 'dentistas',
    mapInstance: null,
    mapMarkersLayer: null,
    mapPolygonsLayer: null,
    activeSweepJobId: null,
    sweepPollInterval: null,
    onboardingStep: 1,
    settings: {
      whatsapp_template: 'Hola, buen dia.',
      lan_ip: window.location.hostname,
      proxy_port: window.location.port || '80',
      lan_url: window.location.origin,
      local_url: window.location.origin
    }
  };

  // DOM Elements - Shell & Nav
  const pageTitle = document.getElementById('page-title');
  const navBtnLeads = document.getElementById('nav-btn-leads');
  const navBtnMap = document.getElementById('nav-btn-map');
  const navBtnCalendar = document.getElementById('nav-btn-calendar');
  const navBtnMetrics = document.getElementById('nav-btn-metrics');
  const navBtnSettings = document.getElementById('nav-btn-settings');
  const mobNavLeads = document.getElementById('mob-nav-leads');
  const mobNavMap = document.getElementById('mob-nav-map');
  const mobNavCalendar = document.getElementById('mob-nav-calendar');
  const mobNavMetrics = document.getElementById('mob-nav-metrics');
  const mobNavSettings = document.getElementById('mob-nav-settings');
  const badgeLeadsCount = document.getElementById('badge-leads-count');
  const badgeEventsCount = document.getElementById('badge-events-count');
  const liveReloadDot = document.getElementById('live-reload-dot');
  const liveReloadText = document.getElementById('live-reload-text');
  const diagWsStatus = document.getElementById('diag-ws-status');
  const sidebarLanLabel = document.getElementById('sidebar-lan-label');
  const btnStartOnboarding = document.getElementById('btn-start-onboarding');

  // DOM Elements - Views
  const viewLeads = document.getElementById('view-leads');
  const viewMap = document.getElementById('view-map');
  const viewCalendar = document.getElementById('view-calendar');
  const viewMetrics = document.getElementById('view-metrics');
  const viewSettings = document.getElementById('view-settings');

  // Controls & Filters
  const leadsSearchInput = document.getElementById('leads-search-input');
  const categoryFilters = document.getElementById('category-filters');
  const btnToggleKanban = document.getElementById('btn-toggle-kanban');
  const btnToggleTable = document.getElementById('btn-toggle-table');
  const btnToggleTrash = document.getElementById('btn-toggle-trash');
  const trashCounter = document.getElementById('trash-counter');
  const statTotalLeads = document.getElementById('stat-total-leads');
  const statWhatsappLeads = document.getElementById('stat-whatsapp-leads');
  const statStagnantLeads = document.getElementById('stat-stagnant-leads');
  const statDueLeads = document.getElementById('stat-due-leads');
  const mobileStageTabs = document.getElementById('mobile-stage-tabs');
  const kanbanBoardContainer = document.getElementById('kanban-board-container');
  const denseTableContainer = document.getElementById('dense-table-container');
  const denseTableBody = document.getElementById('dense-table-body');
  const leadsEmptyState = document.getElementById('leads-empty-state');
  const topBtnNewLead = document.getElementById('top-btn-new-lead');
  const topBtnNewEvent = document.getElementById('top-btn-new-event');
  const topBtnRefresh = document.getElementById('top-btn-refresh');

  // Drawer (Ficha Integral)
  const drawerLeadDetail = document.getElementById('drawer-lead-detail');
  const drawerClose = document.getElementById('drawer-close');
  const drawerLeadName = document.getElementById('drawer-lead-name');
  const drawerLeadCategory = document.getElementById('drawer-lead-category');
  const drawerCurrentStage = document.getElementById('drawer-current-stage');
  const drawerProbScore = document.getElementById('drawer-prob-score');
  const drawerStageSelect = document.getElementById('drawer-stage-select');
  const drawerActionBar = document.getElementById('drawer-action-bar');
  const drawerPhone = document.getElementById('drawer-phone');
  const drawerWebsite = document.getElementById('drawer-website');
  const drawerEmail = document.getElementById('drawer-email');
  const drawerAddress = document.getElementById('drawer-address');
  const drawerReviews = document.getElementById('drawer-reviews');
  const drawerHealthScore = document.getElementById('drawer-health-score');
  const drawerSalesArgsList = document.getElementById('drawer-sales-args-list');
  const drawerStagnationAlert = document.getElementById('drawer-stagnation-alert');
  const drawerPostponedAlert = document.getElementById('drawer-postponed-alert');
  const drawerNotesCount = document.getElementById('drawer-notes-count');
  const drawerNotesList = document.getElementById('drawer-notes-list');
  const formDrawerNote = document.getElementById('form-drawer-note');
  const drawerNoteContent = document.getElementById('drawer-note-content');
  const drawerTimelineFeed = document.getElementById('drawer-timeline-feed');
  const drawerBtnDelete = document.getElementById('drawer-btn-delete');
  const drawerBtnRestore = document.getElementById('drawer-btn-restore');
  const drawerBtnPurge = document.getElementById('drawer-btn-purge');
  const drawerBtnResetHistory = document.getElementById('drawer-btn-reset-history');

  // Stage Action Modal
  const modalStageAction = document.getElementById('modal-stage-action');
  const modalStageActionClose = document.getElementById('modal-stage-action-close');
  const modalStageActionCancel = document.getElementById('modal-stage-action-cancel');
  const formStageAction = document.getElementById('form-stage-action');
  const stageActionTitle = document.getElementById('stage-action-title');
  const stageActionPostponedFields = document.getElementById('stage-action-postponed-fields');
  const stagePostponedDate = document.getElementById('stage-postponed-date');
  const stagePostponedNote = document.getElementById('stage-postponed-note');
  const stageActionRegrettedFields = document.getElementById('stage-action-regretted-fields');
  const stageRegretReason = document.getElementById('stage-regret-reason');
  const stageRegretAmount = document.getElementById('stage-regret-amount');
  const stageRegretService = document.getElementById('stage-regret-service');
  const stageRegretDetails = document.getElementById('stage-regret-details');
  const stageActionLostFields = document.getElementById('stage-action-lost-fields');
  const stageLossReason = document.getElementById('stage-loss-reason');
  const stageGenericNote = document.getElementById('stage-generic-note');

  // Double Confirmation Modal
  const modalDoubleConfirm = document.getElementById('modal-double-confirm');
  const confirmModalTitle = document.getElementById('confirm-modal-title');
  const confirmModalClose = document.getElementById('confirm-modal-close');
  const confirmStep1 = document.getElementById('confirm-step-1');
  const confirmStep2 = document.getElementById('confirm-step-2');
  const confirmWarningText = document.getElementById('confirm-warning-text');
  const confirmBtnCancel1 = document.getElementById('confirm-btn-cancel-1');
  const confirmBtnCancel2 = document.getElementById('confirm-btn-cancel-2');
  const confirmBtnNext = document.getElementById('confirm-btn-next');
  const confirmBtnExecute = document.getElementById('confirm-btn-execute');

  // Manual Lead Creation Modal
  const modalNewLead = document.getElementById('modal-new-lead');
  const modalNewLeadClose = document.getElementById('modal-new-lead-close');
  const modalNewLeadCancel = document.getElementById('modal-new-lead-cancel');
  const formNewLead = document.getElementById('form-new-lead');
  const newLeadName = document.getElementById('new-lead-name');
  const newLeadCat = document.getElementById('new-lead-cat');
  const newLeadPhone = document.getElementById('new-lead-phone');
  const newLeadWebsite = document.getElementById('new-lead-website');
  const newLeadEmail = document.getElementById('new-lead-email');
  const newLeadAddress = document.getElementById('new-lead-address');
  const newLeadNotes = document.getElementById('new-lead-notes');
  const leadDupAlert = document.getElementById('lead-dup-alert');
  const leadDupMsg = document.getElementById('lead-dup-msg');

  // Calendar DOM
  const calendarEventsList = document.getElementById('calendar-events-list');
  const calendarEmptyState = document.getElementById('calendar-empty-state');
  const imminentAlertsBanner = document.getElementById('imminent-alerts-banner');
  const btnRequestNotifications = document.getElementById('btn-request-notifications');
  const btnCalendarAddEvent = document.getElementById('btn-calendar-add-event');
  const modalEvent = document.getElementById('modal-event');
  const modalEventClose = document.getElementById('modal-event-close');
  const modalEventCancel = document.getElementById('modal-event-cancel');
  const formNewEvent = document.getElementById('form-new-event');
  const eventLeadIdSelect = document.getElementById('event-lead-id');
  const eventStartTimeInput = document.getElementById('event-start-time');
  const eventEndTimeInput = document.getElementById('event-end-time');

  // Settings DOM
  const settingsWhatsappTemplate = document.getElementById('settings-whatsapp-template');
  const btnSaveWhatsappTemplate = document.getElementById('btn-save-whatsapp-template');
  const linkLocalPc = document.getElementById('link-local-pc');
  const linkLanMobile = document.getElementById('link-lan-mobile');
  const btnCopyLanUrl = document.getElementById('btn-copy-lan-url');

  // ============================================================================
  // 1. Live Reload WebSocket Client
  // ============================================================================
  function initLiveReload() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/dev/live-reload`;
    let ws = null;
    let retryInterval = 3000;

    function connect() {
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          if (liveReloadDot) liveReloadDot.style.backgroundColor = 'var(--badge-green-text)';
          if (liveReloadText) liveReloadText.textContent = 'Conectado en vivo';
          if (diagWsStatus) diagWsStatus.textContent = 'Conectado';
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.action === 'reload') {
              window.location.reload();
            }
          } catch (e) {
            if (event.data === 'reload') {
              window.location.reload();
            }
          }
        };

        ws.onclose = () => {
          if (liveReloadDot) liveReloadDot.style.backgroundColor = 'var(--badge-amber-text)';
          if (liveReloadText) liveReloadText.textContent = 'Reconectando...';
          if (diagWsStatus) diagWsStatus.textContent = 'Reconectando';
          setTimeout(connect, retryInterval);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        setTimeout(connect, retryInterval);
      }
    }

    connect();
  }

  // ============================================================================
  // 2. Data Fetching
  // ============================================================================
  async function loadInitialData() {
    await Promise.all([
      loadStages(),
      loadSettings(),
      loadPipelineBoard(),
      loadTrashCount(),
      loadCalendarEvents(),
      loadAlerts()
    ]);
  }

  async function loadStages() {
    try {
      const res = await fetch('/api/v1/pipeline/stages');
      if (res.ok) {
        const data = await res.json();
        state.stages = data.stages;
        populateStageDropdowns(data.stages);
        renderMobileStageTabs(data.stages);
      }
    } catch (e) {
      console.error('[Stages] Error al cargar fases:', e);
    }
  }

  async function loadSettings() {
    try {
      const res = await fetch('/api/v1/settings');
      if (res.ok) {
        const data = await res.json();
        state.settings = data;
        if (settingsWhatsappTemplate) settingsWhatsappTemplate.value = data.whatsapp_template || 'Hola, buen dia.';
        if (linkLocalPc) {
          linkLocalPc.href = data.local_url;
          linkLocalPc.textContent = data.local_url;
        }
        if (linkLanMobile) {
          linkLanMobile.href = data.lan_url;
          linkLanMobile.textContent = data.lan_url;
        }
        if (sidebarLanLabel) {
          sidebarLanLabel.textContent = data.lan_ip;
        }
      }
    } catch (e) {
      console.error('[Settings] Error al cargar configuracion:', e);
    }
  }

  async function loadPipelineBoard() {
    try {
      let url = '/api/v1/pipeline/board';
      if (state.activeCategory) url += `?category_slug=${encodeURIComponent(state.activeCategory)}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        state.board = data.board;
        // Flatten leads for table/stats
        const allLeads = [];
        for (const col of Object.values(data.board)) {
          allLeads.push(...col.leads);
        }
        state.leads = allLeads;
        updatePipelineStats();
        populateLeadSelect(allLeads);
        renderCurrentViewMode();
      }
    } catch (e) {
      console.error('[Board] Error al cargar tablero:', e);
    }
  }

  async function loadTrashCount() {
    try {
      const res = await fetch('/api/v1/leads/trash/list');
      if (res.ok) {
        const trash = await res.json();
        state.trashLeads = trash;
        if (trashCounter) trashCounter.textContent = trash.length;
      }
    } catch (e) {
      console.error('[Trash] Error al consultar papelera:', e);
    }
  }

  async function loadCalendarEvents() {
    try {
      const res = await fetch('/api/v1/calendar/events');
      if (res.ok) {
        const events = await res.json();
        renderCalendarEvents(events);
        const pending = events.filter(e => e.status === 'Pendiente' || e.status === 'PENDIENTE').length;
        if (badgeEventsCount) {
          if (pending > 0) {
            badgeEventsCount.textContent = pending;
            badgeEventsCount.style.display = 'inline-block';
          } else {
            badgeEventsCount.style.display = 'none';
          }
        }
      }
    } catch (e) {
      console.error('[Calendar] Error al cargar agenda:', e);
    }
  }

  async function loadAlerts() {
    try {
      const res = await fetch('/api/v1/calendar/alerts');
      if (res.ok) {
        const alerts = await res.json();
        if (imminentAlertsBanner) {
          if (alerts.imminent_alerts && alerts.imminent_alerts.length > 0) {
            const first = alerts.imminent_alerts[0];
            imminentAlertsBanner.innerHTML = `
              <strong>Alerta de Cita Inminente:</strong> "${escapeHtml(first.title)}" inicia a las ${formatTime(first.start_time)}.
            `;
            imminentAlertsBanner.style.display = 'block';
          } else {
            imminentAlertsBanner.style.display = 'none';
          }
        }
      }
    } catch (e) {
      console.error('[Alerts] Error:', e);
    }
  }

  // ============================================================================
  // 3. Stats & Stage Dropdown Population
  // ============================================================================
  function updatePipelineStats() {
    const total = state.leads.length;
    if (statTotalLeads) statTotalLeads.textContent = total;
    if (badgeLeadsCount) badgeLeadsCount.textContent = total;

    const withWa = state.leads.filter(l => l.has_whatsapp !== false && (l.phone_e164 || l.phone_raw)).length;
    if (statWhatsappLeads) statWhatsappLeads.textContent = withWa;

    const stagnant = state.leads.filter(l => l.is_stagnant).length;
    if (statStagnantLeads) statStagnantLeads.textContent = stagnant;

    const due = state.leads.filter(l => {
      if (!l.postponed_until) return false;
      const dueTime = new Date(l.postponed_until).getTime();
      return dueTime <= Date.now();
    }).length;
    if (statDueLeads) statDueLeads.textContent = due;
  }

  function populateStageDropdowns(stages) {
    if (drawerStageSelect) {
      drawerStageSelect.innerHTML = stages.map(s => `
        <option value="${s.slug}">${s.step}. ${escapeHtml(s.name)}</option>
      `).join('');
    }
  }

  function renderMobileStageTabs(stages) {
    if (!mobileStageTabs) return;
    mobileStageTabs.innerHTML = stages.map(s => {
      const count = (state.board[s.slug] && state.board[s.slug].count) || 0;
      const isActive = s.slug === state.activeMobileStage ? 'active' : '';
      return `
        <button class="stage-tab-pill ${isActive}" data-stage="${s.slug}">
          <span>${s.step}. ${escapeHtml(s.name)}</span>
          <span class="stage-tab-count">${count}</span>
        </button>
      `;
    }).join('');

    mobileStageTabs.querySelectorAll('.stage-tab-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        mobileStageTabs.querySelectorAll('.stage-tab-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.activeMobileStage = btn.dataset.stage;
        renderKanbanBoard();
      });
    });
  }

  // ============================================================================
  // 4. Kanban & Table Rendering
  // ============================================================================
  function renderCurrentViewMode() {
    if (state.leadViewMode === 'kanban') {
      if (kanbanBoardContainer) kanbanBoardContainer.style.display = 'flex';
      if (denseTableContainer) denseTableContainer.style.display = 'none';
      renderKanbanBoard();
    } else if (state.leadViewMode === 'table') {
      if (kanbanBoardContainer) kanbanBoardContainer.style.display = 'none';
      if (denseTableContainer) denseTableContainer.style.display = 'block';
      renderDenseTable(state.leads);
    } else if (state.leadViewMode === 'trash') {
      if (kanbanBoardContainer) kanbanBoardContainer.style.display = 'none';
      if (denseTableContainer) denseTableContainer.style.display = 'block';
      renderTrashTable(state.trashLeads);
    }
  }

  function renderKanbanBoard() {
    if (!kanbanBoardContainer) return;
    kanbanBoardContainer.innerHTML = '';

    const q = state.searchQuery.toLowerCase().trim();

    state.stages.forEach(st => {
      const colData = state.board[st.slug] || { leads: [], count: 0 };
      let colLeads = colData.leads;

      // Filter by search query if any
      if (q) {
        colLeads = colLeads.filter(l => {
          return (l.name || '').toLowerCase().includes(q) ||
                 (l.address_raw || '').toLowerCase().includes(q) ||
                 (l.phone_raw || '').toLowerCase().includes(q);
        });
      }

      const colEl = document.createElement('div');
      colEl.className = 'kanban-column';
      colEl.dataset.stage = st.slug;

      // On mobile, hide columns that do not match active mobile tab
      if (window.innerWidth <= 900 && st.slug !== state.activeMobileStage) {
        colEl.style.display = 'none';
      }

      colEl.innerHTML = `
        <div class="kanban-column-header">
          <span class="kanban-column-title">${st.step}. ${escapeHtml(st.name)}</span>
          <span class="kanban-column-count">${colLeads.length}</span>
        </div>
        <div class="kanban-cards-list" data-stage="${st.slug}">
          <!-- Cards rendered here -->
        </div>
      `;

      const listEl = colEl.querySelector('.kanban-cards-list');

      // Drag over and drop handlers
      listEl.addEventListener('dragover', (e) => {
        e.preventDefault();
        colEl.classList.add('drag-over');
      });
      listEl.addEventListener('dragleave', () => {
        colEl.classList.remove('drag-over');
      });
      listEl.addEventListener('drop', (e) => {
        e.preventDefault();
        colEl.classList.remove('drag-over');
        if (state.draggedLeadId) {
          triggerStageTransition(state.draggedLeadId, st.slug);
        }
      });

      colLeads.forEach(lead => {
        const cardEl = createKanbanCard(lead, st.slug);
        listEl.appendChild(cardEl);
      });

      kanbanBoardContainer.appendChild(colEl);
    });

    // Update counts on mobile tabs
    renderMobileStageTabs(state.stages);
  }

  function createKanbanCard(lead, currentStageSlug) {
    const card = document.createElement('div');
    card.className = 'kanban-card';
    card.draggable = true;
    card.dataset.leadId = lead.id;

    // Drag events
    card.addEventListener('dragstart', (e) => {
      state.draggedLeadId = lead.id;
      card.classList.add('dragging');
      e.dataTransfer.setData('text/plain', lead.id);
    });
    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      state.draggedLeadId = null;
    });

    // Score badge
    const prob = Math.round(lead.acceptance_probability_pct || 0);
    let scoreClass = 'low';
    if (prob >= 70) scoreClass = 'high';
    else if (prob >= 40) scoreClass = 'med';

    // Alerts
    let alertsHtml = '';
    if (lead.is_stagnant) {
      alertsHtml += `
        <div class="stagnant-badge" title="Sin actividad por mas de 48 horas">
          <svg style="width:11px;height:11px;" stroke="currentColor" fill="none"><use href="#icon-clock"/></svg>
          ${lead.stagnant_hours}h sin contacto
        </div>
      `;
    }
    if (lead.postponed_until) {
      const isPast = new Date(lead.postponed_until).getTime() <= Date.now();
      alertsHtml += `
        <div class="${isPast ? 'due-badge' : 'stagnant-badge'}" title="Reactivacion: ${escapeHtml(lead.postponed_until)}">
          <svg style="width:11px;height:11px;" stroke="currentColor" fill="none"><use href="#icon-bell"/></svg>
          ${isPast ? 'Reactivar hoy' : 'En espera'}
        </div>
      `;
    }

    card.innerHTML = `
      <div class="kanban-card-top">
        <div class="kanban-card-name">${escapeHtml(lead.name)}</div>
        <span class="score-badge ${scoreClass}">${prob}%</span>
      </div>

      <div class="kanban-card-meta">
        <span>${escapeHtml(lead.primary_category || lead.category_slug)}</span>
        <span>&bull;</span>
        <span>${escapeHtml(lead.phone_e164 || lead.phone_raw || 'Sin tel')}</span>
      </div>

      ${alertsHtml ? `<div style="display:flex; gap:6px; flex-wrap:wrap;">${alertsHtml}</div>` : ''}

      <div class="kanban-card-actions">
        ${lead.whatsapp_url ? `
          <a href="${escapeHtml(lead.whatsapp_url)}" target="_blank" rel="noopener noreferrer" class="btn-action btn-whatsapp" style="height:26px; padding:0 6px; font-size:11px;" title="Contactar por WhatsApp">
            <svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-message-circle"/></svg>
            WA
          </a>
        ` : ''}

        ${lead.phone_e164 || lead.phone_raw ? `
          <a href="tel:${escapeHtml(lead.phone_e164 || lead.phone_raw)}" class="btn-action" style="height:26px; padding:0 6px; font-size:11px;" title="Llamar">
            <svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-phone"/></svg>
          </a>
        ` : ''}

        <button class="btn-secondary-action btn-open-drawer" style="margin-left: auto; height:26px; font-size:11px;">
          Ficha
        </button>
      </div>
    `;

    // Click card opens drawer (except when clicking buttons/links)
    card.addEventListener('click', (e) => {
      if (e.target.closest('a') || e.target.closest('button.btn-whatsapp')) return;
      openLeadDrawer(lead);
    });

    return card;
  }

  function renderDenseTable(leads) {
    if (!denseTableBody) return;
    denseTableBody.innerHTML = '';

    const q = state.searchQuery.toLowerCase().trim();
    let filtered = leads;
    if (q) {
      filtered = filtered.filter(l => {
        return (l.name || '').toLowerCase().includes(q) ||
               (l.address_raw || '').toLowerCase().includes(q) ||
               (l.phone_raw || '').toLowerCase().includes(q);
      });
    }

    if (filtered.length === 0) {
      denseTableBody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">
            No hay prospectos para mostrar.
          </td>
        </tr>
      `;
      return;
    }

    filtered.forEach(lead => {
      const tr = document.createElement('tr');
      const prob = Math.round(lead.acceptance_probability_pct || 0);

      let stageName = lead.lifecycle_stage;
      const stObj = state.stages.find(s => s.slug === lead.lifecycle_stage);
      if (stObj) stageName = `${stObj.step}. ${stObj.name}`;

      let stagText = '--';
      if (lead.is_stagnant) {
        stagText = `<span class="stagnant-badge">${lead.stagnant_hours}h</span>`;
      } else if (lead.postponed_until) {
        stagText = `<span class="due-badge">Pausado</span>`;
      }

      tr.innerHTML = `
        <td><strong>${escapeHtml(lead.name)}</strong></td>
        <td>${escapeHtml(lead.primary_category || lead.category_slug)}</td>
        <td><span class="score-badge med">${escapeHtml(stageName)}</span></td>
        <td><strong>${prob}%</strong></td>
        <td>${escapeHtml(lead.phone_e164 || lead.phone_raw || 'Sin tel')}</td>
        <td style="font-family: var(--font-mono); font-size: 11px;">
          ${lead.last_activity_at ? new Date(lead.last_activity_at).toLocaleDateString('es-MX') : '--'}
        </td>
        <td>${stagText}</td>
        <td>
          <button class="btn-action btn-table-open" style="height:26px; padding:0 8px; font-size:11px;">
            Ficha
          </button>
        </td>
      `;

      tr.addEventListener('click', () => openLeadDrawer(lead));
      denseTableBody.appendChild(tr);
    });
  }

  function renderTrashTable(trashLeads) {
    if (!denseTableBody) return;
    denseTableBody.innerHTML = '';

    if (trashLeads.length === 0) {
      denseTableBody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">
            La papelera esta vacia.
          </td>
        </tr>
      `;
      return;
    }

    trashLeads.forEach(lead => {
      const tr = document.createElement('tr');
      const delDate = lead.deleted_at ? new Date(lead.deleted_at).toLocaleString('es-MX') : '--';

      tr.innerHTML = `
        <td><strong style="text-decoration: line-through; color: var(--text-muted);">${escapeHtml(lead.name)}</strong></td>
        <td>${escapeHtml(lead.primary_category || lead.category_slug)}</td>
        <td><span class="score-badge low">${escapeHtml(lead.lifecycle_stage)}</span></td>
        <td>--</td>
        <td>${escapeHtml(lead.phone_e164 || lead.phone_raw || 'Sin tel')}</td>
        <td style="font-family: var(--font-mono); font-size: 11px;">${delDate}</td>
        <td><span class="due-badge">En Papelera</span></td>
        <td>
          <div style="display:flex; gap:6px;">
            <button class="btn-action btn-restore-lead" data-id="${lead.id}" style="height:26px; font-size:11px;">
              Restaurar
            </button>
            <button class="btn-secondary-action btn-danger btn-purge-lead" data-id="${lead.id}" style="height:26px; font-size:11px;">
              Purgar
            </button>
          </div>
        </td>
      `;

      const restoreBtn = tr.querySelector('.btn-restore-lead');
      if (restoreBtn) {
        restoreBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          executeRestoreLead(lead.id);
        });
      }

      const purgeBtn = tr.querySelector('.btn-purge-lead');
      if (purgeBtn) {
        purgeBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          promptDoubleConfirmation(
            'Purgar Registro Definitivamente',
            `Se eliminara físicamente el prospecto "${lead.name}" de la base de datos de forma irreversible.`,
            async () => {
              await executePurgeLead(lead.id);
            }
          );
        });
      }

      denseTableBody.appendChild(tr);
    });
  }

  // ============================================================================
  // 5. Drawer (Ficha Integral) Management
  // ============================================================================
  async function openLeadDrawer(lead) {
    state.selectedLead = lead;

    if (drawerLeadName) drawerLeadName.textContent = lead.name;
    if (drawerLeadCategory) drawerLeadCategory.textContent = `${lead.primary_category || lead.category_slug} • Tijuana, BC`;
    if (drawerCurrentStage) drawerCurrentStage.textContent = lead.lifecycle_stage;
    if (drawerProbScore) drawerProbScore.textContent = `${Math.round(lead.acceptance_probability_pct || 0)}%`;
    if (drawerStageSelect) drawerStageSelect.value = lead.lifecycle_stage;

    if (drawerPhone) drawerPhone.textContent = lead.phone_e164 || lead.phone_raw || 'Sin telefono registrado';
    if (drawerWebsite) {
      if (lead.website) {
        drawerWebsite.innerHTML = `<a href="${escapeHtml(lead.website)}" target="_blank" rel="noopener noreferrer" style="color:var(--text-main);">${escapeHtml(lead.website)}</a>`;
      } else {
        drawerWebsite.textContent = 'Sin sitio web';
      }
    }
    if (drawerEmail) drawerEmail.textContent = lead.email || 'Sin correo registrado';
    if (drawerAddress) drawerAddress.textContent = lead.address_raw || 'Tijuana, Baja California';
    if (drawerReviews) drawerReviews.textContent = lead.rating ? `${lead.rating.toFixed(1)} estrellas (${lead.review_count || 0} reseñas)` : 'Sin reseñas';
    if (drawerHealthScore) drawerHealthScore.textContent = `${Math.round(lead.technical_health_score || 0)}/100`;

    // Sales Arguments
    if (drawerSalesArgsList) {
      const args = Array.isArray(lead.sales_arguments) ? lead.sales_arguments : [];
      if (args.length > 0) {
        drawerSalesArgsList.innerHTML = args.map(a => `<li>${escapeHtml(a)}</li>`).join('');
      } else {
        drawerSalesArgsList.innerHTML = '<li>Sin argumentos tecnicos calculados.</li>';
      }
    }

    // Stagnation and Due Alerts
    if (drawerStagnationAlert) {
      drawerStagnationAlert.style.display = lead.is_stagnant ? 'inline-flex' : 'none';
    }
    if (drawerPostponedAlert) {
      drawerPostponedAlert.style.display = lead.postponed_until ? 'inline-flex' : 'none';
    }

    // Populate Universal Action Buttons
    populateDrawerActions(lead);

    // Toggle Delete / Restore / Purge buttons
    const isTrash = state.leadViewMode === 'trash';
    if (drawerBtnDelete) drawerBtnDelete.style.display = isTrash ? 'none' : 'inline-flex';
    if (drawerBtnRestore) drawerBtnRestore.style.display = isTrash ? 'inline-flex' : 'none';
    if (drawerBtnPurge) drawerBtnPurge.style.display = isTrash ? 'inline-flex' : 'none';

    // Load Notes and Timeline
    await Promise.all([
      loadLeadNotes(lead.id),
      loadLeadTimeline(lead.id)
    ]);

    if (drawerLeadDetail) drawerLeadDetail.style.display = 'flex';
  }

  function populateDrawerActions(lead) {
    if (!drawerActionBar) return;
    drawerActionBar.innerHTML = '';

    const cleanPhone = (lead.phone_e164 || lead.phone_raw || '').replace(/[^0-9]/g, '');

    // WhatsApp Action
    if (lead.has_whatsapp !== false && cleanPhone.length >= 10) {
      const template = state.settings.whatsapp_template || 'Hola, buen dia.';
      const msg = template.replace(/{nombre}/g, lead.name);
      const waUrl = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(msg)}`;

      const btnWa = document.createElement('button');
      btnWa.className = 'btn-action btn-whatsapp';
      btnWa.innerHTML = `
        <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-message-circle"/></svg>
        WhatsApp
      `;
      btnWa.addEventListener('click', async () => {
        await logInteraction(lead.id, 'WHATSAPP', 'Apertura de chat wa.me');
        window.open(waUrl, '_blank');
      });
      drawerActionBar.appendChild(btnWa);

      const btnNoWa = document.createElement('button');
      btnNoWa.className = 'btn-secondary-action';
      btnNoWa.textContent = 'Sin WhatsApp';
      btnNoWa.title = 'Marcar como linea fija sin soporte de WhatsApp';
      btnNoWa.addEventListener('click', async () => {
        await fetch(`/api/v1/leads/${lead.id}/mark-no-whatsapp`, { method: 'POST' });
        lead.has_whatsapp = false;
        populateDrawerActions(lead);
        loadPipelineBoard();
      });
      drawerActionBar.appendChild(btnNoWa);
    } else {
      const btnFixed = document.createElement('button');
      btnFixed.className = 'btn-action disabled';
      btnFixed.textContent = 'Solo linea fija';
      drawerActionBar.appendChild(btnFixed);
    }

    // Call Action
    if (cleanPhone.length >= 10) {
      const btnCall = document.createElement('button');
      btnCall.className = 'btn-action';
      btnCall.innerHTML = `
        <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-phone"/></svg>
        Llamar
      `;
      btnCall.addEventListener('click', async () => {
        await logInteraction(lead.id, 'LLAMADA', 'Llamada telefonica iniciada');
        window.location.href = `tel:+${cleanPhone}`;
      });
      drawerActionBar.appendChild(btnCall);
    }

    // Email Action
    if (lead.email) {
      const btnEmail = document.createElement('a');
      btnEmail.className = 'btn-icon-only';
      btnEmail.href = `mailto:${escapeHtml(lead.email)}`;
      btnEmail.title = lead.email;
      btnEmail.innerHTML = `<svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-mail"/></svg>`;
      drawerActionBar.appendChild(btnEmail);
    }

    // Website Action
    if (lead.website) {
      const btnWeb = document.createElement('a');
      btnWeb.className = 'btn-icon-only';
      btnWeb.href = lead.website;
      btnWeb.target = '_blank';
      btnWeb.rel = 'noopener noreferrer';
      btnWeb.title = 'Abrir sitio web';
      btnWeb.innerHTML = `<svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-globe"/></svg>`;
      drawerActionBar.appendChild(btnWeb);
    }
  }

  async function logInteraction(leadId, channel, notes) {
    try {
      await fetch(`/api/v1/leads/${leadId}/interact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: channel,
          interaction_type: 'OUTBOUND',
          notes: notes
        })
      });
      loadLeadTimeline(leadId);
    } catch (e) {
      console.error('[Interact] Error:', e);
    }
  }

  // Drawer Tabs Switch
  document.querySelectorAll('.drawer-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.drawer-tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.drawer-tab-panel').forEach(p => p.style.display = 'none');

      btn.classList.add('active');
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.style.display = 'block';
    });
  });

  if (drawerClose) drawerClose.addEventListener('click', () => drawerLeadDetail.style.display = 'none');

  // Drawer Stage Selector Change
  if (drawerStageSelect) {
    drawerStageSelect.addEventListener('change', (e) => {
      const targetStage = e.target.value;
      if (state.selectedLead && targetStage !== state.selectedLead.lifecycle_stage) {
        triggerStageTransition(state.selectedLead.id, targetStage);
      }
    });
  }

  // ============================================================================
  // 6. Notes & Timeline
  // ============================================================================
  async function loadLeadNotes(leadId) {
    try {
      const res = await fetch(`/api/v1/leads/${leadId}/notes`);
      if (res.ok) {
        const notes = await res.json();
        if (drawerNotesCount) drawerNotesCount.textContent = notes.length;
        if (drawerNotesList) {
          if (notes.length === 0) {
            drawerNotesList.innerHTML = '<div style="color:var(--text-muted); font-size:11px;">Sin notas registradas.</div>';
          } else {
            drawerNotesList.innerHTML = notes.map(n => `
              <div style="background:var(--bg-app); border:1px solid var(--border); border-radius:var(--radius-sm); padding:8px 10px; font-size:12px;">
                <div>${escapeHtml(n.content)}</div>
                <div style="font-size:10px; color:var(--text-muted); font-family:var(--font-mono); margin-top:4px;">
                  ${n.author || 'Usuario'} &bull; ${new Date(n.created_at).toLocaleString('es-MX')}
                </div>
              </div>
            `).join('');
          }
        }
      }
    } catch (e) {
      console.error('[Notes] Error:', e);
    }
  }

  if (formDrawerNote) {
    formDrawerNote.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!state.selectedLead) return;
      const content = drawerNoteContent.value.trim();
      if (!content) return;

      try {
        const res = await fetch(`/api/v1/leads/${state.selectedLead.id}/notes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content })
        });
        if (res.ok) {
          drawerNoteContent.value = '';
          loadLeadNotes(state.selectedLead.id);
          loadLeadTimeline(state.selectedLead.id);
        }
      } catch (err) {
        console.error('[Note] Error al guardar nota:', err);
      }
    });
  }

  async function loadLeadTimeline(leadId) {
    try {
      const res = await fetch(`/api/v1/leads/${leadId}/timeline`);
      if (res.ok) {
        const data = await res.json();
        if (drawerTimelineFeed) {
          if (data.timeline.length === 0) {
            drawerTimelineFeed.innerHTML = '<div style="color:var(--text-muted); font-size:11px;">Sin eventos en el historial.</div>';
          } else {
            drawerTimelineFeed.innerHTML = data.timeline.map(item => {
              const dt = new Date(item.timestamp).toLocaleString('es-MX');
              if (item.type === 'STAGE_CHANGE') {
                const durationMinutes = Math.round((item.duration_seconds || 0) / 60);
                return `
                  <div class="timeline-item">
                    <div class="timeline-header">
                      <span>Fase: ${escapeHtml(item.from_stage || 'INICIAL')} &rarr; ${escapeHtml(item.to_stage)}</span>
                      <span class="timeline-time">${dt}</span>
                    </div>
                    <div style="color:var(--text-secondary);">
                      Permanencia: ${durationMinutes} min. ${item.notes ? `&bull; ${escapeHtml(item.notes)}` : ''}
                      ${item.reason ? `<br><strong>Motivo:</strong> ${escapeHtml(item.reason)}` : ''}
                    </div>
                  </div>
                `;
              } else if (item.type === 'NOTE') {
                return `
                  <div class="timeline-item">
                    <div class="timeline-header">
                      <span>Nota de ${escapeHtml(item.author || 'Usuario')}</span>
                      <span class="timeline-time">${dt}</span>
                    </div>
                    <div style="color:var(--text-main);">${escapeHtml(item.content)}</div>
                  </div>
                `;
              } else {
                return `
                  <div class="timeline-item">
                    <div class="timeline-header">
                      <span>[${escapeHtml(item.channel)}] ${escapeHtml(item.action)}</span>
                      <span class="timeline-time">${dt}</span>
                    </div>
                  </div>
                `;
              }
            }).join('');
          }
        }
      }
    } catch (e) {
      console.error('[Timeline] Error:', e);
    }
  }

  // ============================================================================
  // 7. Stage Transitions & Mandatory Modals
  // ============================================================================
  function triggerStageTransition(leadId, targetStage) {
    state.pendingStageTransition = { leadId, targetStage };

    if (targetStage === 'POSTPONED') {
      openStageActionModal(
        'Postergacion de Prospecto (Obligatorio)',
        'postponed'
      );
    } else if (targetStage === 'REGRETTED') {
      openStageActionModal(
        'Motivo de Retractacion (Obligatorio)',
        'regretted'
      );
    } else if (targetStage === 'CLOSED_LOST') {
      openStageActionModal(
        'Motivo de Descarte (Obligatorio)',
        'lost'
      );
    } else {
      // Execute transition directly
      executeStageTransition({
        stage: targetStage,
        notes: 'Transicion manual en tablero'
      });
    }
  }

  function openStageActionModal(title, mode) {
    if (stageActionTitle) stageActionTitle.textContent = title;
    if (stageActionPostponedFields) stageActionPostponedFields.style.display = mode === 'postponed' ? 'block' : 'none';
    if (stageActionRegrettedFields) stageActionRegrettedFields.style.display = mode === 'regretted' ? 'block' : 'none';
    if (stageActionLostFields) stageActionLostFields.style.display = mode === 'lost' ? 'block' : 'none';

    // Set default postponement time (Tomorrow 10am)
    if (mode === 'postponed' && stagePostponedDate) {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(10, 0, 0, 0);
      stagePostponedDate.value = formatDateTimeLocal(tomorrow);
    }

    if (modalStageAction) modalStageAction.style.display = 'flex';
  }

  if (formStageAction) {
    formStageAction.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!state.pendingStageTransition) return;

      const { targetStage } = state.pendingStageTransition;
      const payload = { stage: targetStage };

      if (targetStage === 'POSTPONED') {
        const d = stagePostponedDate.value;
        const n = stagePostponedNote.value.trim();
        if (!d || !n) {
          alert('Fecha y nota son obligatorias para postergar.');
          return;
        }
        payload.reactivation_date = new Date(d).toISOString();
        payload.notes = n;
      } else if (targetStage === 'REGRETTED') {
        const r = stageRegretReason.value;
        if (!r) {
          alert('Selecciona el motivo de retractacion.');
          return;
        }
        payload.regret_reason = r;
        payload.regret_details = stageRegretDetails.value.trim() || null;
        payload.regret_amount = stageRegretAmount.value ? parseFloat(stageRegretAmount.value) : null;
        payload.regret_service = stageRegretService.value.trim() || null;
        payload.notes = stageGenericNote.value.trim() || null;
      } else if (targetStage === 'CLOSED_LOST') {
        const l = stageLossReason.value;
        if (!l) {
          alert('Selecciona el motivo de descarte.');
          return;
        }
        payload.loss_reason = l;
        payload.notes = stageGenericNote.value.trim() || null;
      } else {
        payload.notes = stageGenericNote.value.trim() || null;
      }

      await executeStageTransition(payload);
      if (modalStageAction) modalStageAction.style.display = 'none';
      formStageAction.reset();
    });
  }

  async function executeStageTransition(payload) {
    if (!state.pendingStageTransition) return;
    const { leadId } = state.pendingStageTransition;

    try {
      const res = await fetch(`/api/v1/leads/${leadId}/stage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        await loadPipelineBoard();
        // If drawer open, refresh it
        if (state.selectedLead && state.selectedLead.id === leadId) {
          state.selectedLead.lifecycle_stage = payload.stage;
          if (drawerCurrentStage) drawerCurrentStage.textContent = payload.stage;
          if (drawerStageSelect) drawerStageSelect.value = payload.stage;
          loadLeadTimeline(leadId);
        }
      } else {
        const err = await res.json();
        alert(`Error al cambiar de fase: ${err.detail || 'Operacion no permitida'}`);
      }
    } catch (e) {
      console.error('[Transition] Error:', e);
    }
  }

  if (modalStageActionClose) modalStageActionClose.addEventListener('click', () => modalStageAction.style.display = 'none');
  if (modalStageActionCancel) modalStageActionCancel.addEventListener('click', () => modalStageAction.style.display = 'none');

  // ============================================================================
  // 8. Double Confirmation Dialog for Destructive Actions
  // ============================================================================
  function promptDoubleConfirmation(title, warningMessage, onConfirmCallback) {
    state.pendingDestructiveAction = onConfirmCallback;

    if (confirmModalTitle) confirmModalTitle.textContent = title;
    if (confirmWarningText) confirmWarningText.textContent = warningMessage;

    if (confirmStep1) confirmStep1.style.display = 'block';
    if (confirmStep2) confirmStep2.style.display = 'none';
    if (modalDoubleConfirm) modalDoubleConfirm.style.display = 'flex';
  }

  if (confirmBtnNext) {
    confirmBtnNext.addEventListener('click', () => {
      if (confirmStep1) confirmStep1.style.display = 'none';
      if (confirmStep2) confirmStep2.style.display = 'block';
    });
  }

  if (confirmBtnCancel1) confirmBtnCancel1.addEventListener('click', () => modalDoubleConfirm.style.display = 'none');
  if (confirmBtnCancel2) confirmBtnCancel2.addEventListener('click', () => modalDoubleConfirm.style.display = 'none');
  if (confirmModalClose) confirmModalClose.addEventListener('click', () => modalDoubleConfirm.style.display = 'none');

  if (confirmBtnExecute) {
    confirmBtnExecute.addEventListener('click', async () => {
      if (state.pendingDestructiveAction) {
        await state.pendingDestructiveAction();
      }
      if (modalDoubleConfirm) modalDoubleConfirm.style.display = 'none';
    });
  }

  // Destructive Actions Handlers
  if (drawerBtnDelete) {
    drawerBtnDelete.addEventListener('click', () => {
      if (!state.selectedLead) return;
      promptDoubleConfirmation(
        'Enviar Prospecto a Papelera',
        `El prospecto "${state.selectedLead.name}" sera movido a la papelera (Soft Delete) y sus datos quedaran blindados para evitar que futuras extracciones lo vuelvan a importar como nuevo.`,
        async () => {
          await executeSoftDeleteLead(state.selectedLead.id);
          drawerLeadDetail.style.display = 'none';
        }
      );
    });
  }

  if (drawerBtnRestore) {
    drawerBtnRestore.addEventListener('click', () => {
      if (!state.selectedLead) return;
      executeRestoreLead(state.selectedLead.id);
      drawerLeadDetail.style.display = 'none';
    });
  }

  if (drawerBtnPurge) {
    drawerBtnPurge.addEventListener('click', () => {
      if (!state.selectedLead) return;
      promptDoubleConfirmation(
        'Purgar Registro Definitivamente',
        `Esta accion borrara fisicamente a "${state.selectedLead.name}" de la base de datos de forma permanente e irreversible.`,
        async () => {
          await executePurgeLead(state.selectedLead.id);
          drawerLeadDetail.style.display = 'none';
        }
      );
    });
  }

  if (drawerBtnResetHistory) {
    drawerBtnResetHistory.addEventListener('click', () => {
      if (!state.selectedLead) return;
      promptDoubleConfirmation(
        'Reiniciar Historial de Actividad',
        `Se borrara todo el registro de llamadas, mensajes de WhatsApp, notas y cambios de fase del prospecto "${state.selectedLead.name}". Su estado se restablecera a "Calificado".`,
        async () => {
          await executeResetHistory(state.selectedLead.id);
        }
      );
    });
  }

  async function executeSoftDeleteLead(leadId) {
    try {
      const res = await fetch(`/api/v1/leads/${leadId}`, { method: 'DELETE' });
      if (res.ok) {
        await Promise.all([loadPipelineBoard(), loadTrashCount()]);
      }
    } catch (e) {
      console.error('[SoftDelete] Error:', e);
    }
  }

  async function executeRestoreLead(leadId) {
    try {
      const res = await fetch(`/api/v1/leads/${leadId}/restore`, { method: 'POST' });
      if (res.ok) {
        await Promise.all([loadPipelineBoard(), loadTrashCount()]);
      }
    } catch (e) {
      console.error('[Restore] Error:', e);
    }
  }

  async function executePurgeLead(leadId) {
    try {
      const res = await fetch(`/api/v1/leads/${leadId}/purge`, { method: 'DELETE' });
      if (res.ok) {
        await Promise.all([loadPipelineBoard(), loadTrashCount()]);
      }
    } catch (e) {
      console.error('[Purge] Error:', e);
    }
  }

  async function executeResetHistory(leadId) {
    try {
      const res = await fetch(`/api/v1/leads/${leadId}/reset-history`, { method: 'POST' });
      if (res.ok) {
        await loadPipelineBoard();
        loadLeadTimeline(leadId);
        loadLeadNotes(leadId);
      }
    } catch (e) {
      console.error('[ResetHistory] Error:', e);
    }
  }

  // ============================================================================
  // 9. Manual Lead Creation & Real-Time Duplicate Prevention
  // ============================================================================
  if (topBtnNewLead) {
    topBtnNewLead.addEventListener('click', () => {
      if (formNewLead) formNewLead.reset();
      if (leadDupAlert) leadDupAlert.style.display = 'none';
      if (modalNewLead) modalNewLead.style.display = 'flex';
    });
  }

  if (modalNewLeadClose) modalNewLeadClose.addEventListener('click', () => modalNewLead.style.display = 'none');
  if (modalNewLeadCancel) modalNewLeadCancel.addEventListener('click', () => modalNewLead.style.display = 'none');

  // Real-time duplicate check debounced
  let dupDebounceTimer = null;
  function triggerDupCheck() {
    clearTimeout(dupDebounceTimer);
    dupDebounceTimer = setTimeout(async () => {
      const name = newLeadName.value.trim();
      const phone = newLeadPhone.value.trim();
      const website = newLeadWebsite.value.trim();

      if (!name && !phone && !website) {
        if (leadDupAlert) leadDupAlert.style.display = 'none';
        return;
      }

      try {
        const res = await fetch('/api/v1/leads/validate-duplicate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: name || null,
            phone_e164: phone || null,
            normalized_domain: website || null
          })
        });
        if (res.ok) {
          const check = await res.json();
          if (check.is_duplicate && leadDupAlert) {
            const ex = check.existing_lead;
            leadDupMsg.innerHTML = `
              Coincidencia encontrada por <strong>${escapeHtml(check.conflict_field)}</strong>: "${escapeHtml(ex.name)}" (Fase: ${ex.lifecycle_stage}${ex.is_deleted ? ', En Papelera' : ''}).
            `;
            leadDupAlert.style.display = 'block';
          } else if (leadDupAlert) {
            leadDupAlert.style.display = 'none';
          }
        }
      } catch (err) {
        console.error('[DupCheck] Error:', err);
      }
    }, 400);
  }

  [newLeadName, newLeadPhone, newLeadWebsite].forEach(input => {
    if (input) input.addEventListener('input', triggerDupCheck);
  });

  if (formNewLead) {
    formNewLead.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = newLeadName.value.trim();
      if (!name) return;

      const payload = {
        name,
        category_slug: newLeadCat.value,
        phone_raw: newLeadPhone.value.trim() || null,
        website: newLeadWebsite.value.trim() || null,
        email: newLeadEmail.value.trim() || null,
        address_raw: newLeadAddress.value.trim() || null,
        notes: newLeadNotes.value.trim() || null
      };

      try {
        const res = await fetch('/api/v1/leads', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          modalNewLead.style.display = 'none';
          formNewLead.reset();
          loadPipelineBoard();
        } else {
          const err = await res.json();
          const detail = err.detail;
          if (detail && detail.conflict) {
            alert(`No se puede guardar: ${detail.message}`);
          } else {
            alert(`Error: ${detail || 'No se pudo registrar prospecto'}`);
          }
        }
      } catch (err) {
        console.error('[CreateLead] Error:', err);
      }
    });
  }

  // ============================================================================
  // 10. View Mode & Navigation Handlers
  // ============================================================================
  function switchView(viewName) {
    state.currentView = viewName;
    if (viewLeads) viewLeads.style.display = viewName === 'leads' ? 'block' : 'none';
    if (viewMap) viewMap.style.display = viewName === 'map' ? 'block' : 'none';
    if (viewCalendar) viewCalendar.style.display = viewName === 'calendar' ? 'flex' : 'none';
    if (viewMetrics) viewMetrics.style.display = viewName === 'metrics' ? 'block' : 'none';
    if (viewSettings) viewSettings.style.display = viewName === 'settings' ? 'block' : 'none';

    [navBtnLeads, navBtnMap, navBtnCalendar, navBtnMetrics, navBtnSettings].forEach(btn => {
      if (btn) btn.classList.toggle('active', btn.dataset.view === viewName);
    });
    [mobNavLeads, mobNavMap, mobNavCalendar, mobNavMetrics, mobNavSettings].forEach(btn => {
      if (btn) btn.classList.toggle('active', btn.dataset.view === viewName);
    });

    if (pageTitle) {
      if (viewName === 'leads') pageTitle.textContent = 'Pipeline Comercial (12 Fases)';
      else if (viewName === 'map') pageTitle.textContent = 'Mapa de Extraccion Geolocalizado (Tijuana, BC)';
      else if (viewName === 'calendar') pageTitle.textContent = 'Agenda de Citas y Seguimientos';
      else if (viewName === 'metrics') pageTitle.textContent = 'Panel de Metricas & Embudo de Conversion';
      else if (viewName === 'settings') pageTitle.textContent = 'Ajustes Modulares del Sistema';
    }

    if (viewName === 'map') {
      setTimeout(() => initTijuanaMap(), 50);
    } else if (viewName === 'calendar') {
      loadCalendarEvents();
      loadAlerts();
    } else if (viewName === 'metrics') {
      loadMetricsDashboard();
    } else if (viewName === 'settings') {
      loadAllSettings();
    }
  }

  [navBtnLeads, mobNavLeads].forEach(el => el && el.addEventListener('click', () => switchView('leads')));
  [navBtnMap, mobNavMap].forEach(el => el && el.addEventListener('click', () => switchView('map')));
  [navBtnCalendar, mobNavCalendar].forEach(el => el && el.addEventListener('click', () => switchView('calendar')));
  [navBtnMetrics, mobNavMetrics].forEach(el => el && el.addEventListener('click', () => switchView('metrics')));
  [navBtnSettings, mobNavSettings].forEach(el => el && el.addEventListener('click', () => switchView('settings')));

  // Toggle Kanban vs Table
  if (btnToggleKanban) {
    btnToggleKanban.addEventListener('click', () => {
      state.leadViewMode = 'kanban';
      btnToggleKanban.classList.add('active');
      if (btnToggleTable) btnToggleTable.classList.remove('active');
      if (btnToggleTrash) btnToggleTrash.classList.remove('active');
      renderCurrentViewMode();
    });
  }

  if (btnToggleTable) {
    btnToggleTable.addEventListener('click', () => {
      state.leadViewMode = 'table';
      btnToggleTable.classList.add('active');
      if (btnToggleKanban) btnToggleKanban.classList.remove('active');
      if (btnToggleTrash) btnToggleTrash.classList.remove('active');
      renderCurrentViewMode();
    });
  }

  if (btnToggleTrash) {
    btnToggleTrash.addEventListener('click', async () => {
      state.leadViewMode = 'trash';
      btnToggleTrash.classList.add('active');
      if (btnToggleKanban) btnToggleKanban.classList.remove('active');
      if (btnToggleTable) btnToggleTable.classList.remove('active');
      await loadTrashCount();
      renderCurrentViewMode();
    });
  }

  // Search input
  if (leadsSearchInput) {
    leadsSearchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value;
      renderCurrentViewMode();
    });
  }

  // Category filter
  if (categoryFilters) {
    categoryFilters.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        categoryFilters.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.activeCategory = btn.dataset.category;
        loadPipelineBoard();
      });
    });
  }

  if (topBtnRefresh) {
    topBtnRefresh.addEventListener('click', () => {
      loadInitialData();
    });
  }

  // ============================================================================
  // 11. Calendar & Settings Utilities
  // ============================================================================
  function renderCalendarEvents(events) {
    if (!calendarEventsList) return;
    calendarEventsList.innerHTML = '';

    if (events.length === 0) {
      if (calendarEmptyState) calendarEmptyState.style.display = 'block';
      return;
    }
    if (calendarEmptyState) calendarEmptyState.style.display = 'none';

    events.forEach(evt => {
      const item = document.createElement('div');
      item.className = 'event-card';

      const startDate = new Date(evt.start_time);
      const dateStr = startDate.toLocaleDateString('es-MX', { weekday: 'short', month: 'short', day: 'numeric' });
      const timeStr = startDate.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });

      item.innerHTML = `
        <div class="event-info">
          <div class="event-title">${escapeHtml(evt.title)}</div>
          <div class="event-meta">
            <span class="score-badge med">${escapeHtml(evt.event_type)}</span>
            <span>&bull;</span>
            <span style="font-family: var(--font-mono);">${dateStr} a las ${timeStr}</span>
            ${evt.lead_name ? `<span>&bull;</span> <strong>${escapeHtml(evt.lead_name)}</strong>` : ''}
          </div>
          ${evt.notes ? `<div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">${escapeHtml(evt.notes)}</div>` : ''}
        </div>

        <div class="event-actions">
          ${(evt.status === 'Pendiente' || evt.status === 'PENDIENTE') ? `
            <button class="btn-action" data-evt-action="complete" data-id="${evt.id}" style="font-size: 11px;">
              <svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-check"/></svg>
              Completar
            </button>
            <button class="btn-secondary-action" data-evt-action="cancel" data-id="${evt.id}">
              Cancelar
            </button>
          ` : `
            <span class="score-badge ${evt.status === 'COMPLETADO' ? 'high' : 'low'}">${escapeHtml(evt.status)}</span>
          `}
        </div>
      `;

      const completeBtn = item.querySelector('[data-evt-action="complete"]');
      if (completeBtn) {
        completeBtn.addEventListener('click', async () => {
          await fetch(`/api/v1/calendar/events/${evt.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'COMPLETADO' })
          });
          loadCalendarEvents();
        });
      }

      const cancelBtn = item.querySelector('[data-evt-action="cancel"]');
      if (cancelBtn) {
        cancelBtn.addEventListener('click', async () => {
          await fetch(`/api/v1/calendar/events/${evt.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'CANCELADO' })
          });
          loadCalendarEvents();
        });
      }

      calendarEventsList.appendChild(item);
    });
  }

  function populateLeadSelect(leads) {
    if (!eventLeadIdSelect) return;
    eventLeadIdSelect.innerHTML = '<option value="">Selecciona un prospecto...</option>';
    leads.forEach(l => {
      const opt = document.createElement('option');
      opt.value = l.id;
      opt.textContent = `${l.name} (${l.phone_e164 || l.phone_raw || 'Sin tel'})`;
      eventLeadIdSelect.appendChild(opt);
    });
  }

  if (topBtnNewEvent) {
    topBtnNewEvent.addEventListener('click', () => {
      const now = new Date();
      now.setHours(now.getHours() + 2, 0, 0, 0);
      const end = new Date(now);
      end.setHours(end.getHours() + 1);

      if (eventStartTimeInput) eventStartTimeInput.value = formatDateTimeLocal(now);
      if (eventEndTimeInput) eventEndTimeInput.value = formatDateTimeLocal(end);
      if (modalEvent) modalEvent.style.display = 'flex';
    });
  }

  if (btnCalendarAddEvent) {
    btnCalendarAddEvent.addEventListener('click', () => {
      if (topBtnNewEvent) topBtnNewEvent.click();
    });
  }

  if (modalEventClose) modalEventClose.addEventListener('click', () => modalEvent.style.display = 'none');
  if (modalEventCancel) modalEventCancel.addEventListener('click', () => modalEvent.style.display = 'none');

  if (formNewEvent) {
    formNewEvent.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const res = await fetch('/api/v1/calendar/events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lead_id: eventLeadIdSelect.value,
            title: document.getElementById('event-title').value.trim(),
            event_type: document.getElementById('event-type').value,
            start_time: new Date(eventStartTimeInput.value).toISOString(),
            end_time: new Date(eventEndTimeInput.value).toISOString(),
            notes: document.getElementById('event-notes').value.trim() || null
          })
        });
        if (res.ok) {
          modalEvent.style.display = 'none';
          formNewEvent.reset();
          loadCalendarEvents();
          loadAlerts();
        }
      } catch (err) {
        console.error('[Calendar] Error al crear evento:', err);
      }
    });
  }

  // ============================================================================
  // 11. FASE 6: MAPA INTERACTIVO & MOTOR DE BARRIDO GEOLOCALIZADO (TIJUANA)
  // ============================================================================
  const mapZoneSelect = document.getElementById('map-zone-select');
  const mapCategorySelect = document.getElementById('map-category-select');
  const mapDepthSelect = document.getElementById('map-depth-select');
  const mapBtnSweepStart = document.getElementById('map-btn-sweep-start');
  const mapBtnSweepPause = document.getElementById('map-btn-sweep-pause');
  const mapBtnSweepResume = document.getElementById('map-btn-sweep-resume');
  const mapBtnSweepCancel = document.getElementById('map-btn-sweep-cancel');
  const telemetryStatus = document.getElementById('telemetry-status');
  const telemetrySource = document.getElementById('telemetry-source');
  const telemetryNewLeads = document.getElementById('telemetry-new-leads');
  const telemetryDups = document.getElementById('telemetry-dups');
  const telemetryProgressBar = document.getElementById('telemetry-progress-bar');
  const telemetryProgressPct = document.getElementById('telemetry-progress-pct');

  function initTijuanaMap() {
    if (typeof L === 'undefined') {
      console.warn('[Map] Leaflet no cargado aun.');
      return;
    }
    const mapEl = document.getElementById('tijuana-map');
    if (!mapEl) return;

    if (!state.mapInstance) {
      // Default view centered on Tijuana
      state.mapInstance = L.map('tijuana-map', {
        zoomControl: true
      }).setView([32.527, -117.022], 13);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
      }).addTo(state.mapInstance);

      state.mapPolygonsLayer = L.layerGroup().addTo(state.mapInstance);
      state.mapMarkersLayer = L.layerGroup().addTo(state.mapInstance);
    } else {
      state.mapInstance.invalidateSize();
    }

    loadMapZones();
    loadMapMarkers();
  }

  async function loadMapZones() {
    try {
      const res = await fetch('/api/v1/geo/zones');
      if (!res.ok) return;
      const data = await res.json();
      if (!state.mapPolygonsLayer) return;
      state.mapPolygonsLayer.clearLayers();

      data.zones.forEach(zone => {
        if (zone.slug === 'tijuana-full') return;
        const bbox = zone.bbox;
        const bounds = [[bbox.min_lat, bbox.min_lon], [bbox.max_lat, bbox.max_lon]];
        const rect = L.rectangle(bounds, {
          color: '#60a5fa',
          weight: 1,
          dashArray: '4, 4',
          fillColor: '#3b82f6',
          fillOpacity: 0.04
        });
        rect.bindTooltip(zone.name, { permanent: false, direction: 'center' });
        state.mapPolygonsLayer.addLayer(rect);
      });
    } catch (e) {
      console.error('[Map] Error al cargar zonas:', e);
    }
  }

  async function loadMapMarkers() {
    try {
      const res = await fetch('/api/v1/geo/leads-markers');
      if (!res.ok) return;
      const data = await res.json();
      if (!state.mapMarkersLayer) return;
      state.mapMarkersLayer.clearLayers();

      data.markers.forEach(lead => {
        if (!lead.lat || !lead.lon) return;

        // Color coding by score
        let color = '#b0bec5';
        if (lead.score >= 70) color = '#81c784';
        else if (lead.score >= 40) color = '#ffb74d';

        const marker = L.circleMarker([lead.lat, lead.lon], {
          radius: 7,
          fillColor: color,
          color: '#1a1a1a',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9
        });

        const popupContent = `
          <div class="map-popup-title">${escapeHtml(lead.name)}</div>
          <div class="map-popup-meta">${escapeHtml(lead.category)} &bull; Fase: ${escapeHtml(lead.stage)}</div>
          <div>Probabilidad de Exito: <span class="map-popup-score">${lead.score}%</span></div>
          ${lead.whatsapp_url ? `<a href="${lead.whatsapp_url}" target="_blank" class="map-popup-btn">Contactar WhatsApp</a>` : ''}
        `;

        marker.bindPopup(popupContent);
        state.mapMarkersLayer.addLayer(marker);
      });
    } catch (e) {
      console.error('[Map] Error al cargar marcadores:', e);
    }
  }

  if (mapZoneSelect) {
    mapZoneSelect.addEventListener('change', async (e) => {
      const slug = e.target.value;
      state.activeMapZone = slug;
      try {
        const res = await fetch('/api/v1/geo/zones');
        if (!res.ok) return;
        const data = await res.json();
        const found = data.zones.find(z => z.slug === slug);
        if (found && state.mapInstance) {
          state.mapInstance.flyTo([found.center.lat, found.center.lon], slug === 'tijuana-full' ? 12 : 14);
        }
      } catch (err) {
        console.error('[Map] Error zona cambio:', err);
      }
    });
  }

  if (mapBtnSweepStart) {
    mapBtnSweepStart.addEventListener('click', async () => {
      const zone = mapZoneSelect ? mapZoneSelect.value : 'zona-rio';
      const category = mapCategorySelect ? mapCategorySelect.value : 'dentistas';
      const depth = mapDepthSelect ? parseInt(mapDepthSelect.value, 10) : 2;

      mapBtnSweepStart.style.display = 'none';
      if (mapBtnSweepPause) mapBtnSweepPause.style.display = 'inline-flex';
      if (mapBtnSweepCancel) mapBtnSweepCancel.style.display = 'inline-flex';

      if (telemetryStatus) {
        telemetryStatus.textContent = 'Ejecutando';
        telemetryStatus.style.color = '#81c784';
      }
      if (telemetrySource) telemetrySource.textContent = 'OpenStreetMap Overpass + Google Maps';

      try {
        const res = await fetch('/api/v1/geo/sweep', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            zone_slug: zone,
            category_slug: category,
            max_depth: depth
          })
        });
        if (res.ok) {
          const data = await res.json();
          state.activeSweepJobId = data.job_id;
          startPollingSweepJob();
        }
      } catch (err) {
        console.error('[Sweep] Error inicio:', err);
      }
    });
  }

  if (mapBtnSweepPause) {
    mapBtnSweepPause.addEventListener('click', () => {
      if (telemetryStatus) {
        telemetryStatus.textContent = 'Pausado';
        telemetryStatus.style.color = '#ffb74d';
      }
      mapBtnSweepPause.style.display = 'none';
      if (mapBtnSweepResume) mapBtnSweepResume.style.display = 'inline-flex';
    });
  }

  if (mapBtnSweepResume) {
    mapBtnSweepResume.addEventListener('click', () => {
      if (telemetryStatus) {
        telemetryStatus.textContent = 'Ejecutando';
        telemetryStatus.style.color = '#81c784';
      }
      mapBtnSweepResume.style.display = 'none';
      if (mapBtnSweepPause) mapBtnSweepPause.style.display = 'inline-flex';
    });
  }

  if (mapBtnSweepCancel) {
    mapBtnSweepCancel.addEventListener('click', () => {
      resetSweepControls();
      if (telemetryStatus) {
        telemetryStatus.textContent = 'Cancelado';
        telemetryStatus.style.color = '#fca5a5';
      }
    });
  }

  function resetSweepControls() {
    if (state.sweepPollInterval) {
      clearInterval(state.sweepPollInterval);
      state.sweepPollInterval = null;
    }
    if (mapBtnSweepStart) mapBtnSweepStart.style.display = 'inline-flex';
    if (mapBtnSweepPause) mapBtnSweepPause.style.display = 'none';
    if (mapBtnSweepResume) mapBtnSweepResume.style.display = 'none';
    if (mapBtnSweepCancel) mapBtnSweepCancel.style.display = 'none';
  }

  function startPollingSweepJob() {
    if (state.sweepPollInterval) clearInterval(state.sweepPollInterval);
    state.sweepPollInterval = setInterval(async () => {
      try {
        const res = await fetch('/api/v1/geo/jobs/active');
        if (!res.ok) return;
        const job = await res.json();

        if (telemetryNewLeads) telemetryNewLeads.textContent = job.new_leads_found || 0;
        if (telemetryDups) telemetryDups.textContent = job.duplicates_filtered || 0;
        if (telemetryProgressBar) telemetryProgressBar.style.width = `${job.progress_pct || 0}%`;
        if (telemetryProgressPct) telemetryProgressPct.textContent = `${job.progress_pct || 0}%`;

        if (job.status === 'COMPLETED' || job.status === 'IDLE' || job.progress_pct >= 100) {
          resetSweepControls();
          if (telemetryStatus) {
            telemetryStatus.textContent = 'Completado';
            telemetryStatus.style.color = '#81c784';
          }
          loadMapMarkers();
          loadPipelineBoard();
        }
      } catch (e) {
        console.error('[Sweep] Error polling:', e);
      }
    }, 1500);
  }

  // ============================================================================
  // 12. FASE 6: PANEL DE METRICAS Y ANALITICA COMERCIAL
  // ============================================================================
  const kpiTotalLeads = document.getElementById('kpi-total-leads');
  const kpiContactedLeads = document.getElementById('kpi-contacted-leads');
  const kpiClosedWon = document.getElementById('kpi-closed-won');
  const kpiClosedLost = document.getElementById('kpi-closed-lost');
  const kpiAvgScore = document.getElementById('kpi-avg-score');
  const funnelContainer = document.getElementById('funnel-container');
  const regretBreakdownList = document.getElementById('regret-breakdown-list');
  const lossBreakdownList = document.getElementById('loss-breakdown-list');
  const categoryMetricsList = document.getElementById('category-metrics-list');
  const zoneMetricsList = document.getElementById('zone-metrics-list');

  async function loadMetricsDashboard() {
    try {
      const res = await fetch('/api/v1/metrics/dashboard');
      if (!res.ok) return;
      const data = await res.json();

      // 1. KPIs
      if (kpiTotalLeads) kpiTotalLeads.textContent = data.kpis.total_leads;
      if (kpiContactedLeads) kpiContactedLeads.textContent = data.kpis.contacted_leads;
      if (kpiClosedWon) kpiClosedWon.textContent = data.kpis.closed_won;
      if (kpiClosedLost) kpiClosedLost.textContent = data.kpis.closed_lost;
      if (kpiAvgScore) kpiAvgScore.textContent = `${data.kpis.overall_avg_score}%`;

      // 2. Conversion Funnel
      if (funnelContainer) {
        funnelContainer.innerHTML = '';
        data.funnel.forEach(step => {
          const row = document.createElement('div');
          let specialClass = '';
          if (step.slug === 'CLOSED_WON') specialClass = 'won';
          if (step.slug === 'CLOSED_LOST' || step.slug === 'REGRETTED') specialClass = 'lost';
          row.className = `funnel-row ${specialClass}`;

          const pct = Math.max(step.pct_of_total, step.count > 0 ? 5 : 0);
          row.innerHTML = `
            <div class="funnel-stage-name" title="${escapeHtml(step.name)}">${step.step}. ${escapeHtml(step.name)}</div>
            <div class="funnel-bar-wrapper">
              <div class="funnel-bar-fill" style="width: ${pct}%;"></div>
              <div class="funnel-bar-meta">${step.count} (${step.pct_of_total}%)</div>
            </div>
          `;
          funnelContainer.appendChild(row);
        });
      }

      // 3. Regret & Loss Breakdown
      if (regretBreakdownList) {
        if (!data.regret_breakdown || data.regret_breakdown.length === 0) {
          regretBreakdownList.innerHTML = '<div class="empty-state-sm">Sin casos de retractacion registrados.</div>';
        } else {
          regretBreakdownList.innerHTML = data.regret_breakdown.map(r => `
            <div class="objection-item">
              <span>${escapeHtml(r.reason)}</span>
              <strong style="font-family: var(--font-mono);">${r.count}</strong>
            </div>
          `).join('');
        }
      }

      if (lossBreakdownList) {
        if (!data.loss_breakdown || data.loss_breakdown.length === 0) {
          lossBreakdownList.innerHTML = '<div class="empty-state-sm">Sin descartes comerciales registrados.</div>';
        } else {
          lossBreakdownList.innerHTML = data.loss_breakdown.map(l => `
            <div class="objection-item">
              <span>${escapeHtml(l.reason)}</span>
              <strong style="font-family: var(--font-mono);">${l.count}</strong>
            </div>
          `).join('');
        }
      }

      // 4. Category Distribution
      if (categoryMetricsList) {
        categoryMetricsList.innerHTML = data.category_distribution.map(c => `
          <div class="distribution-item">
            <div>
              <strong style="color: var(--text-main);">${escapeHtml(c.category_slug)}</strong>
              <div style="font-size: 10px; color: var(--text-muted);">Score promedio: ${c.avg_score}%</div>
            </div>
            <div style="font-family: var(--font-mono); font-weight: 700;">${c.count} prospectos</div>
          </div>
        `).join('');
      }

      // 5. Zone Distribution
      if (zoneMetricsList) {
        zoneMetricsList.innerHTML = data.zone_distribution.map(z => `
          <div class="distribution-item">
            <span style="color: var(--text-main); font-weight: 500;">${escapeHtml(z.zone)}</span>
            <span style="font-family: var(--font-mono); font-weight: 600;">${z.count}</span>
          </div>
        `).join('');
      }
    } catch (e) {
      console.error('[Metrics] Error al cargar metricas:', e);
    }
  }

  // ============================================================================
  // 13. FASE 6: PANEL DE AJUSTES MODULAR AVANZADO (8 MODULOS)
  // ============================================================================
  const settingsNavBtns = document.querySelectorAll('.settings-nav-btn');
  const settingsModPanels = document.querySelectorAll('.settings-mod-panel');

  settingsNavBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetMod = btn.dataset.mod;
      settingsNavBtns.forEach(b => b.classList.toggle('active', b === btn));
      settingsModPanels.forEach(p => {
        p.style.display = p.id === targetMod ? 'block' : 'none';
      });
    });
  });

  async function loadAllSettings() {
    try {
      const res = await fetch('/api/v1/settings/all');
      if (!res.ok) return;
      const data = await res.json();

      // 3.1 Operator
      const op = data.operator || {};
      const elOpName = document.getElementById('settings-op-name');
      const elOpLada = document.getElementById('settings-op-lada');
      const elOpPhone = document.getElementById('settings-op-phone');
      const elOpEmail = document.getElementById('settings-op-email');
      if (elOpName) elOpName.value = op.commercial_name || '';
      if (elOpLada) elOpLada.value = op.default_country_code || '+52';
      if (elOpPhone) elOpPhone.value = op.whatsapp_number || '';
      if (elOpEmail) elOpEmail.value = op.response_email || '';

      // 3.2 Categories & Negative Keywords
      const elNeg = document.getElementById('settings-negative-keywords');
      const catListEl = document.getElementById('settings-categories-list');
      if (elNeg) {
        elNeg.value = (data.scraper.negative_keywords || []).join(', ');
      }
      if (catListEl) {
        catListEl.innerHTML = `
          <div style="background: var(--bg-app); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 10px; font-size: 11px;">
            <strong>Dentistas / Clinicas Dentales</strong>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">OSM: amenity=dentist, healthcare=dentist &bull; Slug: dentistas</div>
          </div>
          <div style="background: var(--bg-app); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 10px; font-size: 11px;">
            <strong>Despachos Contables / Fiscales</strong>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">OSM: office=accountant, office=tax_advisor &bull; Slug: despachos-contables</div>
          </div>
        `;
      }

      // 3.3 Scraper
      const sc = data.scraper || {};
      const elConc = document.getElementById('settings-scraper-concurrency');
      const elDepth = document.getElementById('settings-scraper-depth');
      const elJitMin = document.getElementById('settings-jitter-min');
      const elJitMax = document.getElementById('settings-jitter-max');
      const elMirror = document.getElementById('settings-overpass-mirror');
      if (elConc) elConc.value = sc.concurrency_workers || 2;
      if (elDepth) elDepth.value = sc.max_quadtree_depth || 3;
      if (elJitMin) elJitMin.value = sc.jitter_min_ms || 1500;
      if (elJitMax) elJitMax.value = sc.jitter_max_ms || 4500;
      if (elMirror && sc.overpass_mirror_url) elMirror.value = sc.overpass_mirror_url;

      // 3.4 Scoring
      const sco = data.scoring || {};
      const elSsl = document.getElementById('weight-ssl');
      const elMob = document.getElementById('weight-mobile');
      const elPerf = document.getElementById('weight-performance');
      const elPix = document.getElementById('weight-pixels');
      const elRev = document.getElementById('weight-reviews');
      if (elSsl) elSsl.value = sco.weight_ssl ?? 25;
      if (elMob) elMob.value = sco.weight_mobile ?? 25;
      if (elPerf) elPerf.value = sco.weight_performance ?? 20;
      if (elPix) elPix.value = sco.weight_pixels ?? 15;
      if (elRev) elRev.value = sco.weight_reviews ?? 15;

      // 3.5 Templates
      const tmpl = data.templates || {};
      const elWaTmpl = document.getElementById('settings-whatsapp-template');
      if (elWaTmpl && tmpl.whatsapp_template) elWaTmpl.value = tmpl.whatsapp_template;

      // 3.6 Pipeline Rules
      const pipe = data.pipeline || {};
      const elStag = document.getElementById('settings-stagnation-hours');
      const elAlert = document.getElementById('settings-alert-lead-hours');
      if (elStag) elStag.value = pipe.stagnation_threshold_hours || 48;
      if (elAlert) elAlert.value = pipe.alert_lead_hours || 24;

      // 3.7 Calendar
      const cal = data.calendar || {};
      const elCalView = document.getElementById('settings-calendar-view');
      const elCalDur = document.getElementById('settings-event-duration');
      const elOauthId = document.getElementById('oauth-client-id');
      if (elCalView) elCalView.value = cal.default_view || 'agenda';
      if (elCalDur) elCalDur.value = cal.standard_meeting_duration_minutes || 45;
      if (elOauthId && cal.google_client_id) elOauthId.value = cal.google_client_id;

      // 3.8 Security & Protection Status
      const sec = data.security || {};
      const btnProt = document.getElementById('btn-toggle-protection');
      if (btnProt) {
        btnProt.textContent = sec.protection_enabled ? 'Deshabilitar Bloqueo' : 'Habilitar Bloqueo';
        btnProt.classList.toggle('btn-danger', sec.protection_enabled);
      }
    } catch (e) {
      console.error('[SettingsAll] Error al cargar:', e);
    }
  }

  // Save 3.1 Operator
  const btnSaveOperator = document.getElementById('btn-save-operator');
  if (btnSaveOperator) {
    btnSaveOperator.addEventListener('click', async () => {
      const payload = {
        commercial_name: document.getElementById('settings-op-name')?.value || '',
        default_country_code: document.getElementById('settings-op-lada')?.value || '+52',
        whatsapp_number: document.getElementById('settings-op-phone')?.value || '',
        response_email: document.getElementById('settings-op-email')?.value || ''
      };
      try {
        btnSaveOperator.textContent = 'Guardando...';
        const res = await fetch('/api/v1/settings/operator', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          btnSaveOperator.textContent = 'Guardado';
          setTimeout(() => btnSaveOperator.textContent = 'Guardar Datos de Operador', 1500);
        }
      } catch (e) {
        btnSaveOperator.textContent = 'Error';
      }
    });
  }

  // Save 3.2 Categories & Negative Keywords
  const btnSaveCategoriesSettings = document.getElementById('btn-save-categories-settings');
  if (btnSaveCategoriesSettings) {
    btnSaveCategoriesSettings.addEventListener('click', async () => {
      const raw = document.getElementById('settings-negative-keywords')?.value || '';
      const keywords = raw.split(',').map(k => k.trim()).filter(Boolean);
      try {
        btnSaveCategoriesSettings.textContent = 'Guardando...';
        const res = await fetch('/api/v1/settings/scraper', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ negative_keywords: keywords })
        });
        if (res.ok) {
          btnSaveCategoriesSettings.textContent = 'Guardado';
          setTimeout(() => btnSaveCategoriesSettings.textContent = 'Guardar Palabras Clave', 1500);
        }
      } catch (e) {
        btnSaveCategoriesSettings.textContent = 'Error';
      }
    });
  }

  // Save 3.3 Scraper
  const btnSaveScraper = document.getElementById('btn-save-scraper');
  if (btnSaveScraper) {
    btnSaveScraper.addEventListener('click', async () => {
      const payload = {
        concurrency_workers: parseInt(document.getElementById('settings-scraper-concurrency')?.value || 2, 10),
        max_quadtree_depth: parseInt(document.getElementById('settings-scraper-depth')?.value || 3, 10),
        jitter_min_ms: parseInt(document.getElementById('settings-jitter-min')?.value || 1500, 10),
        jitter_max_ms: parseInt(document.getElementById('settings-jitter-max')?.value || 4500, 10),
        overpass_mirror_url: document.getElementById('settings-overpass-mirror')?.value || ''
      };
      try {
        btnSaveScraper.textContent = 'Guardando...';
        const res = await fetch('/api/v1/settings/scraper', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          btnSaveScraper.textContent = 'Guardado';
          setTimeout(() => btnSaveScraper.textContent = 'Guardar Ajustes de Extraccion', 1500);
        }
      } catch (e) {
        btnSaveScraper.textContent = 'Error';
      }
    });
  }

  // Save 3.4 Scoring
  const btnSaveScoring = document.getElementById('btn-save-scoring');
  if (btnSaveScoring) {
    btnSaveScoring.addEventListener('click', async () => {
      const payload = {
        weight_ssl: parseFloat(document.getElementById('weight-ssl')?.value || 25),
        weight_mobile: parseFloat(document.getElementById('weight-mobile')?.value || 25),
        weight_performance: parseFloat(document.getElementById('weight-performance')?.value || 20),
        weight_pixels: parseFloat(document.getElementById('weight-pixels')?.value || 15),
        weight_reviews: parseFloat(document.getElementById('weight-reviews')?.value || 15)
      };
      try {
        btnSaveScoring.textContent = 'Guardando...';
        const res = await fetch('/api/v1/settings/scoring', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          btnSaveScoring.textContent = 'Guardado';
          setTimeout(() => btnSaveScoring.textContent = 'Guardar Ponderaciones', 1500);
        }
      } catch (e) {
        btnSaveScoring.textContent = 'Error';
      }
    });
  }

  // Recalibrate All Scores Massively
  const btnRecalibrateAllScores = document.getElementById('btn-recalibrate-all-scores');
  if (btnRecalibrateAllScores) {
    btnRecalibrateAllScores.addEventListener('click', async () => {
      if (!confirm('¿Deseas recalcular la probabilidad de exito de todos los prospectos en base a las ponderaciones actuales?')) {
        return;
      }
      try {
        btnRecalibrateAllScores.textContent = 'Recalculando...';
        const res = await fetch('/api/v1/settings/recalibrate-scores', { method: 'POST' });
        if (res.ok) {
          const data = await res.json();
          btnRecalibrateAllScores.textContent = `Actualizados: ${data.recalculated_leads}`;
          setTimeout(() => btnRecalibrateAllScores.textContent = 'Recalcular Masivamente', 2000);
          loadPipelineBoard();
        }
      } catch (e) {
        btnRecalibrateAllScores.textContent = 'Error';
      }
    });
  }

  // Save 3.5 Templates
  const btnSaveTemplates = document.getElementById('btn-save-templates');
  if (btnSaveTemplates) {
    btnSaveTemplates.addEventListener('click', async () => {
      const payload = {
        whatsapp_template: document.getElementById('settings-whatsapp-template')?.value || 'Hola, buen dia.',
        visible_channels: {
          whatsapp: document.getElementById('channel-toggle-wa')?.checked ?? true,
          phone: document.getElementById('channel-toggle-tel')?.checked ?? true,
          email: document.getElementById('channel-toggle-mail')?.checked ?? true,
          social: document.getElementById('channel-toggle-social')?.checked ?? true
        }
      };
      try {
        btnSaveTemplates.textContent = 'Guardando...';
        const res = await fetch('/api/v1/settings/templates', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          btnSaveTemplates.textContent = 'Guardado';
          setTimeout(() => btnSaveTemplates.textContent = 'Guardar Plantillas y Canales', 1500);
          loadPipelineBoard();
        }
      } catch (e) {
        btnSaveTemplates.textContent = 'Error';
      }
    });
  }

  // Save 3.6 Pipeline Rules
  const btnSavePipelineRules = document.getElementById('btn-save-pipeline-rules');
  if (btnSavePipelineRules) {
    btnSavePipelineRules.addEventListener('click', async () => {
      const payload = {
        stagnation_threshold_hours: parseInt(document.getElementById('settings-stagnation-hours')?.value || 48, 10),
        alert_lead_hours: parseInt(document.getElementById('settings-alert-lead-hours')?.value || 24, 10)
      };
      try {
        btnSavePipelineRules.textContent = 'Guardando...';
        const res = await fetch('/api/v1/settings/pipeline', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          btnSavePipelineRules.textContent = 'Guardado';
          setTimeout(() => btnSavePipelineRules.textContent = 'Guardar Reglas', 1500);
        }
      } catch (e) {
        btnSavePipelineRules.textContent = 'Error';
      }
    });
  }

  // 3.8 Security: Set PIN
  const btnSetPin = document.getElementById('btn-set-pin');
  if (btnSetPin) {
    btnSetPin.addEventListener('click', async () => {
      const pin = document.getElementById('settings-new-pin')?.value.trim();
      if (!pin || pin.length < 4) {
        alert('El PIN debe tener al menos 4 caracteres.');
        return;
      }
      try {
        btnSetPin.textContent = 'Cifrando...';
        const res = await fetch('/api/v1/security/set-pin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pin })
        });
        if (res.ok) {
          btnSetPin.textContent = 'PIN Configurado';
          document.getElementById('settings-new-pin').value = '';
          setTimeout(() => btnSetPin.textContent = 'Establecer PIN', 1500);
        }
      } catch (e) {
        btnSetPin.textContent = 'Error';
      }
    });
  }

  // 3.8 Security: Toggle LAN Protection
  const btnToggleProtection = document.getElementById('btn-toggle-protection');
  if (btnToggleProtection) {
    btnToggleProtection.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/v1/security/toggle-protection', { method: 'POST' });
        if (res.ok) {
          const data = await res.json();
          btnToggleProtection.textContent = data.protection_enabled ? 'Deshabilitar Bloqueo' : 'Habilitar Bloqueo';
          btnToggleProtection.classList.toggle('btn-danger', data.protection_enabled);
        }
      } catch (e) {
        console.error('[Security] Error toggle:', e);
      }
    });
  }

  // 3.8 Backups: Export JSON
  const btnExportJson = document.getElementById('btn-export-json');
  if (btnExportJson) {
    btnExportJson.addEventListener('click', () => {
      window.open('/api/v1/maintenance/export?format=json', '_blank');
    });
  }

  // 3.8 Backups: Export CSV
  const btnExportCsv = document.getElementById('btn-export-csv');
  if (btnExportCsv) {
    btnExportCsv.addEventListener('click', () => {
      window.open('/api/v1/maintenance/export?format=csv', '_blank');
    });
  }

  // 3.8 Backups: Import
  const inputImportBackup = document.getElementById('input-import-backup');
  if (inputImportBackup) {
    inputImportBackup.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetch('/api/v1/maintenance/import', {
          method: 'POST',
          body: formData
        });
        if (res.ok) {
          alert('Copia de seguridad restaurada correctamente.');
          loadPipelineBoard();
        } else {
          alert('Error al procesar el archivo de respaldo.');
        }
      } catch (err) {
        alert('Error de conexion al restaurar respaldo.');
      }
    });
  }

  // 3.8 Maintenance: Purge Trash
  const btnPurgeTrashAll = document.getElementById('btn-purge-trash-all');
  if (btnPurgeTrashAll) {
    btnPurgeTrashAll.addEventListener('click', () => {
      openDoubleConfirm(
        'Vaciar Papelera Definitivamente',
        '¿Deseas purgar de forma permanente todos los prospectos descartados en la papelera? Esta accion no se puede deshacer.',
        async () => {
          try {
            await fetch('/api/v1/leads/trash/empty', { method: 'POST' });
            await loadTrashCount();
            renderCurrentViewMode();
          } catch (e) {
            console.error('[PurgeTrash] Error:', e);
          }
        }
      );
    });
  }

  // 3.8 Maintenance: Factory Reset
  const btnFactoryReset = document.getElementById('btn-factory-reset');
  if (btnFactoryReset) {
    btnFactoryReset.addEventListener('click', () => {
      openDoubleConfirm(
        'Reinicio de Fabrica (Factory Reset)',
        'ATENCION CRITICA: Esta accion borrara todas las citas, notas, historial y prospectos de la base de datos de Tijuana y restablecera los ajustes iniciales.',
        async () => {
          try {
            const res = await fetch('/api/v1/maintenance/factory-reset', { method: 'POST' });
            if (res.ok) {
              alert('Sistema restablecido a valores de fabrica.');
              window.location.reload();
            }
          } catch (e) {
            alert('Error al ejecutar reinicio de fabrica.');
          }
        }
      );
    });
  }

  // ============================================================================
  // 14. FASE 6: SPOTLIGHT ONBOARDING OVERLAY (PRIMEROS PASOS)
  // ============================================================================
  const spotlightOverlay = document.getElementById('spotlight-overlay');
  const spotlightCard = document.getElementById('spotlight-card');
  const spotlightStepBadge = document.getElementById('spotlight-step-badge');
  const spotlightTitle = document.getElementById('spotlight-title');
  const spotlightText = document.getElementById('spotlight-text');
  const spotlightBtnSkip = document.getElementById('spotlight-btn-skip');
  const spotlightBtnPrev = document.getElementById('spotlight-btn-prev');
  const spotlightBtnNext = document.getElementById('spotlight-btn-next');

  const ONBOARDING_STEPS = [
    {
      targetId: 'nav-btn-leads',
      title: 'Pipeline Comercial de 12 Fases',
      text: 'Supervisa todo el ciclo de captacion, desde la extraccion inicial hasta el cierre comercial con clasificacion en tiempo real.'
    },
    {
      targetId: 'nav-btn-map',
      title: 'Mapa Interactivo de Tijuana',
      text: 'Explora la cobertura geoespacial por delegaciones (Zona Rio, Centro, Otay) y activa barridos de escaneo hibrido en vivo.'
    },
    {
      targetId: 'top-btn-new-lead',
      title: 'Registro de Prospectos & Deduplicacion',
      text: 'Ingresa prospectos manuales con deteccion instantanea de duplicados por telefono E.164, dominio normalizado y ubicacion.'
    },
    {
      targetId: 'nav-btn-calendar',
      title: 'Agenda Comercial & Citas',
      text: 'Programa llamadas y reuniones con calculo de anticipacion y recordatorios visuales 100% locales sin depender de la nube.'
    },
    {
      targetId: 'nav-btn-metrics',
      title: 'Embudo y Analitica Comercial',
      text: 'Mide la conversion entre cada etapa comercial, analiza las objeciones mas frecuentes y evalua el promedio de exito.'
    },
    {
      targetId: 'nav-btn-settings',
      title: 'Ajustes Modulares & Seguridad Argon2id',
      text: 'Personaliza los 8 modulos de operacion, calibra los pesos predictivos de auditoria y protege el acceso en tu red local.'
    }
  ];

  function startSpotlightTour() {
    state.onboardingStep = 1;
    if (spotlightOverlay) spotlightOverlay.style.display = 'block';
    renderSpotlightStep();
  }

  function renderSpotlightStep() {
    const stepData = ONBOARDING_STEPS[state.onboardingStep - 1];
    if (!stepData) return;

    // Remove previous highlights
    document.querySelectorAll('.spotlight-target-highlight').forEach(el => {
      el.classList.remove('spotlight-target-highlight');
    });

    const targetEl = document.getElementById(stepData.targetId);
    if (targetEl) {
      targetEl.classList.add('spotlight-target-highlight');
      const rect = targetEl.getBoundingClientRect();

      if (spotlightCard) {
        if (window.innerWidth > 768) {
          // Desktop positioning
          let top = rect.top;
          let left = rect.right + 20;
          if (left + 360 > window.innerWidth) {
            left = rect.left;
            top = rect.bottom + 16;
          }
          spotlightCard.style.top = `${Math.max(20, top)}px`;
          spotlightCard.style.left = `${Math.max(20, left)}px`;
        }
      }
    }

    if (spotlightStepBadge) spotlightStepBadge.textContent = `Paso ${state.onboardingStep} de ${ONBOARDING_STEPS.length}`;
    if (spotlightTitle) spotlightTitle.textContent = stepData.title;
    if (spotlightText) spotlightText.textContent = stepData.text;

    if (spotlightBtnPrev) spotlightBtnPrev.style.display = state.onboardingStep > 1 ? 'inline-flex' : 'none';
    if (spotlightBtnNext) spotlightBtnNext.textContent = state.onboardingStep === ONBOARDING_STEPS.length ? 'Finalizar' : 'Siguiente';
  }

  function nextSpotlightStep() {
    if (state.onboardingStep < ONBOARDING_STEPS.length) {
      state.onboardingStep++;
      renderSpotlightStep();
    } else {
      finishSpotlightTour();
    }
  }

  function prevSpotlightStep() {
    if (state.onboardingStep > 1) {
      state.onboardingStep--;
      renderSpotlightStep();
    }
  }

  function finishSpotlightTour() {
    document.querySelectorAll('.spotlight-target-highlight').forEach(el => {
      el.classList.remove('spotlight-target-highlight');
    });
    if (spotlightOverlay) spotlightOverlay.style.display = 'none';
    localStorage.setItem('crm_onboarded', 'true');
    fetch('/api/v1/onboarding/complete', { method: 'POST' }).catch(() => {});
  }

  if (spotlightBtnNext) spotlightBtnNext.addEventListener('click', nextSpotlightStep);
  if (spotlightBtnPrev) spotlightBtnPrev.addEventListener('click', prevSpotlightStep);
  if (spotlightBtnSkip) spotlightBtnSkip.addEventListener('click', finishSpotlightTour);
  if (btnStartOnboarding) btnStartOnboarding.addEventListener('click', startSpotlightTour);

  async function checkOnboardingInitial() {
    if (localStorage.getItem('crm_onboarded') === 'true') return;
    try {
      const res = await fetch('/api/v1/onboarding/status');
      if (res.ok) {
        const data = await res.json();
        if (!data.completed) {
          setTimeout(() => startSpotlightTour(), 600);
        }
      }
    } catch (e) {}
  }

  // ============================================================================
  // 15. FASE 6: PANTALLA DE BLOQUEO POR PIN (ARGON2ID LOCAL PROTECTION)
  // ============================================================================
  const pinLockOverlay = document.getElementById('pin-lock-overlay');
  const formPinUnlock = document.getElementById('form-pin-unlock');
  const inputUnlockPin = document.getElementById('input-unlock-pin');
  const pinErrorMsg = document.getElementById('pin-error-msg');

  async function checkSecurityLock() {
    try {
      const res = await fetch('/api/v1/security/status');
      if (!res.ok) return;
      const data = await res.json();
      if (data.protection_enabled && sessionStorage.getItem('crm_pin_unlocked') !== 'true') {
        if (pinLockOverlay) pinLockOverlay.style.display = 'flex';
        if (inputUnlockPin) inputUnlockPin.focus();
      }
    } catch (e) {
      console.error('[Security] Error check:', e);
    }
  }

  if (formPinUnlock) {
    formPinUnlock.addEventListener('submit', async (e) => {
      e.preventDefault();
      const pin = inputUnlockPin?.value.trim();
      if (!pin) return;

      try {
        const res = await fetch('/api/v1/security/verify-pin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pin })
        });
        const data = await res.json();
        if (data.valid) {
          sessionStorage.setItem('crm_pin_unlocked', 'true');
          if (pinLockOverlay) pinLockOverlay.style.display = 'none';
          if (pinErrorMsg) pinErrorMsg.style.display = 'none';
        } else {
          if (pinErrorMsg) pinErrorMsg.style.display = 'block';
          if (inputUnlockPin) {
            inputUnlockPin.value = '';
            inputUnlockPin.focus();
          }
        }
      } catch (err) {
        if (pinErrorMsg) {
          pinErrorMsg.textContent = 'Error de verificacion';
          pinErrorMsg.style.display = 'block';
        }
      }
    });
  }

  if (btnCopyLanUrl) {
    btnCopyLanUrl.addEventListener('click', () => {
      if (state.settings.lan_url) {
        navigator.clipboard.writeText(state.settings.lan_url).then(() => {
          btnCopyLanUrl.innerHTML = '<svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-check"/></svg>';
          setTimeout(() => {
            btnCopyLanUrl.innerHTML = '<svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-copy"/></svg>';
          }, 1500);
        });
      }
    });
  }

  if (btnRequestNotifications) {
    btnRequestNotifications.addEventListener('click', async () => {
      if ('Notification' in window) {
        const p = await Notification.requestPermission();
        if (p === 'granted') {
          btnRequestNotifications.textContent = 'Alertas Habilitadas';
          btnRequestNotifications.classList.add('disabled');
        }
      }
    });
  }

  // ============================================================================
  // 12. Helpers
  // ============================================================================
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatTime(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    return d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
  }

  function formatDateTimeLocal(date) {
    const pad = (n) => String(n).padStart(2, '0');
    const y = date.getFullYear();
    const m = pad(date.getMonth() + 1);
    const d = pad(date.getDate());
    const h = pad(date.getHours());
    const min = pad(date.getMinutes());
    return `${y}-${m}-${d}T${h}:${min}`;
  }

  // Start initial loads
  initLiveReload();
  loadInitialData();
  checkSecurityLock();
  checkOnboardingInitial();
});
