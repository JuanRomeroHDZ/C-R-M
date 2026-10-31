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
    selectedLeadIds: new Set(),
    suspectedPairs: [],
    leadFlags: {},
    activeSuspectedPair: null,
    quickFilter: null,
    recentSearches: [],
    activePreviewLead: null,
    waAngleLead: null,
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
      loadAlerts(),
      loadSuspectedDuplicates(),
      loadRecentSearches(),
      loadTodayTrayCount()
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
      const params = new URLSearchParams();
      if (state.activeCategory) params.append('category_slug', state.activeCategory);
      if (state.onlyOpenNow) params.append('only_open_now', 'true');
      if (state.tagFilter) params.append('tag', state.tagFilter);
      const url = `/api/v1/pipeline/board${params.toString() ? '?' + params.toString() : ''}`;
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
    const focusModeContainer = document.getElementById('focus-mode-container');

    if (leadsEmptyState) {
      if (state.leadViewMode !== 'trash' && state.leads.length === 0) {
        leadsEmptyState.style.display = 'block';
        if (kanbanBoardContainer) kanbanBoardContainer.style.display = 'none';
        if (denseTableContainer) denseTableContainer.style.display = 'none';
        if (focusModeContainer) focusModeContainer.style.display = 'none';
        return;
      } else if (state.leadViewMode === 'trash' && state.trashLeads.length === 0) {
        leadsEmptyState.style.display = 'block';
        if (kanbanBoardContainer) kanbanBoardContainer.style.display = 'none';
        if (denseTableContainer) denseTableContainer.style.display = 'none';
        if (focusModeContainer) focusModeContainer.style.display = 'none';
        return;
      } else {
        leadsEmptyState.style.display = 'none';
      }
    }

    if (state.leadViewMode === 'kanban') {
      if (kanbanBoardContainer) kanbanBoardContainer.style.display = 'flex';
      if (denseTableContainer) denseTableContainer.style.display = 'none';
      if (focusModeContainer) focusModeContainer.style.display = 'none';
      renderKanbanBoard();
    } else if (state.leadViewMode === 'table') {
      if (kanbanBoardContainer) kanbanBoardContainer.style.display = 'none';
      if (denseTableContainer) denseTableContainer.style.display = 'block';
      if (focusModeContainer) focusModeContainer.style.display = 'none';
      renderDenseTable(state.leads);
    } else if (state.leadViewMode === 'trash') {
      if (kanbanBoardContainer) kanbanBoardContainer.style.display = 'none';
      if (denseTableContainer) denseTableContainer.style.display = 'block';
      if (focusModeContainer) focusModeContainer.style.display = 'none';
      renderTrashTable(state.trashLeads);
    } else if (state.leadViewMode === 'focus') {
      if (kanbanBoardContainer) kanbanBoardContainer.style.display = 'none';
      if (denseTableContainer) denseTableContainer.style.display = 'none';
      if (focusModeContainer) focusModeContainer.style.display = 'flex';
      renderFocusMode();
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

      // Filter by quick filter if any (Creative Freedom #3)
      if (state.quickFilter === 'whatsapp') {
        colLeads = colLeads.filter(l => l.has_whatsapp !== false && (l.phone_e164 || l.phone_raw));
      } else if (state.quickFilter === 'phone') {
        colLeads = colLeads.filter(l => Boolean(l.phone_e164 || l.phone_raw));
      } else if (state.quickFilter === 'website') {
        colLeads = colLeads.filter(l => Boolean(l.website));
      } else if (state.quickFilter === 'duplicates') {
        colLeads = colLeads.filter(l => Boolean(state.leadFlags[l.id]));
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

    // Opening status badge
    let openBadgeHtml = '';
    if (lead.open_status_label || lead.is_open_now !== undefined) {
      const cls = lead.is_open_now ? 'open' : 'closed';
      const lbl = lead.open_status_label || (lead.is_open_now ? 'Abierto ahora' : 'Cerrado');
      openBadgeHtml = `<span class="opening-status-badge ${cls}" style="font-size:9px; padding:1px 5px;">${escapeHtml(lbl)}</span>`;
    }

    // Tags
    let tagsHtml = '';
    if (Array.isArray(lead.tags) && lead.tags.length > 0) {
      tagsHtml = `<div class="card-tags">${lead.tags.slice(0, 2).map(t => `<span class="tag-chip" style="font-size:9px; padding:1px 4px;">${escapeHtml(t)}</span>`).join('')}</div>`;
    }

    // Checkbox and Suspected duplicate flag
    const isChecked = state.selectedLeadIds.has(lead.id);
    const hasDuplicateFlag = state.leadFlags && state.leadFlags[lead.id];
    let dupFlagHtml = '';
    if (hasDuplicateFlag) {
      dupFlagHtml = `
        <button type="button" class="btn-flag-duplicate" data-pair-id="${state.leadFlags[lead.id][0]}" title="Posible duplicado detectado">
          <svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-git-merge"/></svg>
        </button>
      `;
    }

    const cleanPhone = (lead.phone_e164 || lead.phone_raw || '').replace(/[^0-9]/g, '');

    card.innerHTML = `
      <div class="kanban-card-top">
        <div style="display:flex; align-items:center; gap:6px; flex:1; min-width:0;">
          <input type="checkbox" class="lead-select-checkbox" data-lead-id="${lead.id}" ${isChecked ? 'checked' : ''} style="cursor:pointer; width:15px; height:15px;">
          <div class="kanban-card-name" style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(lead.name)}</div>
          ${dupFlagHtml}
        </div>
        <div style="display:flex; align-items:center; gap:4px; flex-shrink:0;">
          ${openBadgeHtml}
          <span class="score-badge ${scoreClass}">${prob}%</span>
        </div>
      </div>

      <div class="kanban-card-meta">
        <span>${escapeHtml(lead.primary_category || lead.category_slug)}</span>
        <span>&bull;</span>
        <span>${escapeHtml(lead.phone_e164 || lead.phone_raw || 'Sin tel')}</span>
      </div>

      ${tagsHtml}
      ${alertsHtml ? `<div style="display:flex; gap:6px; flex-wrap:wrap;">${alertsHtml}</div>` : ''}

      <div class="kanban-card-actions">
        ${lead.has_whatsapp !== false && cleanPhone.length >= 10 ? `
          <div style="display:inline-flex; align-items:center;">
            <button type="button" class="btn-solo-icon btn-whatsapp btn-card-wa" data-tooltip="WhatsApp">
              <svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-message-circle"/></svg>
            </button>
            <button type="button" class="btn-solo-icon btn-wa-angle-trigger btn-card-wa-angle" data-tooltip="Enfoque de mensaje" style="width:20px; min-width:20px; margin-left:-3px; padding:0;">
              <svg style="width:10px;height:10px;" stroke="currentColor" fill="none"><use href="#icon-sliders"/></svg>
            </button>
          </div>
        ` : ''}

        ${lead.phone_e164 || lead.phone_raw ? `
          <a href="tel:${escapeHtml(lead.phone_e164 || lead.phone_raw)}" class="btn-solo-icon" data-tooltip="Llamar">
            <svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-phone"/></svg>
          </a>
        ` : ''}

        ${lead.website ? `
          <button type="button" class="btn-solo-icon btn-card-preview-web" data-tooltip="Ver sitio web">
            <svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-globe"/></svg>
          </button>
        ` : ''}

        <button type="button" class="btn-solo-icon btn-copy-card-pitch" data-tooltip="Copiar propuesta">
          <svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-copy"/></svg>
        </button>

        <button type="button" class="btn-solo-icon btn-open-drawer" data-tooltip="Ficha integral" style="margin-left: auto;">
          <svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-file-text"/></svg>
        </button>
      </div>
    `;

    const cb = card.querySelector('.lead-select-checkbox');
    if (cb) {
      cb.addEventListener('change', (e) => {
        e.stopPropagation();
        if (cb.checked) state.selectedLeadIds.add(lead.id);
        else state.selectedLeadIds.delete(lead.id);
        updateBatchBar();
      });
      cb.addEventListener('click', (e) => e.stopPropagation());
    }

    const btnDup = card.querySelector('.btn-flag-duplicate');
    if (btnDup) {
      btnDup.addEventListener('click', (e) => {
        e.stopPropagation();
        openDuplicateComparison(btnDup.dataset.pairId);
      });
    }

    const btnWa = card.querySelector('.btn-card-wa');
    if (btnWa) {
      btnWa.addEventListener('click', (e) => {
        e.stopPropagation();
        const msg = (state.settings.whatsapp_template || 'Hola, buen dia.').replace(/{nombre}/g, lead.name);
        logInteraction(lead.id, 'WHATSAPP', 'Apertura de chat wa.me');
        window.open(`https://wa.me/${cleanPhone}?text=${encodeURIComponent(msg)}`, '_blank');
      });
    }

    const btnAngle = card.querySelector('.btn-card-wa-angle');
    if (btnAngle) {
      btnAngle.addEventListener('click', (e) => {
        e.stopPropagation();
        openWhatsAppAngleMenu(lead, btnAngle);
      });
    }

    const btnWeb = card.querySelector('.btn-card-preview-web');
    if (btnWeb) {
      btnWeb.addEventListener('click', (e) => {
        e.stopPropagation();
        openInAppWebPreview(lead);
      });
    }

    const btnPitch = card.querySelector('.btn-copy-card-pitch');
    if (btnPitch) {
      btnPitch.addEventListener('click', (e) => {
        e.stopPropagation();
        copyCommercialPitch(lead);
      });
    }

    const btnDrawer = card.querySelector('.btn-open-drawer');
    if (btnDrawer) {
      btnDrawer.addEventListener('click', (e) => {
        e.stopPropagation();
        openLeadDrawer(lead);
      });
    }

    // Click card opens drawer (except when clicking buttons/links/checkbox)
    card.addEventListener('click', (e) => {
      if (e.target.closest('a') || e.target.closest('button') || e.target.closest('input')) return;
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

    // Filter by quick filter if any (Creative Freedom #3)
    if (state.quickFilter === 'whatsapp') {
      filtered = filtered.filter(l => l.has_whatsapp !== false && (l.phone_e164 || l.phone_raw));
    } else if (state.quickFilter === 'phone') {
      filtered = filtered.filter(l => Boolean(l.phone_e164 || l.phone_raw));
    } else if (state.quickFilter === 'website') {
      filtered = filtered.filter(l => Boolean(l.website));
    } else if (state.quickFilter === 'duplicates') {
      filtered = filtered.filter(l => Boolean(state.leadFlags[l.id]));
    }

    if (filtered.length === 0) {
      denseTableBody.innerHTML = `
        <tr>
          <td colspan="9" style="text-align: center; color: var(--text-muted); padding: 24px;">
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

      const isChecked = state.selectedLeadIds.has(lead.id);
      const hasDup = state.leadFlags && state.leadFlags[lead.id];
      const cleanPhone = (lead.phone_e164 || lead.phone_raw || '').replace(/[^0-9]/g, '');

      tr.innerHTML = `
        <td style="width:36px; text-align:center;">
          <input type="checkbox" class="lead-select-checkbox" data-lead-id="${lead.id}" ${isChecked ? 'checked' : ''} style="cursor:pointer; width:15px; height:15px;">
        </td>
        <td>
          <div style="display:flex; align-items:center; gap:6px;">
            <strong>${escapeHtml(lead.name)}</strong>
            ${hasDup ? `
              <button type="button" class="btn-flag-duplicate" data-pair-id="${state.leadFlags[lead.id][0]}" title="Posible duplicado detectado">
                <svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-git-merge"/></svg>
              </button>
            ` : ''}
          </div>
        </td>
        <td>${escapeHtml(lead.primary_category || lead.category_slug)}</td>
        <td><span class="score-badge med">${escapeHtml(stageName)}</span></td>
        <td><strong>${prob}%</strong></td>
        <td>${escapeHtml(lead.phone_e164 || lead.phone_raw || 'Sin tel')}</td>
        <td style="font-family: var(--font-mono); font-size: 11px;">
          ${lead.last_activity_at ? new Date(lead.last_activity_at).toLocaleDateString('es-MX') : '--'}
        </td>
        <td>${stagText}</td>
        <td>
          <div style="display:flex; align-items:center; gap:4px;">
            ${lead.has_whatsapp !== false && cleanPhone.length >= 10 ? `
              <button type="button" class="btn-solo-icon btn-whatsapp btn-table-wa" data-tooltip="WhatsApp" style="width:28px; height:28px; min-width:28px; min-height:28px;">
                <svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-message-circle"/></svg>
              </button>
            ` : ''}
            ${lead.website ? `
              <button type="button" class="btn-solo-icon btn-table-preview-web" data-tooltip="Ver sitio" style="width:28px; height:28px; min-width:28px; min-height:28px;">
                <svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-globe"/></svg>
              </button>
            ` : ''}
            <button type="button" class="btn-solo-icon btn-table-open" data-tooltip="Ficha integral" style="width:28px; height:28px; min-width:28px; min-height:28px;">
              <svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-file-text"/></svg>
            </button>
          </div>
        </td>
      `;

      const cb = tr.querySelector('.lead-select-checkbox');
      if (cb) {
        cb.addEventListener('change', (e) => {
          e.stopPropagation();
          if (cb.checked) state.selectedLeadIds.add(lead.id);
          else state.selectedLeadIds.delete(lead.id);
          updateBatchBar();
        });
        cb.addEventListener('click', (e) => e.stopPropagation());
      }

      const btnDup = tr.querySelector('.btn-flag-duplicate');
      if (btnDup) {
        btnDup.addEventListener('click', (e) => {
          e.stopPropagation();
          openDuplicateComparison(btnDup.dataset.pairId);
        });
      }

      const btnWa = tr.querySelector('.btn-table-wa');
      if (btnWa) {
        btnWa.addEventListener('click', (e) => {
          e.stopPropagation();
          const msg = (state.settings.whatsapp_template || 'Hola, buen dia.').replace(/{nombre}/g, lead.name);
          logInteraction(lead.id, 'WHATSAPP', 'Apertura de chat wa.me');
          window.open(`https://wa.me/${cleanPhone}?text=${encodeURIComponent(msg)}`, '_blank');
        });
      }

      const btnWeb = tr.querySelector('.btn-table-preview-web');
      if (btnWeb) {
        btnWeb.addEventListener('click', (e) => {
          e.stopPropagation();
          openInAppWebPreview(lead);
        });
      }

      const btnOpen = tr.querySelector('.btn-table-open');
      if (btnOpen) {
        btnOpen.addEventListener('click', (e) => {
          e.stopPropagation();
          openLeadDrawer(lead);
        });
      }

      tr.addEventListener('click', (e) => {
        if (e.target.closest('a') || e.target.closest('button') || e.target.closest('input')) return;
        openLeadDrawer(lead);
      });

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
        drawerWebsite.innerHTML = `
          <div style="display:flex; align-items:center; gap:8px;">
            <button type="button" class="btn-solo-icon btn-preview-web" data-tooltip="Abrir en visor" style="width:28px; height:28px; min-width:28px; min-height:28px;">
              <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-globe"/></svg>
            </button>
            <span class="preview-open-link" style="color:var(--text-main); cursor:pointer; text-decoration:underline;">${escapeHtml(lead.website)}</span>
          </div>
        `;
        const btnWeb = drawerWebsite.querySelector('.btn-preview-web');
        if (btnWeb) btnWeb.onclick = (e) => { e.preventDefault(); openInAppWebPreview(lead); };
        const lnkWeb = drawerWebsite.querySelector('.preview-open-link');
        if (lnkWeb) lnkWeb.onclick = (e) => { e.preventDefault(); openInAppWebPreview(lead); };
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

    // Opening status badge
    const elOpenStatus = document.getElementById('drawer-opening-status');
    if (elOpenStatus) {
      elOpenStatus.textContent = lead.open_status_label || (lead.is_open_now ? 'Abierto ahora' : 'Cerrado');
      elOpenStatus.className = `opening-status-badge ${lead.is_open_now ? 'open' : 'closed'}`;
    }

    // In-Line Edit Fields Population (FASE 10)
    const editName = document.getElementById('edit-drawer-name');
    const editCat = document.getElementById('edit-drawer-cat');
    const editPhone = document.getElementById('edit-drawer-phone');
    const editWeb = document.getElementById('edit-drawer-website');
    const editEmail = document.getElementById('edit-drawer-email');
    const editAddr = document.getElementById('edit-drawer-address');
    const editFb = document.getElementById('edit-drawer-fb');
    const editIg = document.getElementById('edit-drawer-ig');
    const editTiktok = document.getElementById('edit-drawer-tiktok');
    const editLinkedin = document.getElementById('edit-drawer-linkedin');
    const editX = document.getElementById('edit-drawer-x');
    const editYt = document.getElementById('edit-drawer-yt');

    if (editName) editName.value = lead.name || '';
    if (editCat) editCat.value = lead.category_slug || 'dentistas';
    if (editPhone) editPhone.value = lead.phone_raw || lead.phone_e164 || '';
    if (editWeb) editWeb.value = lead.website || '';
    if (editEmail) editEmail.value = lead.email || '';
    if (editAddr) editAddr.value = lead.address_raw || '';

    const socials = lead.social_links || {};
    if (editFb) editFb.value = socials.facebook || '';
    if (editIg) editIg.value = socials.instagram || '';
    if (editTiktok) editTiktok.value = socials.tiktok || '';
    if (editLinkedin) editLinkedin.value = socials.linkedin || '';
    if (editX) editX.value = socials.x || '';
    if (editYt) editYt.value = socials.youtube || '';

    // Proposal Fields Population (FASE 10)
    const propService = document.getElementById('quote-proposal-service');
    const propCurrency = document.getElementById('quote-proposal-currency');
    const propNotes = document.getElementById('quote-proposal-notes');
    if (propService) propService.value = lead.proposal_service || '';
    if (propCurrency) propCurrency.value = lead.proposal_currency || 'MXN';
    if (propNotes) propNotes.value = lead.proposal_notes || '';

    // Live Re-Audit Trigger (FASE 10)
    const btnReAudit = document.getElementById('btn-re-audit-lead');
    if (btnReAudit) {
      btnReAudit.onclick = async () => {
        btnReAudit.disabled = true;
        btnReAudit.style.opacity = '0.5';
        try {
          const res = await fetch(`/api/v1/leads/${lead.id}/audit`, { method: 'POST' });
          if (res.ok) {
            const auditData = await res.json();
            const score = auditData.technical_health_score !== undefined ? auditData.technical_health_score : auditData.score;
            if (drawerHealthScore) drawerHealthScore.textContent = `${Math.round(score || 0)}/100`;
            if (auditData.sales_arguments && drawerSalesArgsList) {
              drawerSalesArgsList.innerHTML = auditData.sales_arguments.map(a => `<li>${escapeHtml(a)}</li>`).join('');
            }
            lead.technical_health_score = score;
            lead.sales_arguments = auditData.sales_arguments || lead.sales_arguments;
            recordDailyAction('audit');
            showCommercialToast('Auditoria web re-evaluada con exito');
            loadPipelineBoard();
          }
        } catch (e) {
          console.error('[ReAudit] Error:', e);
        } finally {
          btnReAudit.disabled = false;
          btnReAudit.style.opacity = '1';
        }
      };
    }

    // 1-Click Copy Commercial Pitch
    const btnDrawerCopyPitch = document.getElementById('btn-drawer-copy-pitch');
    if (btnDrawerCopyPitch) {
      btnDrawerCopyPitch.onclick = () => copyCommercialPitch(lead);
    }

    // Render Drawer Tags
    renderDrawerTags(lead);

    // Init Drawer Cotizador Express
    initDrawerQuote(lead);

    // Init Drawer Radar Competencia
    loadDrawerCompetitors(lead);

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
      btnWa.className = 'btn-solo-icon btn-whatsapp';
      btnWa.dataset.tooltip = 'WhatsApp';
      btnWa.innerHTML = `<svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-message-circle"/></svg>`;
      btnWa.addEventListener('click', async () => {
        await logInteraction(lead.id, 'WHATSAPP', 'Apertura de chat wa.me');
        window.open(waUrl, '_blank');
      });
      drawerActionBar.appendChild(btnWa);

      const btnAngle = document.createElement('button');
      btnAngle.className = 'btn-solo-icon btn-wa-angle-trigger';
      btnAngle.dataset.tooltip = 'Enfoque de mensaje';
      btnAngle.style.width = '24px';
      btnAngle.style.minWidth = '24px';
      btnAngle.style.marginLeft = '-4px';
      btnAngle.innerHTML = `<svg style="width:11px;height:11px;" stroke="currentColor" fill="none"><use href="#icon-sliders"/></svg>`;
      btnAngle.addEventListener('click', (e) => {
        e.stopPropagation();
        openWhatsAppAngleMenu(lead, btnAngle);
      });
      drawerActionBar.appendChild(btnAngle);

      const btnNoWa = document.createElement('button');
      btnNoWa.className = 'btn-solo-icon';
      btnNoWa.dataset.tooltip = 'Sin WhatsApp (Linea fija)';
      btnNoWa.innerHTML = `<svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-phone-off"/></svg>`;
      btnNoWa.addEventListener('click', async () => {
        await fetch(`/api/v1/leads/${lead.id}/mark-no-whatsapp`, { method: 'POST' });
        lead.has_whatsapp = false;
        populateDrawerActions(lead);
        loadPipelineBoard();
      });
      drawerActionBar.appendChild(btnNoWa);
    } else {
      const btnFixed = document.createElement('button');
      btnFixed.className = 'btn-solo-icon disabled';
      btnFixed.dataset.tooltip = 'Solo linea fija';
      btnFixed.innerHTML = `<svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-phone-off"/></svg>`;
      drawerActionBar.appendChild(btnFixed);
    }

    // Call Action
    if (cleanPhone.length >= 10) {
      const btnCall = document.createElement('a');
      btnCall.className = 'btn-solo-icon';
      btnCall.href = `tel:+${cleanPhone}`;
      btnCall.dataset.tooltip = 'Llamar';
      btnCall.innerHTML = `<svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-phone"/></svg>`;
      btnCall.addEventListener('click', async () => {
        await logInteraction(lead.id, 'LLAMADA', 'Llamada telefonica iniciada');
      });
      drawerActionBar.appendChild(btnCall);
    }

    // Email Action
    if (lead.email) {
      const btnEmail = document.createElement('a');
      btnEmail.className = 'btn-solo-icon';
      btnEmail.href = `mailto:${escapeHtml(lead.email)}`;
      btnEmail.dataset.tooltip = 'Enviar correo';
      btnEmail.innerHTML = `<svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-mail"/></svg>`;
      drawerActionBar.appendChild(btnEmail);
    }

    // Website Action - Opens In-App Web Preview
    if (lead.website) {
      const btnWeb = document.createElement('button');
      btnWeb.className = 'btn-solo-icon btn-preview-web';
      btnWeb.dataset.tooltip = 'Ver sitio web';
      btnWeb.innerHTML = `<svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-globe"/></svg>`;
      btnWeb.addEventListener('click', () => openInAppWebPreview(lead));
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
        `El prospecto "${state.selectedLead.name}" sera movido a la papelera y sus datos quedaran blindados para evitar que futuras extracciones lo vuelvan a importar como nuevo.`,
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
  // ============================================================================
  // 9. Manual Lead Creation (Handled in FASE 10 Suite)
  // ============================================================================

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
      runDiagnosticsCheck();
    }
  }

  [navBtnLeads, mobNavLeads].forEach(el => el && el.addEventListener('click', () => switchView('leads')));
  [navBtnMap, mobNavMap].forEach(el => el && el.addEventListener('click', () => switchView('map')));
  [navBtnCalendar, mobNavCalendar].forEach(el => el && el.addEventListener('click', () => switchView('calendar')));
  [navBtnMetrics, mobNavMetrics].forEach(el => el && el.addEventListener('click', () => switchView('metrics')));
  [navBtnSettings, mobNavSettings].forEach(el => el && el.addEventListener('click', () => switchView('settings')));

  // Toggle Kanban vs Table vs Focus Mode
  const btnToggleFocus = document.getElementById('btn-toggle-focus');
  const btnExitFocus = document.getElementById('btn-exit-focus');
  const btnFilterOpenNow = document.getElementById('btn-filter-open-now');
  const tagFilterSelect = document.getElementById('tag-filter-select');
  const topBtnGlobalSearch = document.getElementById('top-btn-global-search');

  if (topBtnGlobalSearch) {
    topBtnGlobalSearch.addEventListener('click', () => openGlobalSearch());
  }

  if (btnToggleKanban) {
    btnToggleKanban.addEventListener('click', () => {
      state.leadViewMode = 'kanban';
      btnToggleKanban.classList.add('active');
      if (btnToggleTable) btnToggleTable.classList.remove('active');
      if (btnToggleTrash) btnToggleTrash.classList.remove('active');
      if (btnToggleFocus) btnToggleFocus.classList.remove('active');
      renderCurrentViewMode();
    });
  }

  if (btnToggleTable) {
    btnToggleTable.addEventListener('click', () => {
      state.leadViewMode = 'table';
      btnToggleTable.classList.add('active');
      if (btnToggleKanban) btnToggleKanban.classList.remove('active');
      if (btnToggleTrash) btnToggleTrash.classList.remove('active');
      if (btnToggleFocus) btnToggleFocus.classList.remove('active');
      renderCurrentViewMode();
    });
  }

  if (btnToggleFocus) {
    btnToggleFocus.addEventListener('click', () => {
      state.leadViewMode = 'focus';
      btnToggleFocus.classList.add('active');
      if (btnToggleKanban) btnToggleKanban.classList.remove('active');
      if (btnToggleTable) btnToggleTable.classList.remove('active');
      if (btnToggleTrash) btnToggleTrash.classList.remove('active');
      renderCurrentViewMode();
    });
  }

  if (btnExitFocus) {
    btnExitFocus.addEventListener('click', () => {
      state.leadViewMode = 'kanban';
      if (btnToggleKanban) btnToggleKanban.classList.add('active');
      if (btnToggleFocus) btnToggleFocus.classList.remove('active');
      renderCurrentViewMode();
    });
  }

  if (btnFilterOpenNow) {
    btnFilterOpenNow.addEventListener('click', () => {
      state.onlyOpenNow = !state.onlyOpenNow;
      btnFilterOpenNow.classList.toggle('active', state.onlyOpenNow);
      const dot = document.getElementById('filter-open-dot');
      if (dot) dot.classList.toggle('active-open', state.onlyOpenNow);
      loadPipelineBoard();
    });
  }

  if (tagFilterSelect) {
    tagFilterSelect.addEventListener('change', (e) => {
      state.tagFilter = e.target.value;
      loadPipelineBoard();
    });
  }

  if (btnToggleTrash) {
    btnToggleTrash.addEventListener('click', async () => {
      state.leadViewMode = 'trash';
      btnToggleTrash.classList.add('active');
      if (btnToggleKanban) btnToggleKanban.classList.remove('active');
      if (btnToggleTable) btnToggleTable.classList.remove('active');
      if (btnToggleFocus) btnToggleFocus.classList.remove('active');
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
        const data = await res.json();
        const job = data.job || data;
        const status = job.status || data.status;
        const progress = job.progress_pct !== undefined ? job.progress_pct : (data.progress_pct || 0);

        if (telemetryNewLeads) telemetryNewLeads.textContent = job.leads_saved !== undefined ? job.leads_saved : (data.new_leads_found || 0);
        if (telemetryDups) telemetryDups.textContent = job.leads_skipped !== undefined ? job.leads_skipped : (data.duplicates_filtered || 0);
        if (telemetryProgressBar) telemetryProgressBar.style.width = `${progress}%`;
        if (telemetryProgressPct) telemetryProgressPct.textContent = `${progress}%`;

        if (status === 'COMPLETED' || status === 'IDLE' || status === 'FAILED' || progress >= 100 || !data.has_active_job) {
          resetSweepControls();
          if (telemetryStatus) {
            telemetryStatus.textContent = status === 'FAILED' ? 'Finalizado' : 'Completado';
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
  // FASE 7: DYNAMIC GEO-SEARCH, LIVE SSE STREAM & DIAGNOSTICS SELF-CHECK
  // ============================================================================
  const btnRunSearch = document.getElementById('btn-run-search');
  const inputSearchLocation = document.getElementById('input-search-location');
  const inputSearchCategory = document.getElementById('input-search-category');
  const selectSearchLimit = document.getElementById('select-search-limit');
  const btnEmptyGoSearch = document.getElementById('btn-empty-go-search');

  if (btnEmptyGoSearch) {
    btnEmptyGoSearch.addEventListener('click', () => {
      switchView('map');
      if (inputSearchCategory) inputSearchCategory.focus();
    });
  }

  async function triggerDynamicSearch() {
    const loc = (inputSearchLocation ? inputSearchLocation.value : '').trim() || 'Tijuana';
    const cat = (inputSearchCategory ? inputSearchCategory.value : '').trim() || 'Dentistas';
    const limit = selectSearchLimit ? parseInt(selectSearchLimit.value, 10) : 10;

    if (btnRunSearch) {
      btnRunSearch.disabled = true;
      btnRunSearch.textContent = 'Buscando en vivo...';
    }

    if (telemetryStatus) {
      telemetryStatus.textContent = `Buscando ${cat} en ${loc}...`;
      telemetryStatus.style.color = '#81c784';
    }

    try {
      // 1. Geocode location if provided and map is ready
      if (loc && state.mapInstance) {
        try {
          const geoRes = await fetch(`/api/v1/geo/geocode?q=${encodeURIComponent(loc)}`);
          if (geoRes.ok) {
            const geoData = await geoRes.json();
            if (geoData.center) {
              state.mapInstance.flyTo([geoData.center.lat, geoData.center.lon], 13);
              if (geoData.bbox && state.mapPolygonsLayer) {
                state.mapPolygonsLayer.clearLayers();
                const bounds = [
                  [geoData.bbox.min_lat, geoData.bbox.min_lon],
                  [geoData.bbox.max_lat, geoData.bbox.max_lon]
                ];
                L.rectangle(bounds, { color: '#60a5fa', weight: 1, dashArray: '4, 4', fill: false }).addTo(state.mapPolygonsLayer);
              }
            }
          }
        } catch (e) {
          console.warn('[Geocode] Fallback a bounds por defecto:', e);
        }
      }

      // 2. Trigger Sweep Job
      const sweepRes = await fetch('/api/v1/geo/sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location_query: loc,
          query_term: cat,
          max_results: limit
        })
      });

      if (sweepRes.ok) {
        const sweepData = await sweepRes.json();
        state.activeSweepJobId = sweepData.job_id;
        startPollingSweepJob();
      }
    } catch (err) {
      console.error('[DynamicSearch] Error en barrido:', err);
    } finally {
      if (btnRunSearch) {
        btnRunSearch.disabled = false;
        btnRunSearch.innerHTML = '<svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-search"/></svg> Buscar / Iniciar Barrido';
      }
    }
  }

  if (btnRunSearch) {
    btnRunSearch.addEventListener('click', triggerDynamicSearch);
  }
  if (inputSearchLocation) {
    inputSearchLocation.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') triggerDynamicSearch();
    });
  }
  if (inputSearchCategory) {
    inputSearchCategory.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') triggerDynamicSearch();
    });
  }

  // Live SSE Stream
  function initEventStream() {
    try {
      const evtSource = new EventSource('/api/v1/stream/events');
      evtSource.onmessage = (e) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.type === 'lead_captured') {
            const lead = payload.data;
            const exists = state.leads.some(l => l.id === lead.id);
            if (!exists) {
              state.leads.unshift(lead);
              if (leadsEmptyState) leadsEmptyState.style.display = 'none';
              loadPipelineBoard();
              if (state.mapInstance && state.mapMarkersLayer && lead.lat && lead.lon) {
                const color = lead.score >= 70 ? '#81c784' : (lead.score >= 40 ? '#ffb74d' : '#b0bec5');
                const marker = L.circleMarker([lead.lat, lead.lon], {
                  radius: 7,
                  fillColor: color,
                  color: '#ffffff',
                  weight: 1.5,
                  opacity: 1,
                  fillOpacity: 0.85
                });
                const popupContent = `
                  <div class="map-popup-title">${escapeHtml(lead.name)}</div>
                  <div class="map-popup-meta">${escapeHtml(lead.category || '')} &bull; Fase: ${escapeHtml(lead.stage || 'Calificado')}</div>
                  <div>Probabilidad de Exito: <span class="map-popup-score">${lead.score || 0}%</span></div>
                  ${lead.whatsapp_url ? `<a href="${lead.whatsapp_url}" target="_blank" class="map-popup-btn">Contactar WhatsApp</a>` : ''}
                `;
                marker.bindPopup(popupContent);
                state.mapMarkersLayer.addLayer(marker);
              }
            }
          } else if (payload.type === 'status_update') {
            if (telemetryStatus) {
              telemetryStatus.textContent = payload.data.step || 'Procesando...';
              telemetryStatus.style.color = '#81c784';
            }
          }
        } catch (err) {
          // keep-alive or raw comment
        }
      };
      evtSource.onerror = () => {
        // SSE reconnects automatically
      };
    } catch (err) {
      console.warn('[SSE] EventSource init failed:', err);
    }
  }

  // Diagnostics Health-Check Runner
  const btnRunDiagnostics = document.getElementById('btn-run-diagnostics');
  async function runDiagnosticsCheck() {
    if (!btnRunDiagnostics) return;
    btnRunDiagnostics.disabled = true;
    btnRunDiagnostics.innerHTML = '<svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-refresh"/></svg> Verificando componentes...';

    try {
      const res = await fetch('/api/v1/diagnostics/health-check');
      if (!res.ok) return;
      const data = await res.json();
      const s = data.services || {};

      // PostgreSQL
      const elPgBadge = document.getElementById('diag-badge-postgres');
      const elPgMeta = document.getElementById('diag-meta-postgres');
      if (elPgBadge && s.postgres) {
        elPgBadge.className = `diag-badge ${s.postgres.status === 'OK' ? 'ok' : 'error'}`;
        elPgBadge.textContent = s.postgres.status;
        elPgMeta.textContent = `Respuesta: ${s.postgres.latency_ms}ms | Leads activos: ${s.postgres.active_leads_count}`;
      }

      // Redis
      const elRdBadge = document.getElementById('diag-badge-redis');
      const elRdMeta = document.getElementById('diag-meta-redis');
      if (elRdBadge && s.redis) {
        elRdBadge.className = `diag-badge ${s.redis.status === 'OK' ? 'ok' : 'error'}`;
        elRdBadge.textContent = s.redis.status;
        elRdMeta.textContent = `Respuesta: ${s.redis.latency_ms}ms | Tareas en cola: ${s.redis.pending_jobs_queue}`;
      }

      // Chromium
      const elCrBadge = document.getElementById('diag-badge-chromium');
      const elCrMeta = document.getElementById('diag-meta-chromium');
      if (elCrBadge && s.chromium_headless) {
        elCrBadge.className = `diag-badge ${s.chromium_headless.status === 'OK' ? 'ok' : 'warn'}`;
        elCrBadge.textContent = s.chromium_headless.status;
        elCrMeta.textContent = `Inicializacion: ${s.chromium_headless.execution_ms}ms | ${s.chromium_headless.sandbox}`;
      }

      // Nominatim
      const elNomBadge = document.getElementById('diag-badge-nominatim');
      const elNomMeta = document.getElementById('diag-meta-nominatim');
      if (elNomBadge && s.nominatim_api) {
        elNomBadge.className = `diag-badge ${s.nominatim_api.status === 'OK' ? 'ok' : 'warn'}`;
        elNomBadge.textContent = s.nominatim_api.status;
        elNomMeta.textContent = `Respuesta: ${s.nominatim_api.latency_ms}ms | Geocodificacion Activa`;
      }

      // Overpass
      const elOverBadge = document.getElementById('diag-badge-overpass');
      const elOverMeta = document.getElementById('diag-meta-overpass');
      if (elOverBadge && s.overpass_api) {
        elOverBadge.className = `diag-badge ${s.overpass_api.status === 'OK' ? 'ok' : 'warn'}`;
        elOverBadge.textContent = s.overpass_api.status;
        elOverMeta.textContent = s.overpass_api.latency_ms ? `Respuesta: ${s.overpass_api.latency_ms}ms` : 'Operativo (Rotacion de espejos)';
      }

      // Google Maps
      const elGmBadge = document.getElementById('diag-badge-gmaps');
      const elGmMeta = document.getElementById('diag-meta-gmaps');
      if (elGmBadge && s.google_maps) {
        elGmBadge.className = `diag-badge ${s.google_maps.status === 'OK' ? 'ok' : 'warn'}`;
        elGmBadge.textContent = s.google_maps.status;
        elGmMeta.textContent = `Respuesta: ${s.google_maps.latency_ms}ms | Conectividad Directa`;
      }
    } catch (e) {
      console.error('[Diagnostics] Error al verificar componentes:', e);
    } finally {
      if (btnRunDiagnostics) {
        btnRunDiagnostics.disabled = false;
        btnRunDiagnostics.innerHTML = '<svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-activity"/></svg> Ejecutar Diagnostico del Sistema';
      }
    }
  }

  if (btnRunDiagnostics) {
    btnRunDiagnostics.addEventListener('click', runDiagnosticsCheck);
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
      text: 'Ingresa prospectos manuales con deteccion instantanea de duplicados por telefono verificado, pagina web y ubicacion.'
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
      title: 'Ajustes Modulares & Seguridad Local',
      text: 'Personaliza los modulos de operacion, calibra los pesos predictivos de auditoria y protege el acceso en tu red local.'
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

  // ============================================================================
  // FASE 8: HERRAMIENTAS DE VELOCIDAD COMERCIAL Y CREATIVIDAD
  // ============================================================================

  // 1. Toast Notification Helper
  function showCommercialToast(message) {
    const existing = document.querySelector('.commercial-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'commercial-toast';
    toast.innerHTML = `
      <svg style="width:14px;height:14px;color:#7da382;" stroke="currentColor" fill="none"><use href="#icon-check"/></svg>
      <span>${escapeHtml(message)}</span>
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 2400);
  }

  // 2. Commercial Pitch 1-Click Copy
  async function copyCommercialPitch(lead) {
    if (!lead) return;
    let pitch = lead.commercial_pitch;
    if (!pitch) {
      try {
        const res = await fetch(`/api/v1/leads/${lead.id}/pitch`);
        if (res.ok) {
          const data = await res.json();
          pitch = data.pitch;
          lead.commercial_pitch = pitch;
        }
      } catch (e) {
        console.error('[Pitch] Error:', e);
      }
    }
    if (!pitch) {
      pitch = `Hola, me comunico con relación a mejoras en la presencia digital y velocidad de ${lead.name} en Tijuana para captar más clientes que buscan en internet.`;
    }
    navigator.clipboard.writeText(pitch).then(() => {
      showCommercialToast('Resumen comercial copiado al portapapeles');
    }).catch(() => {
      const ta = document.createElement('textarea');
      ta.value = pitch;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
      showCommercialToast('Resumen comercial copiado al portapapeles');
    });
  }

  // 3. Modo Enfoque (Focus Mode / Rafaga de Contacto Comercial)
  function getFocusLeads() {
    let list = (state.leads || []).filter(l => !l.is_deleted);
    if (state.activeCategory) {
      list = list.filter(l => l.category_slug === state.activeCategory || l.primary_category === state.activeCategory);
    }
    if (state.onlyOpenNow) {
      list = list.filter(l => l.is_open_now === true);
    }
    if (state.tagFilter) {
      list = list.filter(l => Array.isArray(l.tags) && l.tags.includes(state.tagFilter));
    }
    list.sort((a, b) => (b.acceptance_probability_pct || 0) - (a.acceptance_probability_pct || 0));
    return list;
  }

  function renderFocusMode() {
    const focusContainer = document.getElementById('focus-card-wrapper');
    const curNum = document.getElementById('focus-current-num');
    const totNum = document.getElementById('focus-total-num');
    const progBar = document.getElementById('focus-progress-bar');
    if (!focusContainer) return;

    const focusList = getFocusLeads();
    if (focusList.length === 0) {
      if (curNum) curNum.textContent = '0';
      if (totNum) totNum.textContent = '0';
      if (progBar) progBar.style.width = '0%';
      focusContainer.innerHTML = `
        <div style="text-align: center; padding: 48px 16px; color: var(--text-muted); background: var(--bg-surface); border: 1px solid var(--border); border-radius: var(--radius-md);">
          <div style="font-size: 14px; font-weight: 600; color: var(--text-main); margin-bottom: 6px;">No hay prospectos en esta seleccion</div>
          <p style="font-size: 12px; color: var(--text-secondary);">Cambia los filtros de categoria o desactiva "Solo abiertos ahora" para continuar la prospeccion.</p>
        </div>
      `;
      return;
    }

    if (state.focusIndex >= focusList.length) state.focusIndex = 0;
    if (state.focusIndex < 0) state.focusIndex = focusList.length - 1;

    const lead = focusList[state.focusIndex];
    state.selectedLead = lead;

    if (curNum) curNum.textContent = state.focusIndex + 1;
    if (totNum) totNum.textContent = focusList.length;
    if (progBar) progBar.style.width = `${((state.focusIndex + 1) / focusList.length) * 100}%`;

    const prob = Math.round(lead.acceptance_probability_pct || 0);
    const cleanPhone = (lead.phone_e164 || lead.phone_raw || '').replace(/[^0-9]/g, '');
    const waMsg = (state.settings.whatsapp_template || 'Hola, buen dia.').replace(/{nombre}/g, lead.name);
    const waUrl = cleanPhone.length >= 10 ? `https://wa.me/${cleanPhone}?text=${encodeURIComponent(waMsg)}` : null;

    const openCls = lead.is_open_now ? 'open' : 'closed';
    const openLbl = lead.open_status_label || (lead.is_open_now ? 'Abierto ahora' : 'Cerrado en este momento');

    // Flaws
    const flawBadges = (Array.isArray(lead.sales_arguments) ? lead.sales_arguments : []).slice(0, 3).map(arg => `
      <span class="focus-flaw-badge">${escapeHtml(arg)}</span>
    `).join('');

    focusContainer.innerHTML = `
      <div class="focus-lead-card">
        <div class="focus-lead-top">
          <div>
            <div class="focus-lead-name">${escapeHtml(lead.name)}</div>
            <div class="focus-lead-meta">
              <span>${escapeHtml(lead.primary_category || lead.category_slug)}</span>
              <span>&bull;</span>
              <span>${escapeHtml(lead.address_raw || 'Tijuana, BC')}</span>
              <span>&bull;</span>
              <span>${escapeHtml(lead.phone_e164 || lead.phone_raw || 'Sin telefono')}</span>
            </div>
          </div>
          <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
            <span class="opening-status-badge ${openCls}">${escapeHtml(openLbl)}</span>
            <span class="score-badge ${prob >= 70 ? 'high' : (prob >= 40 ? 'med' : 'low')}" style="font-size: 13px; padding: 4px 10px;">${prob}% Exito</span>
          </div>
        </div>

        ${flawBadges ? `<div class="focus-diagnostic-badges">${flawBadges}</div>` : ''}

        <div class="focus-pitch-box">
          <div class="focus-pitch-header">
            <span>Diagnostico Comercial Sin Tecnicismos</span>
            <button class="btn-secondary-action" id="focus-btn-copy-pitch" style="height: 22px; font-size: 10px; padding: 0 6px;">
              <svg style="width:10px;height:10px;" stroke="currentColor" fill="none"><use href="#icon-copy"/></svg>
              Copiar (C)
            </button>
          </div>
          <div>${escapeHtml(lead.commercial_pitch || 'Analizando negocio para generar propuesta comercial adaptada...')}</div>
        </div>

        <div class="focus-contact-actions">
          ${lead.has_whatsapp !== false && waUrl ? `
            <a href="${escapeHtml(waUrl)}" target="_blank" rel="noopener noreferrer" class="btn-focus-big btn-focus-whatsapp" id="focus-btn-wa">
              <svg style="width:16px;height:16px;" stroke="currentColor" fill="none"><use href="#icon-message-circle"/></svg>
              Contactar WhatsApp (W)
            </a>
          ` : `
            <button class="btn-focus-big disabled" style="background:var(--bg-subtle); color:var(--text-muted); cursor:not-allowed;">
              Sin WhatsApp disponible
            </button>
          `}

          ${cleanPhone.length >= 10 ? `
            <a href="tel:+${cleanPhone}" class="btn-focus-big btn-focus-call" id="focus-btn-call">
              <svg style="width:15px;height:15px;" stroke="currentColor" fill="none"><use href="#icon-phone"/></svg>
              Llamar
            </a>
          ` : `
            <button class="btn-focus-big disabled" style="background:var(--bg-subtle); color:var(--text-muted); cursor:not-allowed;">Sin tel</button>
          `}

          <button class="btn-focus-big" id="focus-btn-view-drawer" style="background:var(--bg-subtle); color:var(--text-main);">
            Ver Ficha
          </button>
        </div>

        <div class="focus-rapid-actions">
          <button class="btn-rapid-action btn-rapid-contacted" id="focus-btn-contacted" title="Avanza a Primer Contacto y pasa al siguiente lead">
            <svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-check"/></svg>
            Ya lo contacte (1)
          </button>
          <button class="btn-rapid-action btn-rapid-no-wa" id="focus-btn-no-wa" title="Marca permanentemente sin WhatsApp y salta al siguiente lead">
            Sin WhatsApp / Saltar (2)
          </button>
          <button class="btn-rapid-action btn-rapid-discard" id="focus-btn-discard" title="Descartar prospecto y pasar al siguiente lead">
            <svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-x"/></svg>
            Descartar (3)
          </button>
        </div>

        <div class="focus-nav-row">
          <button class="btn-secondary-action" id="focus-btn-prev" style="height: 26px; font-size: 11px;">
            &larr; Anterior (K)
          </button>
          <span>Usa las teclas <strong>J</strong> y <strong>K</strong> para navegar</span>
          <button class="btn-secondary-action" id="focus-btn-next" style="height: 26px; font-size: 11px;">
            Siguiente (J) &rarr;
          </button>
        </div>
      </div>
    `;

    // Wire listeners
    const btnCopy = document.getElementById('focus-btn-copy-pitch');
    if (btnCopy) btnCopy.addEventListener('click', () => copyCommercialPitch(lead));

    const btnWa = document.getElementById('focus-btn-wa');
    if (btnWa) {
      btnWa.addEventListener('click', async () => {
        await logInteraction(lead.id, 'WHATSAPP', 'Contacto iniciado desde Modo Enfoque');
      });
    }

    const btnCall = document.getElementById('focus-btn-call');
    if (btnCall) {
      btnCall.addEventListener('click', async () => {
        await logInteraction(lead.id, 'LLAMADA', 'Llamada iniciada desde Modo Enfoque');
      });
    }

    const btnDrawer = document.getElementById('focus-btn-view-drawer');
    if (btnDrawer) btnDrawer.addEventListener('click', () => openLeadDrawer(lead));

    const btnContacted = document.getElementById('focus-btn-contacted');
    if (btnContacted) btnContacted.addEventListener('click', () => handleFocusContacted(lead));

    const btnNoWa = document.getElementById('focus-btn-no-wa');
    if (btnNoWa) btnNoWa.addEventListener('click', () => handleFocusNoWa(lead));

    const btnDiscard = document.getElementById('focus-btn-discard');
    if (btnDiscard) btnDiscard.addEventListener('click', () => handleFocusDiscard(lead));

    const btnPrev = document.getElementById('focus-btn-prev');
    if (btnPrev) btnPrev.addEventListener('click', () => { state.focusIndex--; renderFocusMode(); });

    const btnNext = document.getElementById('focus-btn-next');
    if (btnNext) btnNext.addEventListener('click', () => { state.focusIndex++; renderFocusMode(); });
  }

  async function handleFocusContacted(lead) {
    try {
      await fetch(`/api/v1/pipeline/leads/${lead.id}/transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stage: 'FIRST_CONTACT', notes: 'Marcado como contactado desde Modo Enfoque' })
      });
      await logInteraction(lead.id, 'SEGUIMIENTO', 'Transicion rapida a Primer Contacto');
      lead.lifecycle_stage = 'FIRST_CONTACT';
      showCommercialToast('Avanzado a Primer Contacto');
      state.focusIndex++;
      renderFocusMode();
    } catch (e) {
      console.error('[Focus] Error contacted:', e);
      state.focusIndex++;
      renderFocusMode();
    }
  }

  async function handleFocusNoWa(lead) {
    try {
      await fetch(`/api/v1/leads/${lead.id}/mark-no-whatsapp`, { method: 'POST' });
      lead.has_whatsapp = false;
      showCommercialToast('Marcado sin WhatsApp');
      state.focusIndex++;
      renderFocusMode();
    } catch (e) {
      console.error('[Focus] Error no-wa:', e);
      state.focusIndex++;
      renderFocusMode();
    }
  }

  async function handleFocusDiscard(lead) {
    try {
      await fetch(`/api/v1/pipeline/leads/${lead.id}/transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stage: 'CLOSED_LOST', loss_reason: 'Descartado en prospeccion rapida', notes: 'Descartado desde Modo Enfoque' })
      });
      lead.lifecycle_stage = 'CLOSED_LOST';
      showCommercialToast('Prospecto descartado');
      state.focusIndex++;
      renderFocusMode();
    } catch (e) {
      console.error('[Focus] Error discard:', e);
      state.focusIndex++;
      renderFocusMode();
    }
  }

  // 4. Buscador Global Rapido (Ctrl + K)
  const modalGlobalSearch = document.getElementById('modal-global-search');
  const globalSearchInput = document.getElementById('global-search-input');
  const globalSearchResults = document.getElementById('global-search-results');
  const modalGlobalSearchClose = document.getElementById('modal-global-search-close');
  let searchDebounceTimeout = null;

  function openGlobalSearch() {
    if (!modalGlobalSearch) return;
    modalGlobalSearch.style.display = 'flex';
    if (globalSearchInput) {
      globalSearchInput.value = '';
      globalSearchInput.focus();
    }
    state.globalSearchResults = [];
    state.selectedGlobalSearchIndex = 0;
    if (globalSearchResults) {
      globalSearchResults.innerHTML = `
        <div style="padding: 24px 16px; text-align: center; color: var(--text-muted); font-size: 12px;">
          Escribe para buscar prospectos al instante en Tijuana...
        </div>
      `;
    }
  }

  function closeGlobalSearch() {
    if (modalGlobalSearch) modalGlobalSearch.style.display = 'none';
  }

  if (modalGlobalSearchClose) {
    modalGlobalSearchClose.addEventListener('click', closeGlobalSearch);
  }

  if (modalGlobalSearch) {
    modalGlobalSearch.addEventListener('click', (e) => {
      if (e.target === modalGlobalSearch) closeGlobalSearch();
    });
  }

  if (globalSearchInput) {
    globalSearchInput.addEventListener('input', (e) => {
      clearTimeout(searchDebounceTimeout);
      const q = e.target.value.trim();
      if (!q) {
        if (globalSearchResults) {
          globalSearchResults.innerHTML = `
            <div style="padding: 24px 16px; text-align: center; color: var(--text-muted); font-size: 12px;">
              Escribe para buscar prospectos al instante en Tijuana...
            </div>
          `;
        }
        return;
      }
      searchDebounceTimeout = setTimeout(async () => {
        try {
          const res = await fetch(`/api/v1/leads/search/global?q=${encodeURIComponent(q)}`);
          if (res.ok) {
            const results = await res.json();
            state.globalSearchResults = results;
            state.selectedGlobalSearchIndex = 0;
            renderGlobalSearchResults(results);
          }
        } catch (err) {
          console.error('[Search] Error:', err);
        }
      }, 180);
    });

    globalSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeGlobalSearch();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (state.globalSearchResults.length > 0) {
          state.selectedGlobalSearchIndex = (state.selectedGlobalSearchIndex + 1) % state.globalSearchResults.length;
          highlightSelectedSearchResult();
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (state.globalSearchResults.length > 0) {
          state.selectedGlobalSearchIndex = (state.selectedGlobalSearchIndex - 1 + state.globalSearchResults.length) % state.globalSearchResults.length;
          highlightSelectedSearchResult();
        }
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (state.globalSearchResults.length > 0 && state.globalSearchResults[state.selectedGlobalSearchIndex]) {
          const selected = state.globalSearchResults[state.selectedGlobalSearchIndex];
          closeGlobalSearch();
          openLeadDrawer(selected);
        }
      }
    });
  }

  function renderGlobalSearchResults(results) {
    if (!globalSearchResults) return;
    if (results.length === 0) {
      globalSearchResults.innerHTML = `
        <div style="padding: 24px 16px; text-align: center; color: var(--text-muted); font-size: 12px;">
          No se encontraron prospectos coincidentes en Tijuana.
        </div>
      `;
      return;
    }

    globalSearchResults.innerHTML = results.map((l, idx) => {
      const prob = Math.round(l.acceptance_probability_pct || 0);
      const isSel = idx === state.selectedGlobalSearchIndex ? 'selected' : '';
      const tagsHtml = (Array.isArray(l.tags) ? l.tags : []).slice(0, 2).map(t => `<span class="tag-chip" style="font-size:9px; padding:1px 4px;">${escapeHtml(t)}</span>`).join('');
      return `
        <div class="global-search-item ${isSel}" data-index="${idx}" data-lead-id="${l.id}">
          <div class="global-search-item-info">
            <div class="global-search-item-name">${escapeHtml(l.name)}</div>
            <div class="global-search-item-meta">
              <span>${escapeHtml(l.primary_category || l.category_slug)}</span>
              <span>&bull;</span>
              <span>${escapeHtml(l.phone_e164 || l.phone_raw || 'Sin tel')}</span>
              <span>&bull;</span>
              <span>${escapeHtml(l.address_raw || 'Tijuana')}</span>
              ${tagsHtml}
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="score-badge ${prob >= 70 ? 'high' : (prob >= 40 ? 'med' : 'low')}">${prob}%</span>
          </div>
        </div>
      `;
    }).join('');

    globalSearchResults.querySelectorAll('.global-search-item').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.dataset.index, 10);
        const selected = results[idx];
        if (selected) {
          closeGlobalSearch();
          openLeadDrawer(selected);
        }
      });
    });
  }

  function highlightSelectedSearchResult() {
    if (!globalSearchResults) return;
    globalSearchResults.querySelectorAll('.global-search-item').forEach((el, idx) => {
      el.classList.toggle('selected', idx === state.selectedGlobalSearchIndex);
      if (idx === state.selectedGlobalSearchIndex) {
        el.scrollIntoView({ block: 'nearest' });
      }
    });
  }

  // 5. Tags Management
  function renderDrawerTags(lead) {
    const container = document.getElementById('drawer-tags-container');
    const inputTag = document.getElementById('input-drawer-tag');
    const btnAddTag = document.getElementById('btn-add-drawer-tag');
    if (!container) return;

    const tags = Array.isArray(lead.tags) ? lead.tags : [];
    container.innerHTML = tags.map(t => `
      <span class="tag-chip">
        <span>${escapeHtml(t)}</span>
        <span class="tag-chip-remove" data-tag="${escapeHtml(t)}">&times;</span>
      </span>
    `).join('');

    container.querySelectorAll('.tag-chip-remove').forEach(btn => {
      btn.addEventListener('click', async () => {
        const tagToRemove = btn.dataset.tag;
        const newTags = tags.filter(x => x !== tagToRemove);
        await saveLeadTags(lead.id, newTags);
        lead.tags = newTags;
        renderDrawerTags(lead);
        loadPipelineBoard();
      });
    });

    const handleAdd = async () => {
      const val = inputTag?.value.trim();
      if (!val) return;
      if (!tags.includes(val)) {
        const newTags = [...tags, val];
        await saveLeadTags(lead.id, newTags);
        lead.tags = newTags;
        if (inputTag) inputTag.value = '';
        renderDrawerTags(lead);
        loadPipelineBoard();
      }
    };

    if (btnAddTag) btnAddTag.onclick = handleAdd;
    if (inputTag) {
      inputTag.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleAdd();
        }
      };
    }
  }

  async function saveLeadTags(leadId, tags) {
    try {
      await fetch(`/api/v1/leads/${leadId}/tags`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tags })
      });
      showCommercialToast('Etiquetas actualizadas');
    } catch (e) {
      console.error('[Tags] Error:', e);
    }
  }

  // 6. Cotizador Express
  function initDrawerQuote(lead) {
    const checkboxes = document.querySelectorAll('.quote-pkg-checkbox');
    const customInput = document.getElementById('quote-custom-amount');
    const totalDisplay = document.getElementById('quote-total-display');
    const btnSaveQuote = document.getElementById('btn-save-quote');
    const btnCopyProposal = document.getElementById('btn-copy-quote-proposal');

    checkboxes.forEach(cb => { cb.checked = false; });
    if (customInput) customInput.value = lead.deal_value_estimated ? Math.round(lead.deal_value_estimated) : '';

    function recalculate() {
      let sum = 0;
      checkboxes.forEach(cb => {
        if (cb.checked) sum += parseFloat(cb.dataset.price || 0);
      });
      const customVal = customInput && customInput.value ? parseFloat(customInput.value) : 0;
      const total = customVal > 0 ? customVal : sum;
      if (totalDisplay) totalDisplay.textContent = `$${total.toLocaleString('es-MX')} MXN`;
      return total;
    }

    checkboxes.forEach(cb => {
      cb.onchange = recalculate;
    });
    if (customInput) customInput.oninput = recalculate;
    recalculate();

    if (btnSaveQuote) {
      btnSaveQuote.onclick = async () => {
        const total = recalculate();
        const propService = document.getElementById('quote-proposal-service');
        const propCurrency = document.getElementById('quote-proposal-currency');
        const propNotes = document.getElementById('quote-proposal-notes');

        const serviceVal = propService ? propService.value.trim() : '';
        const currencyVal = propCurrency ? propCurrency.value : 'MXN';
        const notesVal = propNotes ? propNotes.value.trim() : '';

        try {
          await fetch(`/api/v1/leads/${lead.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              deal_value_estimated: total,
              proposal_service: serviceVal || 'Servicio Digital',
              proposal_currency: currencyVal,
              proposal_notes: notesVal
            })
          });
          lead.deal_value_estimated = total;
          lead.proposal_service = serviceVal || 'Servicio Digital';
          lead.proposal_currency = currencyVal;
          lead.proposal_notes = notesVal;

          recordDailyAction('proposal');
          showCommercialToast(`Propuesta comercial de $${total.toLocaleString('es-MX')} ${currencyVal} guardada`);
          loadPipelineBoard();
        } catch (e) {
          console.error('[Quote] Error:', e);
        }
      };
    }

    // 1-Click Printable Proposal Sheet (Creative Freedom 2)
    const btnPrintSheet = document.getElementById('btn-print-proposal-sheet');
    if (btnPrintSheet) {
      btnPrintSheet.onclick = () => {
        const total = recalculate();
        const propService = document.getElementById('quote-proposal-service');
        const propCurrency = document.getElementById('quote-proposal-currency');
        const propNotes = document.getElementById('quote-proposal-notes');

        const serviceVal = propService ? propService.value.trim() : (lead.proposal_service || 'Digitalizacion Comercial');
        const currencyVal = propCurrency ? propCurrency.value : (lead.proposal_currency || 'MXN');
        const notesVal = propNotes ? propNotes.value.trim() : (lead.proposal_notes || 'Implementacion de presencia local, conversion y optimizacion web.');

        const argsList = Array.isArray(lead.sales_arguments) ? lead.sales_arguments : [];
        const healthScore = Math.round(lead.technical_health_score || 0);

        const printContainer = document.getElementById('printable-proposal-report');
        if (printContainer) {
          printContainer.innerHTML = `
            <div class="printable-header">
              <div>
                <div class="printable-title">PROPUESTA COMERCIAL Y DIAGNOSTICO DIGITAL</div>
                <div style="font-size:12px; color:#4b5563; margin-top:4px;">
                  Tijuana, Baja California &bull; Preparado para: <strong>${escapeHtml(lead.name)}</strong>
                </div>
              </div>
              <div style="text-align:right; font-size:11px; color:#6b7280;">
                Fecha: ${new Date().toLocaleDateString('es-MX', { year:'numeric', month:'long', day:'numeric' })}
              </div>
            </div>

            <div class="printable-section">
              <div class="printable-section-title">1. Diagnostico de Presencia Tecnica y Web</div>
              <div style="font-size:12px; line-height:1.5;">
                <p><strong>Calificacion de Salud Web:</strong> ${healthScore}/100 (${healthScore >= 70 ? 'Aceptable' : healthScore >= 40 ? 'Requiere optimizacion' : 'Critico / Sin candado seguro'})</p>
                <p><strong>Sitio Web:</strong> ${lead.website ? escapeHtml(lead.website) : 'No cuenta con portal dedicado activo.'}</p>
                <p><strong>Giro / Categoria:</strong> ${escapeHtml(lead.primary_category || lead.category_slug)}</p>
                <p><strong>Ubicacion:</strong> ${escapeHtml(lead.address_raw || 'Tijuana, BC')}</p>
              </div>
            </div>

            <div class="printable-section">
              <div class="printable-section-title">2. Oportunidades de Mejora Comercial Detectadas</div>
              <ul style="font-size:12px; line-height:1.6; padding-left:18px; margin:4px 0;">
                ${argsList.length > 0 ? argsList.map(a => `<li>${escapeHtml(a)}</li>`).join('') : '<li>Modernizacion general para captacion activa de clientes locales en Tijuana.</li>'}
              </ul>
            </div>

            <div class="printable-section">
              <div class="printable-section-title">3. Servicio y Alcance Propuesto</div>
              <div style="font-size:13px; font-weight:600; color:#111827; margin-bottom:6px;">${escapeHtml(serviceVal)}</div>
              <div style="font-size:12px; line-height:1.5; color:#374151;">${escapeHtml(notesVal)}</div>

              <div class="printable-amount-box">
                <div style="font-size:12px; color:#4b5563;">Inversion Estimada del Proyecto:</div>
                <div style="font-size:22px; font-weight:800; color:#111827; font-family:monospace;">
                  $${total.toLocaleString('es-MX')} ${currencyVal}
                </div>
                <div style="font-size:11px; color:#6b7280; margin-top:4px;">Incluye soporte tecnico y acompanamiento comercial local en Tijuana.</div>
              </div>
            </div>
          `;
          window.print();
        }
      };
    }

    if (btnCopyProposal) {
      btnCopyProposal.onclick = () => {
        const total = recalculate();
        const selectedPkgs = Array.from(checkboxes).filter(c => c.checked).map(c => c.dataset.name);
        const pkgText = selectedPkgs.length > 0 ? selectedPkgs.join(' + ') : 'Solución de Modernización Digital';
        const proposal = `Hola, respecto a la modernización de ${lead.name}, le comparto la propuesta preparada: ${pkgText}. Inversión estimada: $${total.toLocaleString('es-MX')} MXN con soporte local en Tijuana. ¿Le gustaría que le comparta más detalles hoy?`;
        navigator.clipboard.writeText(proposal).then(() => {
          showCommercialToast('Propuesta comercial copiada al portapapeles');
        });
      };
    }
  }

  // 7. Radar de Competencia Local
  async function loadDrawerCompetitors(lead) {
    const pctWeb = document.getElementById('radar-pct-web');
    const pctSsl = document.getElementById('radar-pct-ssl');
    const leverageBox = document.getElementById('radar-leverage-box');
    const competitorsList = document.getElementById('radar-competitors-list');
    const btnCopyRadar = document.getElementById('btn-copy-radar-pitch');

    try {
      const res = await fetch(`/api/v1/leads/${lead.id}/competitors`);
      if (!res.ok) return;
      const data = await res.json();

      if (pctWeb) pctWeb.textContent = `${data.zone_stats.pct_with_website}%`;
      if (pctSsl) pctSsl.textContent = `${data.zone_stats.pct_with_secure_site}%`;
      if (leverageBox) leverageBox.textContent = data.commercial_leverage_text || 'Comparativa comercial lista.';

      if (competitorsList) {
        if (!data.competitors || data.competitors.length === 0) {
          competitorsList.innerHTML = '<div style="font-size:11px; color:var(--text-muted);">Sin otros competidores cercanos registrados en la misma categoría.</div>';
        } else {
          competitorsList.innerHTML = data.competitors.map(c => `
            <div class="radar-competitor-item">
              <div>
                <strong>${escapeHtml(c.name)}</strong>
                <div style="font-size:10px; color:var(--text-muted);">${escapeHtml(c.status_summary)}</div>
              </div>
              <span class="score-badge ${c.health_score >= 70 ? 'high' : 'low'}">${c.health_score}/100</span>
            </div>
          `).join('');
        }
      }

      if (btnCopyRadar) {
        btnCopyRadar.onclick = () => {
          const text = data.commercial_leverage_text || `En esta zona de Tijuana, el ${data.zone_stats.pct_with_secure_site}% de los negocios ya cuenta con presencia digital protegida.`;
          navigator.clipboard.writeText(text).then(() => {
            showCommercialToast('Argumento de competencia copiado al portapapeles');
          });
        };
      }
    } catch (e) {
      console.error('[Competitors] Error:', e);
    }
  }

  // 8. Atajos de Teclado Comerciales (Navegacion Agil / Una sola mano)
  window.addEventListener('keydown', (e) => {
    // Global Search toggle (Ctrl + K or Cmd + K)
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openGlobalSearch();
      return;
    }

    const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
    const isTyping = activeTag === 'input' || activeTag === 'textarea' || activeTag === 'select';

    if (e.key === 'Escape') {
      if (modalGlobalSearch && modalGlobalSearch.style.display !== 'none') {
        closeGlobalSearch();
        return;
      }
      if (drawerLeadDetail && drawerLeadDetail.style.display !== 'none') {
        drawerLeadDetail.style.display = 'none';
        return;
      }
      if (state.leadViewMode === 'focus') {
        state.leadViewMode = 'kanban';
        if (btnToggleKanban) btnToggleKanban.classList.add('active');
        if (btnToggleFocus) btnToggleFocus.classList.remove('active');
        renderCurrentViewMode();
        return;
      }
      return;
    }

    if (isTyping) return;

    const key = e.key.toLowerCase();

    // Toggle Focus Mode (F)
    if (key === 'f') {
      e.preventDefault();
      if (state.leadViewMode === 'focus') {
        state.leadViewMode = 'kanban';
        if (btnToggleKanban) btnToggleKanban.classList.add('active');
        if (btnToggleFocus) btnToggleFocus.classList.remove('active');
      } else {
        state.leadViewMode = 'focus';
        if (btnToggleFocus) btnToggleFocus.classList.add('active');
        if (btnToggleKanban) btnToggleKanban.classList.remove('active');
      }
      renderCurrentViewMode();
      return;
    }

    // Navigation: Next (J or ArrowDown)
    if (key === 'j' || e.key === 'ArrowDown') {
      e.preventDefault();
      if (state.leadViewMode === 'focus') {
        state.focusIndex++;
        renderFocusMode();
      }
      return;
    }

    // Navigation: Prev (K or ArrowUp)
    if (key === 'k' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (state.leadViewMode === 'focus') {
        state.focusIndex--;
        renderFocusMode();
      }
      return;
    }

    // WhatsApp shortcut (W)
    if (key === 'w' && state.selectedLead) {
      e.preventDefault();
      const clean = (state.selectedLead.phone_e164 || state.selectedLead.phone_raw || '').replace(/[^0-9]/g, '');
      if (clean.length >= 10 && state.selectedLead.has_whatsapp !== false) {
        const msg = (state.settings.whatsapp_template || 'Hola, buen dia.').replace(/{nombre}/g, state.selectedLead.name);
        window.open(`https://wa.me/${clean}?text=${encodeURIComponent(msg)}`, '_blank');
      }
      return;
    }

    // Copy commercial pitch (C)
    if (key === 'c' && state.selectedLead) {
      e.preventDefault();
      copyCommercialPitch(state.selectedLead);
      return;
    }

    // Quick Note (N)
    if (key === 'n' && state.selectedLead && drawerLeadDetail && drawerLeadDetail.style.display !== 'none') {
      e.preventDefault();
      const tabNotesBtn = document.querySelector('.drawer-tab-btn[data-tab="tab-notes"]');
      if (tabNotesBtn) tabNotesBtn.click();
      const noteTa = document.getElementById('drawer-note-content');
      if (noteTa) noteTa.focus();
      return;
    }

    // Focus mode numbers: 1 (Contacted), 2 (No WA), 3 (Discard)
    if (state.leadViewMode === 'focus' && state.selectedLead) {
      if (key === '1') {
        e.preventDefault();
        handleFocusContacted(state.selectedLead);
      } else if (key === '2') {
        e.preventDefault();
        handleFocusNoWa(state.selectedLead);
      } else if (key === '3') {
        e.preventDefault();
        handleFocusDiscard(state.selectedLead);
      }
    }

    // Escape closes In-App Preview or Duplicate Modal
    if (key === 'Escape') {
      closeInAppWebPreview();
      const dupModal = document.getElementById('modal-merge-duplicate');
      if (dupModal) dupModal.style.display = 'none';
      const angleMenu = document.getElementById('wa-angle-menu');
      if (angleMenu) angleMenu.classList.add('hidden');
    }
  });

  // ============================================================================
  // FASE 9: IN-APP WEB PREVIEW (VISOR INTEGRADO SIN SALIR DE LA APP)
  // ============================================================================
  function openInAppWebPreview(lead) {
    if (!lead || !lead.website) {
      showCommercialToast('Este prospecto no tiene sitio web registrado.');
      return;
    }
    state.activePreviewLead = lead;

    const previewContainer = document.getElementById('in-app-web-preview');
    if (!previewContainer) return;

    const urlText = document.getElementById('preview-url-text');
    const sslIcon = document.getElementById('preview-ssl-icon');
    const flawPill = document.getElementById('preview-live-flaw-pill');
    const flawSummary = document.getElementById('preview-flaw-summary');
    const flawList = document.getElementById('preview-flaw-list');
    const extLink = document.getElementById('preview-external-link');
    const iframe = document.getElementById('preview-iframe');

    // Domain display
    const domain = lead.normalized_domain || lead.website.replace(/^https?:\/\//i, '').replace(/\/$/, '');
    if (urlText) urlText.textContent = domain;

    // SSL badge
    const isHttps = lead.website.toLowerCase().startsWith('https://');
    if (sslIcon) {
      if (isHttps) {
        sslIcon.className = 'preview-ssl-badge valid';
        sslIcon.title = 'Sitio con conexion segura (SSL)';
        sslIcon.innerHTML = '<svg class="icon-inline" style="width:14px;height:14px;"><use href="#icon-lock"/></svg>';
      } else {
        sslIcon.className = 'preview-ssl-badge warning';
        sslIcon.title = 'Sitio no protegido (sin candado SSL)';
        sslIcon.innerHTML = '<svg class="icon-inline" style="width:14px;height:14px;"><use href="#icon-unlock"/></svg>';
      }
    }

    // Creative Freedom #1: Live Speed & Flaw Visual Overlay on Preview
    const flaws = Array.isArray(lead.sales_arguments) ? lead.sales_arguments : [];
    if (flawPill) {
      if (flaws.length > 0) {
        flawPill.classList.remove('hidden');
        if (flawSummary) flawSummary.textContent = `${flaws.length} punto${flaws.length > 1 ? 's' : ''} de mejora`;
        if (flawList) {
          flawList.innerHTML = `<ul>${flaws.map(f => `<li>${escapeHtml(f)}</li>`).join('')}</ul>`;
        }
      } else {
        flawPill.classList.add('hidden');
      }
    }

    // External link
    if (extLink) extLink.href = lead.website;

    // Proxy URL inside isolated iframe
    const proxyUrl = `/api/v1/preview/proxy?url=${encodeURIComponent(lead.website)}`;
    if (iframe) iframe.src = proxyUrl;

    // Load Lead Notes for quick notepad inside preview
    loadPreviewNotes(lead.id);

    // Show preview container
    previewContainer.classList.remove('hidden');
    document.body.classList.add('preview-open');
  }

  function closeInAppWebPreview() {
    const previewContainer = document.getElementById('in-app-web-preview');
    if (previewContainer) previewContainer.classList.add('hidden');
    document.body.classList.remove('preview-open');

    const iframe = document.getElementById('preview-iframe');
    if (iframe) iframe.src = 'about:blank';

    const notepadDrawer = document.getElementById('preview-notepad-drawer');
    if (notepadDrawer) notepadDrawer.classList.add('hidden');

    state.activePreviewLead = null;
  }

  async function loadPreviewNotes(leadId) {
    const historyEl = document.getElementById('preview-notes-history');
    if (!historyEl) return;
    try {
      const res = await fetch(`/api/v1/leads/${leadId}/notes`);
      if (res.ok) {
        const notes = await res.json();
        if (notes.length === 0) {
          historyEl.innerHTML = '<div style="color:var(--text-muted); font-size:11px;">Sin notas guardadas aun.</div>';
        } else {
          historyEl.innerHTML = notes.map(n => `
            <div class="preview-note-item">
              <div>${escapeHtml(n.content)}</div>
              <div style="font-size:9px; color:var(--text-muted); margin-top:2px;">${new Date(n.created_at).toLocaleString('es-MX')}</div>
            </div>
          `).join('');
        }
      }
    } catch (err) {
      console.error('Error loading notes:', err);
    }
  }

  async function submitPreviewNote() {
    if (!state.activePreviewLead) return;
    const input = document.getElementById('preview-note-input');
    if (!input || !input.value.trim()) return;

    const content = input.value.trim();
    try {
      const res = await fetch(`/api/v1/leads/${state.activePreviewLead.id}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content, author: 'Operador' })
      });
      if (res.ok) {
        input.value = '';
        loadPreviewNotes(state.activePreviewLead.id);
        showCommercialToast('Nota guardada');
      }
    } catch (err) {
      showCommercialToast('Error al guardar la nota');
    }
  }

  // ============================================================================
  // FASE 9: BARRA FLOTANTE DE ACCIONES EN LOTE
  // ============================================================================
  function updateBatchBar() {
    const bar = document.getElementById('floating-batch-bar');
    const countEl = document.getElementById('batch-selected-count');
    const count = state.selectedLeadIds.size;

    if (count >= 2) {
      if (bar) bar.classList.remove('hidden');
      if (countEl) countEl.textContent = count;
    } else {
      if (bar) bar.classList.add('hidden');
    }

    document.querySelectorAll('.lead-select-checkbox').forEach(cb => {
      cb.checked = state.selectedLeadIds.has(cb.dataset.leadId);
    });
  }

  function clearBatchSelection() {
    state.selectedLeadIds.clear();
    const thAll = document.getElementById('th-select-all-leads');
    if (thAll) thAll.checked = false;
    updateBatchBar();
  }

  async function batchUpdateStage(newStage) {
    if (state.selectedLeadIds.size === 0) return;
    try {
      const res = await fetch('/api/v1/leads/batch/stage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lead_ids: Array.from(state.selectedLeadIds),
          stage: newStage,
          reason: 'Cambio de fase en lote'
        })
      });
      if (res.ok) {
        const data = await res.json();
        showCommercialToast(`${data.updated_count} prospectos movidos`);
        clearBatchSelection();
        loadPipelineBoard();
      }
    } catch (err) {
      showCommercialToast('Error al actualizar fase');
    }
  }

  async function batchUpdateTags(action, tag) {
    if (state.selectedLeadIds.size === 0) return;
    try {
      const res = await fetch('/api/v1/leads/batch/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lead_ids: Array.from(state.selectedLeadIds),
          action: action,
          tag: tag
        })
      });
      if (res.ok) {
        showCommercialToast('Etiquetas actualizadas');
        clearBatchSelection();
        loadPipelineBoard();
      }
    } catch (err) {
      showCommercialToast('Error al actualizar etiquetas');
    }
  }

  async function batchExport() {
    if (state.selectedLeadIds.size === 0) return;
    try {
      const res = await fetch('/api/v1/leads/batch/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lead_ids: Array.from(state.selectedLeadIds)
        })
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `prospectos_exportados_${new Date().toISOString().slice(0,10)}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        showCommercialToast('Descarga CSV iniciada');
      }
    } catch (err) {
      showCommercialToast('Error al exportar prospectos');
    }
  }

  async function batchTrash() {
    if (state.selectedLeadIds.size === 0) return;
    const count = state.selectedLeadIds.size;
    if (!confirm(`¿Mover ${count} prospectos a la papelera?`)) return;

    try {
      const res = await fetch('/api/v1/leads/batch/trash', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lead_ids: Array.from(state.selectedLeadIds),
          reason: 'Descarte en lote'
        })
      });
      if (res.ok) {
        showCommercialToast(`${count} prospectos movidos a papelera`);
        clearBatchSelection();
        loadPipelineBoard();
        loadTrashCount();
      }
    } catch (err) {
      showCommercialToast('Error al descartar prospectos');
    }
  }

  // ============================================================================
  // FASE 9: DETECTOR VISUAL DE POSIBLES DUPLICADOS
  // ============================================================================
  async function loadSuspectedDuplicates() {
    try {
      const res = await fetch('/api/v1/deduplication/suspected-duplicates');
      if (res.ok) {
        const data = await res.json();
        state.suspectedPairs = data.suspected_pairs || [];
        state.leadFlags = data.lead_flags || {};

        const dupCounter = document.getElementById('dup-badge-counter');
        if (dupCounter) {
          if (state.suspectedPairs.length > 0) {
            dupCounter.textContent = state.suspectedPairs.length;
            dupCounter.classList.remove('hidden');
          } else {
            dupCounter.classList.add('hidden');
          }
        }
      }
    } catch (err) {
      console.error('Error fetching suspected duplicates:', err);
    }
  }

  function openDuplicateComparison(pairId) {
    const pair = state.suspectedPairs.find(p => p.pair_id === pairId);
    if (!pair) return;

    state.activeSuspectedPair = pair;
    const modal = document.getElementById('modal-merge-duplicate');
    const badge = document.getElementById('dup-similarity-badge');
    const colA = document.getElementById('dup-lead-a-fields');
    const colB = document.getElementById('dup-lead-b-fields');

    if (badge) badge.textContent = `${pair.similarity_pct}% de similitud`;

    const renderFields = (lead) => `
      <div class="compare-field-row">
        <span class="compare-field-label">Nombre Comercial</span>
        <span class="compare-field-value"><strong>${escapeHtml(lead.name)}</strong></span>
      </div>
      <div class="compare-field-row">
        <span class="compare-field-label">Telefono</span>
        <span class="compare-field-value">${escapeHtml(lead.phone_e164 || lead.phone_raw || 'Sin telefono')}</span>
      </div>
      <div class="compare-field-row">
        <span class="compare-field-label">Sitio Web</span>
        <span class="compare-field-value">${lead.website ? escapeHtml(lead.website) : 'Sin web'}</span>
      </div>
      <div class="compare-field-row">
        <span class="compare-field-label">Colonia / Zona</span>
        <span class="compare-field-value">${escapeHtml(lead.suburb || lead.city || 'Tijuana')}</span>
      </div>
      <div class="compare-field-row">
        <span class="compare-field-label">Fase Comercial</span>
        <span class="compare-field-value"><span class="score-badge med">${escapeHtml(lead.lifecycle_stage)}</span></span>
      </div>
    `;

    if (colA) colA.innerHTML = renderFields(pair.lead_a);
    if (colB) colB.innerHTML = renderFields(pair.lead_b);

    if (modal) modal.style.display = 'flex';
  }

  async function resolveDuplicate(action) {
    if (!state.activeSuspectedPair) return;
    const pair = state.activeSuspectedPair;

    try {
      const res = await fetch('/api/v1/deduplication/resolve-suspected', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: action,
          lead_a_id: pair.lead_a.id,
          lead_b_id: pair.lead_b.id,
          master_id: pair.lead_a.id
        })
      });
      if (res.ok) {
        const data = await res.json();
        showCommercialToast(data.message || 'Resuelto exitosamente');
        const modal = document.getElementById('modal-merge-duplicate');
        if (modal) modal.style.display = 'none';
        state.activeSuspectedPair = null;
        await loadSuspectedDuplicates();
        loadPipelineBoard();
      }
    } catch (err) {
      showCommercialToast('Error al resolver duplicado');
    }
  }

  // ============================================================================
  // FASE 9: HISTORIAL DE BUSQUEDAS RECIENTES (1-CLIC RE-SCAN)
  // ============================================================================
  async function loadRecentSearches() {
    const container = document.getElementById('recent-chips-container');
    if (!container) return;
    try {
      const res = await fetch('/api/v1/geo/recent-searches');
      if (res.ok) {
        const searches = await res.json();
        state.recentSearches = searches;
        if (searches.length === 0) {
          container.innerHTML = '<span style="color:var(--text-muted); font-size:11px;">Sin busquedas previas</span>';
        } else {
          container.innerHTML = searches.map(s => `
            <button type="button" class="chip-recent" data-cat="${escapeHtml(s.category)}" data-loc="${escapeHtml(s.location)}">
              ${escapeHtml(s.category)} en ${escapeHtml(s.location)}
            </button>
          `).join('');

          container.querySelectorAll('.chip-recent').forEach(chip => {
            chip.addEventListener('click', () => {
              const cat = chip.dataset.cat;
              const loc = chip.dataset.loc;
              const inCat = document.getElementById('input-search-category');
              const inLoc = document.getElementById('input-search-location');
              if (inCat) inCat.value = cat;
              if (inLoc) inLoc.value = loc;
              const btnRun = document.getElementById('btn-run-search');
              if (btnRun) btnRun.click();
            });
          });
        }
      }
    } catch (err) {
      console.error('Error loading recent searches:', err);
    }
  }

  // ============================================================================
  // FASE 9: WHATSAPP ANGLE SELECTOR (CREATIVE FREEDOM #2)
  // ============================================================================
  function openWhatsAppAngleMenu(lead, triggerEl) {
    state.waAngleLead = lead;
    const menu = document.getElementById('wa-angle-menu');
    if (!menu) return;

    const rect = triggerEl.getBoundingClientRect();
    menu.style.top = `${rect.bottom + 6}px`;
    menu.style.left = `${Math.min(rect.left, window.innerWidth - 240)}px`;
    menu.classList.remove('hidden');
  }

  function handleWhatsAppAngleSelect(angle) {
    const lead = state.waAngleLead;
    if (!lead) return;

    const cleanPhone = (lead.phone_e164 || lead.phone_raw || '').replace(/[^0-9]/g, '');
    if (cleanPhone.length < 10) {
      showCommercialToast('Telefono no valido para WhatsApp');
      return;
    }

    let text = '';
    const leadName = lead.name || 'estimado';

    if (angle === 'ssl') {
      text = `Hola ${leadName}, buen dia. Notamos que el candado de seguridad en su sitio web muestra advertencias a clientes en celular. En Tijuana podemos resolverlo en 24 horas para evitar perder consultas.`;
    } else if (angle === 'mobile') {
      text = `Hola ${leadName}, un gusto saludarle. Al revisar su presencia en linea en Tijuana, vimos que su pagina no esta adaptada a celulares y pierde citas de pacientes o clientes. ¿Tienen disponible unos minutos esta semana?`;
    } else if (angle === 'maps') {
      text = `Hola ${leadName}. Vimos su perfil en mapas de Tijuana con muy buenas opiniones y nos gustaria proponerles enlazar sus citas directamente a este WhatsApp para duplicar prospectos.`;
    } else {
      const template = state.settings.whatsapp_template || 'Hola, buen dia.';
      text = template.replace(/{nombre}/g, leadName);
    }

    logInteraction(lead.id, 'WHATSAPP', `Mensaje enviado con angulo: ${angle}`);
    window.open(`https://wa.me/${cleanPhone}?text=${encodeURIComponent(text)}`, '_blank');

    const menu = document.getElementById('wa-angle-menu');
    if (menu) menu.classList.add('hidden');
    state.waAngleLead = null;
  }

  // ============================================================================
  // FASE 9: QUICK FILTER SOLO-ICON BAR (CREATIVE FREEDOM #3)
  // ============================================================================
  function initQuickFilters() {
    const bar = document.getElementById('quick-filter-icon-bar');
    if (!bar) return;

    bar.querySelectorAll('.btn-filter-icon').forEach(btn => {
      btn.addEventListener('click', () => {
        const filter = btn.dataset.filter;
        if (state.quickFilter === filter) {
          state.quickFilter = null;
          btn.classList.remove('active');
        } else {
          bar.querySelectorAll('.btn-filter-icon').forEach(b => b.classList.remove('active'));
          state.quickFilter = filter;
          btn.classList.add('active');
        }
        if (state.leadViewMode === 'kanban') renderKanbanBoard();
        else if (state.leadViewMode === 'table') renderDenseTable(state.leads);
      });
    });
  }

  // ============================================================================
  // FASE 9: EVENT LISTENERS INITIALIZATION
  // ============================================================================
  function initPhase9EventListeners() {
    // In-App Web Preview Controls
    const btnClosePreview = document.getElementById('preview-close-btn');
    if (btnClosePreview) btnClosePreview.addEventListener('click', closeInAppWebPreview);

    const btnToggleDesktop = document.getElementById('preview-toggle-desktop');
    const btnToggleMobile = document.getElementById('preview-toggle-mobile');
    const deviceFrame = document.getElementById('preview-device-frame');

    if (btnToggleDesktop && deviceFrame) {
      btnToggleDesktop.addEventListener('click', () => {
        btnToggleDesktop.classList.add('active');
        if (btnToggleMobile) btnToggleMobile.classList.remove('active');
        deviceFrame.className = 'device-desktop';
      });
    }

    if (btnToggleMobile && deviceFrame) {
      btnToggleMobile.addEventListener('click', () => {
        btnToggleMobile.classList.add('active');
        if (btnToggleDesktop) btnToggleDesktop.classList.remove('active');
        deviceFrame.className = 'device-mobile';
      });
    }

    const btnReloadPreview = document.getElementById('preview-reload-btn');
    if (btnReloadPreview) {
      btnReloadPreview.addEventListener('click', () => {
        if (state.activePreviewLead && state.activePreviewLead.website) {
          const iframe = document.getElementById('preview-iframe');
          if (iframe) iframe.src = `/api/v1/preview/proxy?url=${encodeURIComponent(state.activePreviewLead.website)}`;
        }
      });
    }

    const btnNotesToggle = document.getElementById('preview-notes-toggle');
    const notepadDrawer = document.getElementById('preview-notepad-drawer');
    const btnNotepadClose = document.getElementById('preview-notepad-close');
    const btnNoteSubmit = document.getElementById('preview-note-submit');

    if (btnNotesToggle && notepadDrawer) {
      btnNotesToggle.addEventListener('click', () => {
        notepadDrawer.classList.toggle('hidden');
        if (!notepadDrawer.classList.contains('hidden')) {
          const input = document.getElementById('preview-note-input');
          if (input) input.focus();
        }
      });
    }

    if (btnNotepadClose && notepadDrawer) {
      btnNotepadClose.addEventListener('click', () => {
        notepadDrawer.classList.add('hidden');
      });
    }

    if (btnNoteSubmit) {
      btnNoteSubmit.addEventListener('click', submitPreviewNote);
    }

    const previewNoteInput = document.getElementById('preview-note-input');
    if (previewNoteInput) {
      previewNoteInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          submitPreviewNote();
        }
      });
    }

    // Popover trigger inside Preview Flaw Pill
    const flawBtn = document.getElementById('preview-flaw-popover-btn');
    const flawPopover = document.getElementById('preview-flaw-popover');
    if (flawBtn && flawPopover) {
      flawBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        flawPopover.classList.toggle('hidden');
      });
      document.addEventListener('click', (e) => {
        if (!flawPopover.contains(e.target) && e.target !== flawBtn) {
          flawPopover.classList.add('hidden');
        }
      });
    }

    // Floating Batch Bar Buttons
    const batchStageBtn = document.getElementById('batch-stage-btn');
    const modalBatchStage = document.getElementById('modal-batch-stage');
    const batchStageConfirmBtn = document.getElementById('batch-stage-confirm-btn');

    if (batchStageBtn && modalBatchStage) {
      batchStageBtn.addEventListener('click', () => {
        modalBatchStage.style.display = 'flex';
      });
    }

    if (batchStageConfirmBtn && modalBatchStage) {
      batchStageConfirmBtn.addEventListener('click', () => {
        const select = document.getElementById('batch-target-stage');
        if (select) {
          batchUpdateStage(select.value);
          modalBatchStage.style.display = 'none';
        }
      });
    }

    const batchTagBtn = document.getElementById('batch-tag-btn');
    const modalBatchTag = document.getElementById('modal-batch-tag');
    const batchTagConfirmBtn = document.getElementById('batch-tag-confirm-btn');

    if (batchTagBtn && modalBatchTag) {
      batchTagBtn.addEventListener('click', () => {
        modalBatchTag.style.display = 'flex';
      });
    }

    if (batchTagConfirmBtn && modalBatchTag) {
      batchTagConfirmBtn.addEventListener('click', () => {
        const actionSel = document.getElementById('batch-tag-action');
        const input = document.getElementById('batch-tag-input');
        if (actionSel && input && input.value.trim()) {
          batchUpdateTags(actionSel.value, input.value.trim());
          modalBatchTag.style.display = 'none';
          input.value = '';
        }
      });
    }

    const batchExportBtn = document.getElementById('batch-export-btn');
    if (batchExportBtn) batchExportBtn.addEventListener('click', batchExport);

    const batchTrashBtn = document.getElementById('batch-trash-btn');
    if (batchTrashBtn) batchTrashBtn.addEventListener('click', batchTrash);

    const batchCancelBtn = document.getElementById('batch-cancel-btn');
    if (batchCancelBtn) batchCancelBtn.addEventListener('click', clearBatchSelection);

    // Table Header Select All
    const thSelectAll = document.getElementById('th-select-all-leads');
    if (thSelectAll) {
      thSelectAll.addEventListener('change', () => {
        const checkboxes = document.querySelectorAll('.lead-select-checkbox');
        checkboxes.forEach(cb => {
          cb.checked = thSelectAll.checked;
          if (thSelectAll.checked) state.selectedLeadIds.add(cb.dataset.leadId);
          else state.selectedLeadIds.delete(cb.dataset.leadId);
        });
        updateBatchBar();
      });
    }

    // Modal close buttons
    document.querySelectorAll('[data-close-modal]').forEach(btn => {
      btn.addEventListener('click', () => {
        const modalId = btn.dataset.closeModal;
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'none';
      });
    });

    // Suspected duplicate modal actions
    const dupMergeBtn = document.getElementById('dup-confirm-merge-btn');
    const dupDistinctBtn = document.getElementById('dup-mark-distinct-btn');
    if (dupMergeBtn) dupMergeBtn.addEventListener('click', () => resolveDuplicate('merge'));
    if (dupDistinctBtn) dupDistinctBtn.addEventListener('click', () => resolveDuplicate('whitelist'));

    // WhatsApp angle menu
    const angleMenu = document.getElementById('wa-angle-menu');
    if (angleMenu) {
      angleMenu.querySelectorAll('.angle-item').forEach(item => {
        item.addEventListener('click', () => {
          handleWhatsAppAngleSelect(item.dataset.angle);
        });
      });
      document.addEventListener('click', (e) => {
        if (!angleMenu.contains(e.target) && !e.target.closest('.btn-wa-angle-trigger')) {
          angleMenu.classList.add('hidden');
        }
      });
    }

    // Quick filters
    initQuickFilters();
  }

  // ==============================================================================
  // FASE 10 EXTENDIDA: FULL PRODUCTIVITY SUITE, SHORTCUTS, PORTALS & LIFECYCLE
  // ==============================================================================

  function recordDailyAction(actionType) {
    const todayKey = 'crm_actions_' + new Date().toISOString().slice(0, 10);
    let count = parseInt(localStorage.getItem(todayKey) || '0', 10);
    count += 1;
    localStorage.setItem(todayKey, count);
    const countEl = document.getElementById('copilot-actions-count');
    if (countEl) countEl.textContent = count;
  }

  function initDailyCopilotCounter() {
    const todayKey = 'crm_actions_' + new Date().toISOString().slice(0, 10);
    let count = parseInt(localStorage.getItem(todayKey) || '0', 10);
    const countEl = document.getElementById('copilot-actions-count');
    if (countEl) countEl.textContent = count;
  }

  function showGlobalPortalPopover(targetEl, text) {
    const portal = document.getElementById('global-portal-popover');
    if (!portal || !text) return;
    portal.textContent = text;
    portal.classList.remove('hidden');

    const rect = targetEl.getBoundingClientRect();
    const popoverRect = portal.getBoundingClientRect();

    let top = rect.top - popoverRect.height - 8;
    if (top < 8) {
      top = rect.bottom + 8;
    }

    let left = rect.left + (rect.width / 2) - (popoverRect.width / 2);
    if (left < 8) left = 8;
    if (left + popoverRect.width > window.innerWidth - 8) {
      left = window.innerWidth - popoverRect.width - 8;
    }

    portal.style.top = `${top}px`;
    portal.style.left = `${left}px`;
  }

  function hideGlobalPortalPopover() {
    const portal = document.getElementById('global-portal-popover');
    if (portal) portal.classList.add('hidden');
  }

  function initGlobalPortalPopovers() {
    document.addEventListener('mouseover', (e) => {
      const trigger = e.target.closest('[data-tooltip], [data-popover]');
      if (trigger) {
        const text = trigger.dataset.tooltip || trigger.dataset.popover;
        if (text) showGlobalPortalPopover(trigger, text);
      }
    });
    document.addEventListener('mouseout', (e) => {
      const trigger = e.target.closest('[data-tooltip], [data-popover]');
      if (trigger) hideGlobalPortalPopover();
    });
  }

  async function loadTodayTrayCount() {
    try {
      const res = await fetch('/api/v1/leads/today/tray');
      if (!res.ok) return;
      const data = await res.json();
      const badge = document.getElementById('badge-today-count');
      if (badge) badge.textContent = data.total_count || 0;
    } catch (e) {
      console.error('[TodayTrayCount] Error:', e);
    }
  }

  async function renderTodayTray(activeFilter) {
    const listEl = document.getElementById('today-tray-items-list');
    const summaryEl = document.getElementById('tray-summary-text');
    if (!listEl) return;

    listEl.innerHTML = '<div style="font-size:12px; color:var(--text-secondary); padding:10px;">Cargando pendientes para hoy...</div>';

    try {
      const res = await fetch('/api/v1/leads/today/tray');
      if (!res.ok) {
        listEl.innerHTML = '<div style="font-size:12px; color:var(--badge-red-text); padding:10px;">Error al cargar pendientes.</div>';
        return;
      }
      const data = await res.json();

      const countAll = document.getElementById('tray-count-all');
      const countCal = document.getElementById('tray-count-calendar');
      const countPost = document.getElementById('tray-count-postponed');
      const countStag = document.getElementById('tray-count-stagnant');
      const badgeTop = document.getElementById('badge-today-count');

      if (countAll) countAll.textContent = data.total_count || 0;
      if (countCal) countCal.textContent = data.calendar_count || 0;
      if (countPost) countPost.textContent = data.postponed_count || 0;
      if (countStag) countStag.textContent = data.stagnant_count || 0;
      if (badgeTop) badgeTop.textContent = data.total_count || 0;

      if (summaryEl) {
        summaryEl.textContent = `${data.total_count || 0} pendientes para resolver hoy en Tijuana`;
      }

      let itemsToRender = data.items || [];
      if (activeFilter === 'calendar') itemsToRender = data.calendar_leads || [];
      else if (activeFilter === 'postponed') itemsToRender = data.postponed_leads || [];
      else if (activeFilter === 'stagnant') itemsToRender = data.stagnant_leads || [];

      if (itemsToRender.length === 0) {
        listEl.innerHTML = `
          <div style="text-align:center; padding:30px 10px; color:var(--text-secondary); font-size:12px;">
            <svg style="width:24px;height:24px; margin-bottom:6px; opacity:0.6;" stroke="currentColor" fill="none"><use href="#icon-check-square"/></svg>
            <div>¡Al dia! No hay prospectos pendientes en este filtro para hoy.</div>
          </div>
        `;
        return;
      }

      listEl.innerHTML = '';
      itemsToRender.forEach(lead => {
        let badgeType = 'stagnant';
        let badgeText = 'Estancado';
        if (data.calendar_leads && data.calendar_leads.some(c => c.id === lead.id)) {
          badgeType = 'calendar';
          badgeText = 'Cita Hoy';
        } else if (data.postponed_leads && data.postponed_leads.some(p => p.id === lead.id)) {
          badgeType = 'postponed';
          badgeText = 'Reactivar';
        }

        const cleanPhone = (lead.phone_e164 || lead.phone_raw || '').replace(/[^0-9+]/g, '');
        const waUrl = cleanPhone.length >= 10 ? `https://wa.me/${cleanPhone.replace('+', '')}?text=${encodeURIComponent('Hola, buen día. Le escribo para dar seguimiento a su propuesta comercial en Tijuana.')}` : '';

        const itemEl = document.createElement('div');
        itemEl.className = 'tray-lead-item';
        itemEl.innerHTML = `
          <div class="tray-lead-header">
            <div class="tray-lead-title" title="${escapeHtml(lead.name)}">${escapeHtml(lead.name)}</div>
            <span class="tray-badge-pill ${badgeType}">${badgeText}</span>
          </div>
          <div style="font-size:11px; color:var(--text-secondary); display:flex; justify-content:space-between;">
            <span>${escapeHtml(lead.primary_category || lead.category_slug)}</span>
            <span>Fase: <strong>${escapeHtml(lead.lifecycle_stage)}</strong></span>
          </div>
          <div class="tray-actions-bar">
            <div class="tray-solo-icons">
              ${waUrl && lead.has_whatsapp !== false ? `
                <a href="${waUrl}" target="_blank" class="btn-solo-icon btn-tray-wa" data-tooltip="Abrir WhatsApp" style="width:30px;height:30px;min-width:30px;min-height:30px;">
                  <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-message-circle"/></svg>
                </a>
              ` : `
                <button class="btn-solo-icon disabled" data-tooltip="Sin WhatsApp" style="width:30px;height:30px;min-width:30px;min-height:30px;">
                  <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-phone-off"/></svg>
                </button>
              `}
              ${cleanPhone ? `
                <a href="tel:${cleanPhone}" class="btn-solo-icon btn-tray-call" data-tooltip="Llamar" style="width:30px;height:30px;min-width:30px;min-height:30px;">
                  <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-phone"/></svg>
                </a>
              ` : ''}
              <button type="button" class="btn-solo-icon btn-tray-view" data-tooltip="Ver ficha integral" style="width:30px;height:30px;min-width:30px;min-height:30px;">
                <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-users"/></svg>
              </button>
            </div>
            ${badgeType === 'stagnant' ? `
              <button type="button" class="btn-action btn-tray-revive" style="font-size:10px; height:24px; padding:0 8px; background:var(--bg-app);" title="Generar sugerencia de reactivacion inteligente">
                <svg style="width:11px;height:11px;" stroke="currentColor" fill="none"><use href="#icon-rotate-ccw"/></svg>
                Auto-Reactivar
              </button>
            ` : ''}
          </div>
        `;

        // Wire events inside tray item
        const btnView = itemEl.querySelector('.btn-tray-view');
        if (btnView) {
          btnView.addEventListener('click', () => {
            const modalTray = document.getElementById('modal-today-tray');
            if (modalTray) modalTray.style.display = 'none';
            openLeadDrawer(lead);
          });
        }

        const titleEl = itemEl.querySelector('.tray-lead-title');
        if (titleEl) {
          titleEl.addEventListener('click', () => {
            const modalTray = document.getElementById('modal-today-tray');
            if (modalTray) modalTray.style.display = 'none';
            openLeadDrawer(lead);
          });
        }

        const btnWa = itemEl.querySelector('.btn-tray-wa');
        if (btnWa) {
          btnWa.addEventListener('click', () => recordDailyAction('whatsapp'));
        }

        const btnCall = itemEl.querySelector('.btn-tray-call');
        if (btnCall) {
          btnCall.addEventListener('click', () => recordDailyAction('call'));
        }

        const btnRevive = itemEl.querySelector('.btn-tray-revive');
        if (btnRevive) {
          btnRevive.addEventListener('click', async () => {
            btnRevive.disabled = true;
            try {
              const noteText = `Auto-reactivacion inteligente: Se retoma contacto con ${lead.name} tras periodo inactivo. Enfoque sugerido: propuesta de modernizacion digital local con soporte en Tijuana.`;
              await fetch(`/api/v1/leads/${lead.id}/notes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: noteText, author: 'Auto-Copiloto' })
              });
              recordDailyAction('revive');
              showCommercialToast(`Reactivacion registrada para "${lead.name}"`);
              await renderTodayTray(activeFilter);
              loadPipelineBoard();
            } catch (err) {
              console.error('[AutoRevive] Error:', err);
            }
          });
        }

        listEl.appendChild(itemEl);
      });
    } catch (err) {
      console.error('[RenderTodayTray] Error:', err);
      listEl.innerHTML = '<div style="font-size:12px; color:var(--badge-red-text); padding:10px;">Error de conexion al cargar bandeja.</div>';
    }
  }

  function initPhase10Features() {
    initDailyCopilotCounter();
    initGlobalPortalPopovers();
    loadTodayTrayCount();

    // 1. Manual Lead Registration
    const topBtnNewLead = document.getElementById('top-btn-new-lead');
    const modalNewLead = document.getElementById('modal-new-lead');
    const modalNewLeadClose = document.getElementById('modal-new-lead-close');
    const modalNewLeadCancel = document.getElementById('modal-new-lead-cancel');
    const formNewLead = document.getElementById('form-new-lead');
    const selectCat = document.getElementById('new-lead-cat');
    const inputCatCustom = document.getElementById('new-lead-cat-custom');
    const dupAlert = document.getElementById('lead-dup-alert');
    const dupMsg = document.getElementById('lead-dup-msg');
    const btnDupOpen = document.getElementById('btn-dup-open-existing');

    let pendingDupId = null;

    if (topBtnNewLead && modalNewLead) {
      topBtnNewLead.addEventListener('click', () => {
        if (formNewLead) formNewLead.reset();
        if (dupAlert) dupAlert.style.display = 'none';
        if (inputCatCustom) inputCatCustom.style.display = 'none';
        pendingDupId = null;
        modalNewLead.style.display = 'flex';
        const nameInput = document.getElementById('new-lead-name');
        if (nameInput) nameInput.focus();
      });
    }

    if (modalNewLeadClose && modalNewLead) {
      modalNewLeadClose.addEventListener('click', () => modalNewLead.style.display = 'none');
    }
    if (modalNewLeadCancel && modalNewLead) {
      modalNewLeadCancel.addEventListener('click', () => modalNewLead.style.display = 'none');
    }

    if (selectCat && inputCatCustom) {
      selectCat.addEventListener('change', () => {
        if (selectCat.value === '__new__') {
          inputCatCustom.style.display = 'block';
          inputCatCustom.focus();
        } else {
          inputCatCustom.style.display = 'none';
        }
      });
    }

    if (btnDupOpen) {
      btnDupOpen.addEventListener('click', async () => {
        if (!pendingDupId) return;
        if (modalNewLead) modalNewLead.style.display = 'none';
        try {
          const res = await fetch(`/api/v1/leads/${pendingDupId}`);
          if (res.ok) {
            const lead = await res.json();
            openLeadDrawer(lead);
          }
        } catch (err) {
          console.error('[OpenExisting] Error:', err);
        }
      });
    }

    if (formNewLead) {
      formNewLead.addEventListener('submit', async (e) => {
        e.preventDefault();
        const nameInput = document.getElementById('new-lead-name');
        const phoneInput = document.getElementById('new-lead-phone');
        const webInput = document.getElementById('new-lead-website');
        const emailInput = document.getElementById('new-lead-email');
        const addrInput = document.getElementById('new-lead-address');
        const notesInput = document.getElementById('new-lead-notes');

        const name = nameInput ? nameInput.value.trim() : '';
        const phone = phoneInput ? phoneInput.value.trim() : '';
        const web = webInput ? webInput.value.trim() : '';

        if (!name) {
          showCommercialToast('Por favor ingrese el nombre comercial del negocio.');
          return;
        }
        if (!phone && !web) {
          showCommercialToast('Validacion inteligente: Se requiere al menos un telefono o un sitio web para guardar.');
          return;
        }

        let catSlug = selectCat ? selectCat.value : 'dentistas';
        let primaryCat = catSlug;
        if (catSlug === '__new__' && inputCatCustom && inputCatCustom.value.trim()) {
          primaryCat = inputCatCustom.value.trim();
          catSlug = primaryCat.toLowerCase().replace(/[^a-z0-9]+/g, '-');
        }

        const socials = {
          facebook: document.getElementById('new-lead-fb')?.value.trim() || undefined,
          instagram: document.getElementById('new-lead-ig')?.value.trim() || undefined,
          tiktok: document.getElementById('new-lead-tiktok')?.value.trim() || undefined,
          linkedin: document.getElementById('new-lead-linkedin')?.value.trim() || undefined,
          x: document.getElementById('new-lead-x')?.value.trim() || undefined,
          youtube: document.getElementById('new-lead-yt')?.value.trim() || undefined,
        };

        const payload = {
          name: name,
          category_slug: catSlug,
          primary_category: primaryCat,
          phone_raw: phone || undefined,
          website: web || undefined,
          email: emailInput ? emailInput.value.trim() || undefined : undefined,
          address_raw: addrInput ? addrInput.value.trim() || 'Tijuana, BC' : 'Tijuana, BC',
          notes: notesInput ? notesInput.value.trim() || undefined : undefined,
          social_links: socials
        };

        try {
          const res = await fetch('/api/v1/leads', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });

          if (res.status === 409) {
            const errData = await res.json();
            const detail = errData.detail || {};
            pendingDupId = detail.existing_lead_id || (detail.conflict && detail.conflict.existing_lead && detail.conflict.existing_lead.id);
            const conflictName = detail.existing_name || 'Negocio existente';
            if (dupAlert) {
              dupAlert.style.display = 'block';
              if (dupMsg) dupMsg.textContent = `Ya existe "${conflictName}" registrado con el mismo identificador.`;
            }
            return;
          }

          if (res.ok) {
            const data = await res.json();
            modalNewLead.style.display = 'none';
            recordDailyAction('lead_created');
            showCommercialToast(`Prospecto "${name}" guardado exitosamente`);
            await loadPipelineBoard();
            if (data.id) {
              const leadRes = await fetch(`/api/v1/leads/${data.id}`);
              if (leadRes.ok) {
                const savedLead = await leadRes.json();
                openLeadDrawer(savedLead);
              }
            }
          } else {
            showCommercialToast('No se pudo guardar el prospecto.');
          }
        } catch (err) {
          console.error('[CreateLead] Error:', err);
        }
      });
    }

    // 2. In-Line Drawer Form Submit
    const formDrawerEdit = document.getElementById('form-drawer-inline-edit');
    if (formDrawerEdit) {
      formDrawerEdit.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!state.selectedLead) return;

        const editName = document.getElementById('edit-drawer-name');
        const editCat = document.getElementById('edit-drawer-cat');
        const editPhone = document.getElementById('edit-drawer-phone');
        const editWeb = document.getElementById('edit-drawer-website');
        const editEmail = document.getElementById('edit-drawer-email');
        const editAddr = document.getElementById('edit-drawer-address');

        const socials = {
          facebook: document.getElementById('edit-drawer-fb')?.value.trim() || undefined,
          instagram: document.getElementById('edit-drawer-ig')?.value.trim() || undefined,
          tiktok: document.getElementById('edit-drawer-tiktok')?.value.trim() || undefined,
          linkedin: document.getElementById('edit-drawer-linkedin')?.value.trim() || undefined,
          x: document.getElementById('edit-drawer-x')?.value.trim() || undefined,
          youtube: document.getElementById('edit-drawer-yt')?.value.trim() || undefined,
        };

        const payload = {
          name: editName ? editName.value.trim() : undefined,
          category_slug: editCat ? editCat.value : undefined,
          phone_raw: editPhone ? editPhone.value.trim() : undefined,
          website: editWeb ? editWeb.value.trim() : undefined,
          email: editEmail ? editEmail.value.trim() : undefined,
          address_raw: editAddr ? editAddr.value.trim() : undefined,
          social_links: socials
        };

        try {
          const res = await fetch(`/api/v1/leads/${state.selectedLead.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          if (res.ok) {
            Object.assign(state.selectedLead, payload);
            if (drawerLeadName) drawerLeadName.textContent = state.selectedLead.name;
            if (drawerLeadCategory) drawerLeadCategory.textContent = `${state.selectedLead.primary_category || state.selectedLead.category_slug} • Tijuana, BC`;
            recordDailyAction('edit');
            showCommercialToast('Modificaciones guardadas en la base de datos');
            loadPipelineBoard();
          }
        } catch (err) {
          console.error('[InlineEdit] Error:', err);
        }
      });
    }

    // 3. "Para Hoy" Tray Modal & Tab Filters
    const btnTrayToday = document.getElementById('btn-tray-today');
    const modalTodayTray = document.getElementById('modal-today-tray');
    const modalTodayTrayClose = document.getElementById('modal-today-tray-close');
    const btnTrayLaunchFocus = document.getElementById('btn-tray-launch-focus');

    let currentTrayFilter = 'all';

    if (btnTrayToday && modalTodayTray) {
      btnTrayToday.addEventListener('click', async () => {
        modalTodayTray.style.display = 'flex';
        currentTrayFilter = 'all';
        document.querySelectorAll('.tray-tabs-strip .filter-btn').forEach(btn => {
          btn.classList.toggle('active', btn.dataset.trayFilter === 'all');
        });
        await renderTodayTray('all');
      });
    }

    if (modalTodayTrayClose && modalTodayTray) {
      modalTodayTrayClose.addEventListener('click', () => modalTodayTray.style.display = 'none');
    }

    document.querySelectorAll('.tray-tabs-strip .filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tray-tabs-strip .filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTrayFilter = btn.dataset.trayFilter;
        renderTodayTray(currentTrayFilter);
      });
    });

    if (btnTrayLaunchFocus) {
      btnTrayLaunchFocus.addEventListener('click', () => {
        if (modalTodayTray) modalTodayTray.style.display = 'none';
        const btnToggleFocus = document.getElementById('btn-toggle-focus');
        if (btnToggleFocus) btnToggleFocus.click();
      });
    }

    // 4. Importer Dialog
    const btnOpenImport = document.getElementById('btn-open-import');
    const modalImport = document.getElementById('modal-import-leads');
    const modalImportClose = document.getElementById('modal-import-close');
    const btnImportCancel = document.getElementById('btn-import-cancel');
    const btnImportExecute = document.getElementById('btn-import-execute');
    const inputImportFile = document.getElementById('input-import-file');
    const textareaImportRaw = document.getElementById('textarea-import-raw');
    const importPreviewStatus = document.getElementById('import-preview-status');

    if (btnOpenImport && modalImport) {
      btnOpenImport.addEventListener('click', () => {
        modalImport.style.display = 'flex';
        if (textareaImportRaw) textareaImportRaw.value = '';
        if (inputImportFile) inputImportFile.value = '';
        if (importPreviewStatus) importPreviewStatus.textContent = 'Listo para importar.';
      });
    }
    if (modalImportClose && modalImport) {
      modalImportClose.addEventListener('click', () => modalImport.style.display = 'none');
    }
    if (btnImportCancel && modalImport) {
      btnImportCancel.addEventListener('click', () => modalImport.style.display = 'none');
    }

    if (inputImportFile) {
      inputImportFile.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
          if (textareaImportRaw) textareaImportRaw.value = event.target.result;
          if (importPreviewStatus) importPreviewStatus.textContent = `Archivo cargado: ${file.name} (${Math.round(file.size / 1024)} KB)`;
        };
        reader.readAsText(file);
      });
    }

    if (btnImportExecute) {
      btnImportExecute.addEventListener('click', async () => {
        const raw = textareaImportRaw ? textareaImportRaw.value.trim() : '';
        if (!raw) {
          showCommercialToast('Por favor cargue un archivo o pegue datos para importar.');
          return;
        }

        let parsedItems = [];
        if (raw.startsWith('[') || raw.startsWith('{')) {
          try {
            const parsed = JSON.parse(raw);
            parsedItems = Array.isArray(parsed) ? parsed : [parsed];
          } catch (err) {
            showCommercialToast('Error de sintaxis JSON en los datos provistos.');
            return;
          }
        } else {
          // Parse CSV
          const lines = raw.split(/\r?\n/).filter(l => l.trim().length > 0);
          if (lines.length === 0) return;
          const header = lines[0].split(',').map(h => h.trim().toLowerCase());
          for (let i = 1; i < lines.length; i++) {
            const cols = lines[i].split(',').map(c => c.trim().replace(/^["']|["']$/g, ''));
            if (cols.length === 0 || !cols[0]) continue;
            parsedItems.push({
              name: cols[0] || 'Contacto Importado',
              category_slug: cols[1] || 'dentistas',
              phone_raw: cols[2] || undefined,
              website: cols[3] || undefined,
              email: cols[4] || undefined,
              address_raw: cols[5] || 'Tijuana, BC'
            });
          }
        }

        if (parsedItems.length === 0) {
          showCommercialToast('No se encontraron registros validos para procesar.');
          return;
        }

        btnImportExecute.disabled = true;
        btnImportExecute.textContent = 'Importando...';

        try {
          const res = await fetch('/api/v1/leads/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ leads: parsedItems })
          });
          if (res.ok) {
            const summary = await res.json();
            showCommercialToast(`Importacion completada: ${summary.imported} guardados, ${summary.duplicates_skipped} duplicados omitidos`);
            if (modalImport) modalImport.style.display = 'none';
            await loadPipelineBoard();
            recordDailyAction('import');
          } else {
            showCommercialToast('Error al ejecutar la importacion en el servidor.');
          }
        } catch (err) {
          console.error('[Import] Error:', err);
        } finally {
          btnImportExecute.disabled = false;
          btnImportExecute.textContent = 'Iniciar Importacion';
        }
      });
    }

    // 5. Exporter Dialog
    const btnOpenExport = document.getElementById('btn-open-export');
    const modalExport = document.getElementById('modal-export-leads');
    const modalExportClose = document.getElementById('modal-export-close');
    const btnExportCancel = document.getElementById('btn-export-cancel');
    const btnExportExecute = document.getElementById('btn-export-execute');
    const selectExportFormat = document.getElementById('select-export-format');
    const selectExportScope = document.getElementById('select-export-scope');

    if (btnOpenExport && modalExport) {
      btnOpenExport.addEventListener('click', () => {
        modalExport.style.display = 'flex';
      });
    }
    if (modalExportClose && modalExport) {
      modalExportClose.addEventListener('click', () => modalExport.style.display = 'none');
    }
    if (btnExportCancel && modalExport) {
      btnExportCancel.addEventListener('click', () => modalExport.style.display = 'none');
    }

    if (btnExportExecute) {
      btnExportExecute.addEventListener('click', () => {
        const fmt = selectExportFormat ? selectExportFormat.value : 'csv';
        const scope = selectExportScope ? selectExportScope.value : 'all';
        let url = `/api/v1/leads/export?format=${fmt}`;
        if (scope === 'filtered' && state.selectedCategory) {
          url += `&category_slug=${encodeURIComponent(state.selectedCategory)}`;
        }
        window.open(url, '_blank');
        if (modalExport) modalExport.style.display = 'none';
        recordDailyAction('export');
        showCommercialToast(`Exportando archivo en formato ${fmt.toUpperCase()}...`);
      });
    }

    // 6. Fast Keyboard Shortcuts (Directive 4.4)
    const btnShortcutsInfo = document.getElementById('btn-shortcuts-info');
    const modalShortcuts = document.getElementById('modal-shortcuts-guide');
    const modalShortcutsClose = document.getElementById('modal-shortcuts-close');
    const btnShortcutsOk = document.getElementById('btn-shortcuts-ok');

    if (btnShortcutsInfo && modalShortcuts) {
      btnShortcutsInfo.addEventListener('click', () => {
        modalShortcuts.style.display = 'flex';
      });
    }
    if (modalShortcutsClose && modalShortcuts) {
      modalShortcutsClose.addEventListener('click', () => modalShortcuts.style.display = 'none');
    }
    if (btnShortcutsOk && modalShortcuts) {
      btnShortcutsOk.addEventListener('click', () => modalShortcuts.style.display = 'none');
    }

    window.addEventListener('keydown', (e) => {
      const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
      const isInput = activeTag === 'input' || activeTag === 'textarea' || activeTag === 'select';

      // Ctrl + K or '/' when not typing
      if ((e.ctrlKey && e.key.toLowerCase() === 'k') || (!isInput && e.key === '/')) {
        e.preventDefault();
        const globalSearchBtn = document.getElementById('top-btn-global-search');
        if (globalSearchBtn) globalSearchBtn.click();
        return;
      }

      // Esc closes modals, drawer, preview
      if (e.key === 'Escape') {
        const drawer = document.getElementById('drawer-lead-detail');
        if (drawer && drawer.style.display === 'flex') {
          drawer.style.display = 'none';
          return;
        }
        const preview = document.getElementById('in-app-web-preview');
        if (preview && !preview.classList.contains('hidden')) {
          preview.classList.add('hidden');
          document.body.classList.remove('preview-open');
          return;
        }
        document.querySelectorAll('.modal-backdrop').forEach(m => {
          if (m.style.display === 'flex' || m.style.display === 'block') {
            m.style.display = 'none';
          }
        });
        return;
      }

      if (isInput) return;

      // Views Navigation: 1, 2, 3
      if (e.key === '1') {
        const btnLeads = document.getElementById('nav-btn-leads');
        if (btnLeads) btnLeads.click();
      } else if (e.key === '2') {
        const btnMap = document.getElementById('nav-btn-map');
        if (btnMap) btnMap.click();
      } else if (e.key === '3') {
        const btnCal = document.getElementById('nav-btn-calendar');
        if (btnCal) btnCal.click();
      }

      // Actions on active selected lead
      if (state.selectedLead) {
        if (e.key.toLowerCase() === 'c') {
          copyCommercialPitch(state.selectedLead);
        } else if (e.key.toLowerCase() === 'n') {
          const notesTab = document.querySelector('.drawer-tab-btn[data-tab="tab-notes"]');
          if (notesTab) notesTab.click();
          const noteInput = document.getElementById('drawer-note-content');
          if (noteInput) noteInput.focus();
        } else if (e.key.toLowerCase() === 'w') {
          const cleanPhone = (state.selectedLead.phone_e164 || state.selectedLead.phone_raw || '').replace(/[^0-9]/g, '');
          if (cleanPhone.length >= 10 && state.selectedLead.has_whatsapp !== false) {
            window.open(`https://wa.me/${cleanPhone}`, '_blank');
            recordDailyAction('whatsapp');
          }
        }
      }
    });
  }

  // Start initial loads
  initLiveReload();
  initEventStream();
  loadInitialData();
  initPhase9EventListeners();
  initPhase10Features();
  checkSecurityLock();
  checkOnboardingInitial();
});
