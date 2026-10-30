// CONTINUUM Main Client-Side Controller
// Professional Research-Project Dashboard Orchestrator & Telemetry Sync

document.addEventListener('DOMContentLoaded', () => {
    // -----------------------------------------------------------------
    // 1. DOM Elements
    // -----------------------------------------------------------------
    const codeEditor = document.getElementById('codeEditor');
    const lineNumbers = document.getElementById('lineNumbers');
    const charCount = document.getElementById('charCount');
    const compilerFlags = document.getElementById('compilerFlags');
    const stdinData = document.getElementById('stdinData');
    const btnClearStdin = document.getElementById('btnClearStdin');
    const stdinWaitingMsg = document.getElementById('stdinWaitingMsg');
    const timeoutSeconds = document.getElementById('timeoutSeconds');
    const chkSimulateKaliEnv = document.getElementById('chkSimulateKaliEnv');
    const chkSimulateParrotDown = document.getElementById('chkSimulateParrotDown');
    const btnRunProgram = document.getElementById('btnRunProgram');
    const btnExample = document.getElementById('btnExample');
    const btnClearEditor = document.getElementById('btnClearEditor');
    const sampleSelect = document.getElementById('sampleSelect');
    const fileTag = document.getElementById('fileTag');
    
    // Header Agent Status Chips
    const badgeKali = document.getElementById('badgeKali');
    const textStatusKali = document.getElementById('textStatusKali');
    const urlKaliDisplay = document.getElementById('urlKaliDisplay');
    const badgeParrot = document.getElementById('badgeParrot');
    const textStatusParrot = document.getElementById('textStatusParrot');
    const urlParrotDisplay = document.getElementById('urlParrotDisplay');
    const btnRefreshAgents = document.getElementById('btnRefreshAgents');
    
    // Theme Toggle
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const sunIcon = themeToggleBtn ? themeToggleBtn.querySelector('.sun-icon') : null;
    const moonIcon = themeToggleBtn ? themeToggleBtn.querySelector('.moon-icon') : null;

    // Pipeline elements
    const nodeWindows = document.getElementById('nodeWindows');
    const nodeKali = document.getElementById('nodeKali');
    const nodeParrot = document.getElementById('nodeParrot');
    const nodeOutput = document.getElementById('nodeOutput');
    const wireKali = document.getElementById('wireKali');
    const wireFailover = document.getElementById('wireFailover');
    const wireOutput = document.getElementById('wireOutput');
    const pipelineStatusText = document.getElementById('pipelineStatusText');
    const wireFailoverBadge = document.getElementById('wireFailoverBadge');
    const nodeKaliEnv = nodeKali ? nodeKali.querySelector('.node-env') : null;
    const nodeParrotEnv = nodeParrot ? nodeParrot.querySelector('.node-env') : null;
    const nodeOutputEnv = document.getElementById('nodeOutputEnv');
    
    // Result HUD elements
    const hudJobId = document.getElementById('hudJobId');
    const hudTarget = document.getElementById('hudTarget');
    const hudStatus = document.getElementById('hudStatus');
    const hudExitCode = document.getElementById('hudExitCode');
    const hudExitLatency = document.getElementById('hudExitLatency');
    const hudMigrationStatus = document.getElementById('hudMigrationStatus');
    const hudLatencyTime = document.getElementById('hudLatencyTime');
    
    // Console & Timeline elements
    const timelineContainer = document.getElementById('timelineContainer');
    const timelineCount = document.getElementById('timelineCount');
    const consoleBody = document.getElementById('consoleBody');
    const consoleTabs = document.querySelectorAll('.console-tab');
    
    // Jobs Tables & Metrics
    const jobsTableBody = document.getElementById('jobsTableBody');
    const jobsTableBodyFull = document.getElementById('jobsTableBodyFull');
    const btnRefreshJobs = document.getElementById('btnRefreshJobs');
    const btnRefreshJobsFull = document.getElementById('btnRefreshJobsFull');
    const metricTotalJobs = document.getElementById('metricTotalJobs');
    const metricKaliSuccess = document.getElementById('metricKaliSuccess');
    const metricParrotMigrated = document.getElementById('metricParrotMigrated');
    const metricErrors = document.getElementById('metricErrors');
    
    // View 1 Status Cards (Kali & Parrot)
    const cardKaliBadge = document.getElementById('cardKaliBadge');
    const cardKaliEndpoint = document.getElementById('cardKaliEndpoint');
    const cardKaliLatency = document.getElementById('cardKaliLatency');
    const cardParrotBadge = document.getElementById('cardParrotBadge');
    const cardParrotEndpoint = document.getElementById('cardParrotEndpoint');
    const cardParrotLatency = document.getElementById('cardParrotLatency');

    // Sidebar & View Navigation Elements
    const navItems = document.querySelectorAll('.nav-item');
    const viewSections = document.querySelectorAll('.view-section');
    const topNavLinks = document.querySelectorAll('.top-nav-link');
    const btnToggleSidebar = document.getElementById('btnToggleSidebar');
    const sidebar = document.getElementById('sidebar');
    const navSidebarStatusDot = document.getElementById('navSidebarStatusDot');
    const sidebarKaliDot = document.getElementById('sidebarKaliDot');
    const sidebarKaliText = document.getElementById('sidebarKaliText');
    const sidebarParrotDot = document.getElementById('sidebarParrotDot');
    const sidebarParrotText = document.getElementById('sidebarParrotText');

    // System Status View Elements
    const btnRefreshStatusView = document.getElementById('btnRefreshStatusView');
    const btnTestKaliPing = document.getElementById('btnTestKaliPing');
    const btnTestParrotPing = document.getElementById('btnTestParrotPing');
    const statusViewBadgeKali = document.getElementById('statusViewBadgeKali');
    const statusViewUrlKali = document.getElementById('statusViewUrlKali');
    const statusViewLatencyKali = document.getElementById('statusViewLatencyKali');
    const statusViewBadgeParrot = document.getElementById('statusViewBadgeParrot');
    const statusViewUrlParrot = document.getElementById('statusViewUrlParrot');
    const statusViewLatencyParrot = document.getElementById('statusViewLatencyParrot');
    const routeKaliNode = document.getElementById('routeKaliNode');
    const routeParrotNode = document.getElementById('routeParrotNode');
    const failoverRouteStatus = document.getElementById('failoverRouteStatus');

    // Settings Modal & View Elements
    const settingsModal = document.getElementById('settingsModal');
    const btnOpenSettings = document.getElementById('btnOpenSettings');
    const btnCloseSettingsModal = document.getElementById('btnCloseSettingsModal');
    const btnCancelSettings = document.getElementById('btnCancelSettings');
    const btnSaveSettings = document.getElementById('btnSaveSettings');
    const inputKaliUrl = document.getElementById('inputKaliUrl');
    const inputParrotUrl = document.getElementById('inputParrotUrl');
    const settingsViewKaliUrl = document.getElementById('settingsViewKaliUrl');
    const settingsViewParrotUrl = document.getElementById('settingsViewParrotUrl');
    const btnSaveViewSettings = document.getElementById('btnSaveViewSettings');
    const btnPresetHostOnly = document.getElementById('btnPresetHostOnly');
    const btnPresetLocalhost = document.getElementById('btnPresetLocalhost');
    const selectPollInterval = document.getElementById('selectPollInterval');
    const selectEditorFontSize = document.getElementById('selectEditorFontSize');
    const chkAutoScrollConsole = document.getElementById('chkAutoScrollConsole');

    // Failover Confirmation Modal & Banner Elements
    const failoverModal = document.getElementById('failoverModal');
    const btnCloseFailoverModal = document.getElementById('btnCloseFailoverModal');
    const btnStayOnKali = document.getElementById('btnStayOnKali');
    const btnMigrateToParrot = document.getElementById('btnMigrateToParrot');
    const failoverFailureReason = document.getElementById('failoverFailureReason');
    const failoverConfirmationBanner = document.getElementById('failoverConfirmationBanner');
    const inlineFailureDetails = document.getElementById('inlineFailureDetails');
    const btnBannerStayKali = document.getElementById('btnBannerStayKali');
    const btnBannerMigrateParrot = document.getElementById('btnBannerMigrateParrot');

    // -----------------------------------------------------------------
    // 2. State Management
    // -----------------------------------------------------------------
    let currentJob = null;
    let activeConsoleTab = 'stdout';
    let isCustomCode = false;
    let pollIntervalMs = 10000;
    let pollTimer = null;
    let autoScrollConsole = true;
    const sampleKeys = ['normal', 'failover', 'syntax_error', 'parrot_down', 'timeout', 'interactive_stdin', 'scanf_sum'];
    let currentSampleIndex = 0;

    // -----------------------------------------------------------------
    // 3. Theme Toggle (Light / Dark)
    // -----------------------------------------------------------------
    function applyTheme(isDark) {
        if (isDark) {
            document.body.classList.add('dark-theme');
            document.body.classList.remove('light-theme');
            if (sunIcon) sunIcon.style.display = 'none';
            if (moonIcon) moonIcon.style.display = 'block';
        } else {
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
            if (sunIcon) sunIcon.style.display = 'block';
            if (moonIcon) moonIcon.style.display = 'none';
        }
    }

    const savedTheme = localStorage.getItem('continuum_theme');
    if (savedTheme === 'dark') {
        applyTheme(true);
    } else {
        applyTheme(false); // Default clean light dashboard
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const isDarkNow = document.body.classList.contains('dark-theme');
            applyTheme(!isDarkNow);
            localStorage.setItem('continuum_theme', !isDarkNow ? 'dark' : 'light');
        });
    }

    // -----------------------------------------------------------------
    // 4. Navigation & View Switching
    // -----------------------------------------------------------------
    function switchView(viewId) {
        if (!document.getElementById(viewId)) return;

        viewSections.forEach(sec => {
            sec.classList.toggle('active', sec.id === viewId);
        });

        navItems.forEach(item => {
            item.classList.toggle('active', item.dataset.view === viewId);
        });

        // Sync Top Navigation links highlight
        if (topNavLinks) {
            topNavLinks.forEach(lnk => lnk.classList.remove('active'));
            if (viewId === 'viewExecute') {
                const homeLink = document.getElementById('topNavHome');
                if (homeLink) homeLink.classList.add('active');
            } else if (viewId === 'viewAbout') {
                const aboutLink = document.getElementById('topNavAbout');
                if (aboutLink) aboutLink.classList.add('active');
            } else if (viewId === 'viewHistory') {
                const histLink = document.getElementById('topNavHistory');
                if (histLink) histLink.classList.add('active');
            }
        }

        // Close mobile drawer
        if (window.innerWidth <= 992 && sidebar) {
            sidebar.classList.remove('open');
        }

        if (viewId === 'viewExecute') {
            updateLineNumbers();
        } else if (viewId === 'viewHistory') {
            loadJobsHistory();
        } else if (viewId === 'viewStatus') {
            checkAgents();
        } else if (viewId === 'viewSettings') {
            syncSettingsInputs();
        }
    }

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const viewId = item.dataset.view;
            if (viewId) switchView(viewId);
        });
    });

    // Top Navigation Link handlers
    const topNavHome = document.getElementById('topNavHome');
    const topNavAbout = document.getElementById('topNavAbout');
    const topNavHistory = document.getElementById('topNavHistory');
    const topNavDoc = document.getElementById('topNavDoc');

    if (topNavHome) topNavHome.addEventListener('click', () => switchView('viewExecute'));
    if (topNavAbout) topNavAbout.addEventListener('click', () => switchView('viewAbout'));
    if (topNavHistory) topNavHistory.addEventListener('click', () => switchView('viewHistory'));
    if (topNavDoc) topNavDoc.addEventListener('click', () => switchView('viewAbout'));

    if (btnToggleSidebar) {
        btnToggleSidebar.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // -----------------------------------------------------------------
    // 5. Line Numbers & Code Editor Controls
    // -----------------------------------------------------------------
    function updateLineNumbers() {
        if (!codeEditor || !lineNumbers) return;
        const lines = codeEditor.value.split('\n').length;
        if (charCount) {
            charCount.textContent = `${lines} line${lines === 1 ? '' : 's'} (${codeEditor.value.length} chars)`;
        }
        let numsHtml = '';
        for (let i = 1; i <= lines; i++) {
            numsHtml += i + '<br>';
        }
        lineNumbers.innerHTML = numsHtml;
    }

    codeEditor.addEventListener('input', () => {
        isCustomCode = true;
        document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
        if (fileTag) fileTag.textContent = 'program.c (custom)';
        updateLineNumbers();
    });

    codeEditor.addEventListener('scroll', () => {
        lineNumbers.scrollTop = codeEditor.scrollTop;
    });

    // Support Tab key in editor
    codeEditor.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = codeEditor.selectionStart;
            const end = codeEditor.selectionEnd;
            codeEditor.value = codeEditor.value.substring(0, start) + '    ' + codeEditor.value.substring(end);
            codeEditor.selectionStart = codeEditor.selectionEnd = start + 4;
            updateLineNumbers();
        }
    });

    // Clear Editor Button
    if (btnClearEditor) {
        btnClearEditor.addEventListener('click', () => {
            codeEditor.value = '';
            if (stdinData) stdinData.value = '';
            updateLineNumbers();
            if (fileTag) fileTag.textContent = 'program.c (empty)';
            document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
        });
    }

    // Clear Stdin Input Button
    if (btnClearStdin) {
        btnClearStdin.addEventListener('click', () => {
            if (stdinData) {
                stdinData.value = '';
                stdinData.focus();
            }
        });
    }

    // Example Button: cycles through sample programs
    if (btnExample) {
        btnExample.addEventListener('click', () => {
            currentSampleIndex = (currentSampleIndex + 1) % sampleKeys.length;
            const key = sampleKeys[currentSampleIndex];
            sampleSelect.value = key;
            loadPreset(key);
        });
    }

    // -----------------------------------------------------------------
    // 6. Load Presets & Test Cases
    // -----------------------------------------------------------------
    function loadPreset(key) {
        if (typeof SAMPLES === 'undefined') return;
        const s = SAMPLES[key];
        if (!s) return;
        
        codeEditor.value = s.code;
        compilerFlags.value = (s.flags || ["-Wall", "-O2"]).join(' ');
        stdinData.value = s.stdin || "";
        timeoutSeconds.value = s.timeout || 10;
        chkSimulateKaliEnv.checked = !!s.simulate_kali_env;
        chkSimulateParrotDown.checked = !!s.simulate_parrot_offline;
        updateLineNumbers();
        
        // Update active preset button highlight
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.preset === key);
        });
        
        isCustomCode = false;
        resetPipeline();
        if (fileTag) fileTag.textContent = 'program.c';
        pipelineStatusText.textContent = `Preset loaded: ${s.title}`;
    }

    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const presetKey = btn.dataset.preset;
            sampleSelect.value = presetKey;
            loadPreset(presetKey);
        });
    });

    sampleSelect.addEventListener('change', (e) => {
        loadPreset(e.target.value);
    });

    // Test Cases View Load/Run buttons
    document.querySelectorAll('.btn-load-test').forEach(btn => {
        btn.addEventListener('click', () => {
            const presetKey = btn.dataset.preset;
            sampleSelect.value = presetKey;
            loadPreset(presetKey);
            switchView('viewExecute');
        });
    });

    document.querySelectorAll('.btn-run-test').forEach(btn => {
        btn.addEventListener('click', () => {
            const presetKey = btn.dataset.preset;
            sampleSelect.value = presetKey;
            loadPreset(presetKey);
            switchView('viewExecute');
            setTimeout(() => {
                btnRunProgram.click();
            }, 100);
        });
    });

    // -----------------------------------------------------------------
    // 7. Agent Health Monitor & Telemetry Sync
    // -----------------------------------------------------------------
    async function checkAgents() {
        try {
            const res = await fetch('/api/health/agents');
            if (!res.ok) throw new Error('Health check error');
            const data = await res.json();
            
            let kaliOnline = false;
            let parrotOnline = false;

            data.forEach(a => {
                const isOnline = a.status === 'online';
                if (a.agent_id.includes('kali')) {
                    kaliOnline = isOnline;
                    
                    // Header chip
                    if (badgeKali) badgeKali.className = `status-indicator-dot ${isOnline ? 'online' : 'offline'}`;
                    if (textStatusKali) textStatusKali.textContent = a.status.toUpperCase();
                    if (urlKaliDisplay) urlKaliDisplay.textContent = a.base_url;
                    inputKaliUrl.value = a.base_url;
                    if (settingsViewKaliUrl) settingsViewKaliUrl.value = a.base_url;

                    // View 1 Status card
                    if (cardKaliBadge) {
                        cardKaliBadge.className = `badge ${isOnline ? 'online' : 'offline'}`;
                        cardKaliBadge.textContent = a.status.toUpperCase();
                    }
                    if (cardKaliEndpoint) cardKaliEndpoint.textContent = a.base_url;
                    if (cardKaliLatency) cardKaliLatency.textContent = `${a.latency_ms} ms`;

                    // View 3 System status view
                    if (statusViewBadgeKali) {
                        statusViewBadgeKali.className = `badge ${isOnline ? 'online' : 'offline'}`;
                        statusViewBadgeKali.textContent = a.status.toUpperCase();
                    }
                    if (statusViewUrlKali) statusViewUrlKali.textContent = a.base_url;
                    if (statusViewLatencyKali) statusViewLatencyKali.textContent = `${a.latency_ms} ms`;

                    // Sidebar
                    if (sidebarKaliDot) sidebarKaliDot.className = `telemetry-dot ${isOnline ? 'online' : ''}`;
                    if (sidebarKaliText) sidebarKaliText.textContent = a.status.toUpperCase();
                    if (routeKaliNode) routeKaliNode.className = `pipeline-node ${isOnline ? 'active' : 'failed'}`;

                } else if (a.agent_id.includes('parrot')) {
                    parrotOnline = isOnline;
                    
                    // Header chip
                    if (badgeParrot) badgeParrot.className = `status-indicator-dot ${isOnline ? 'online' : 'offline'}`;
                    if (textStatusParrot) textStatusParrot.textContent = a.status.toUpperCase();
                    if (urlParrotDisplay) urlParrotDisplay.textContent = a.base_url;
                    inputParrotUrl.value = a.base_url;
                    if (settingsViewParrotUrl) settingsViewParrotUrl.value = a.base_url;

                    // View 1 Status card
                    if (cardParrotBadge) {
                        cardParrotBadge.className = `badge ${isOnline ? 'online' : 'offline'}`;
                        cardParrotBadge.textContent = a.status.toUpperCase();
                    }
                    if (cardParrotEndpoint) cardParrotEndpoint.textContent = a.base_url;
                    if (cardParrotLatency) cardParrotLatency.textContent = `${a.latency_ms} ms`;

                    // View 3 System status view
                    if (statusViewBadgeParrot) {
                        statusViewBadgeParrot.className = `badge ${isOnline ? 'online' : 'offline'}`;
                        statusViewBadgeParrot.textContent = a.status.toUpperCase();
                    }
                    if (statusViewUrlParrot) statusViewUrlParrot.textContent = a.base_url;
                    if (statusViewLatencyParrot) statusViewLatencyParrot.textContent = `${a.latency_ms} ms`;

                    // Sidebar
                    if (sidebarParrotDot) sidebarParrotDot.className = `telemetry-dot ${isOnline ? 'online' : ''}`;
                    if (sidebarParrotText) sidebarParrotText.textContent = a.status.toUpperCase();
                    if (routeParrotNode) routeParrotNode.className = `pipeline-node ${isOnline ? 'active' : 'failed'}`;
                }
            });

            // Overall status in sidebar
            if (navSidebarStatusDot) {
                if (kaliOnline && parrotOnline) {
                    navSidebarStatusDot.className = 'nav-status-dot online';
                } else if (kaliOnline || parrotOnline) {
                    navSidebarStatusDot.className = 'nav-status-dot degraded';
                } else {
                    navSidebarStatusDot.className = 'nav-status-dot';
                }
            }

            if (failoverRouteStatus) {
                if (kaliOnline && parrotOnline) {
                    failoverRouteStatus.textContent = 'Active • Both Kali Primary & Parrot Backup VMs Ready for Failover';
                    failoverRouteStatus.style.color = 'var(--success-color)';
                } else if (kaliOnline) {
                    failoverRouteStatus.textContent = 'Warning • Kali Primary VM Online, Parrot Backup VM Offline';
                    failoverRouteStatus.style.color = 'var(--warning-color)';
                } else if (parrotOnline) {
                    failoverRouteStatus.textContent = 'Degraded • Kali Primary Offline, Parrot Standby Online';
                    failoverRouteStatus.style.color = 'var(--warning-color)';
                } else {
                    failoverRouteStatus.textContent = 'Offline • Both Virtual Machines Unreachable';
                    failoverRouteStatus.style.color = 'var(--danger-color)';
                }
            }

        } catch (err) {
            console.error('Agent health probe error:', err);
            if (badgeKali) badgeKali.className = 'status-indicator-dot offline';
            if (textStatusKali) textStatusKali.textContent = 'OFFLINE';
            if (badgeParrot) badgeParrot.className = 'status-indicator-dot offline';
            if (textStatusParrot) textStatusParrot.textContent = 'OFFLINE';
            if (cardKaliBadge) { cardKaliBadge.className = 'badge offline'; cardKaliBadge.textContent = 'OFFLINE'; }
            if (cardParrotBadge) { cardParrotBadge.className = 'badge offline'; cardParrotBadge.textContent = 'OFFLINE'; }
            if (sidebarKaliDot) sidebarKaliDot.className = 'telemetry-dot';
            if (sidebarKaliText) sidebarKaliText.textContent = 'OFFLINE';
            if (sidebarParrotDot) sidebarParrotDot.className = 'telemetry-dot';
            if (sidebarParrotText) sidebarParrotText.textContent = 'OFFLINE';
            if (navSidebarStatusDot) navSidebarStatusDot.className = 'nav-status-dot';
        }
    }

    btnRefreshAgents.addEventListener('click', checkAgents);
    if (btnRefreshStatusView) btnRefreshStatusView.addEventListener('click', checkAgents);
    if (btnTestKaliPing) btnTestKaliPing.addEventListener('click', checkAgents);
    if (btnTestParrotPing) btnTestParrotPing.addEventListener('click', checkAgents);

    // -----------------------------------------------------------------
    // 8. Pipeline Flow Visualization
    // -----------------------------------------------------------------
    function resetPipeline() {
        if (!nodeWindows) return;
        nodeWindows.className = 'pipeline-node active';
        if (nodeKali) nodeKali.className = 'pipeline-node';
        if (nodeParrot) {
            nodeParrot.className = 'pipeline-node';
            nodeParrot.style.display = 'flex';
        }
        if (nodeOutput) nodeOutput.className = 'pipeline-node';

        if (wireKali) wireKali.className = 'pipeline-connector';
        if (wireFailover) {
            wireFailover.className = 'pipeline-connector failover';
            wireFailover.style.display = 'flex';
        }
        if (wireOutput) wireOutput.className = 'pipeline-connector';

        if (nodeKaliEnv) nodeKaliEnv.textContent = 'Primary VM';
        if (nodeParrotEnv) nodeParrotEnv.textContent = 'Backup VM';
        if (nodeOutputEnv) nodeOutputEnv.textContent = 'Verified';
        if (wireFailoverBadge) wireFailoverBadge.textContent = 'Failover ➔';
    }

    function updatePipelineForJob(job) {
        if (!job) return;
        resetPipeline();

        const status = job.status || '';
        const isMigrated = !!(job.migrated || status.includes('PARROT') || status.includes('MIGRAT'));

        if (status === 'RUNNING_KALI') {
            nodeKali.className = 'pipeline-node active';
            wireKali.className = 'pipeline-connector pulsing';
            pipelineStatusText.textContent = 'Executing on Kali Linux...';
        } else if (status === 'SUCCESS_KALI') {
            // Normal Kali Success: Windows Host → Kali Linux (successful) → Final Result
            // Parrot OS is bypassed and hidden to keep the path directly focused
            if (nodeParrot) nodeParrot.style.display = 'none';
            if (wireFailover) wireFailover.style.display = 'none';

            nodeWindows.className = 'pipeline-node success';
            wireKali.className = 'pipeline-connector success';
            nodeKali.className = 'pipeline-node success';
            if (nodeKaliEnv) nodeKaliEnv.textContent = 'Successful';

            wireOutput.className = 'pipeline-connector success';
            nodeOutput.className = 'pipeline-node success';
            if (nodeOutputEnv) nodeOutputEnv.textContent = 'Success (Kali)';

            pipelineStatusText.textContent = 'Completed on Kali Linux without failover.';
        } else if (status === 'AWAITING_APPROVAL') {
            // Kali environment failure detected; awaiting user authorization to migrate to Parrot
            if (nodeParrot) nodeParrot.style.display = 'flex';
            if (wireFailover) wireFailover.style.display = 'flex';

            nodeWindows.className = 'pipeline-node active';
            wireKali.className = 'pipeline-connector failed';
            nodeKali.className = 'pipeline-node failed';
            if (nodeKaliEnv) nodeKaliEnv.textContent = 'Env Failure';

            wireFailover.className = 'pipeline-connector failover awaiting pulsing';
            if (wireFailoverBadge) wireFailoverBadge.textContent = 'Awaiting Approval ➔';

            nodeParrot.className = 'pipeline-node awaiting';
            if (nodeParrotEnv) nodeParrotEnv.textContent = 'Ready Target';

            wireOutput.className = 'pipeline-connector';
            nodeOutput.className = 'pipeline-node';
            if (nodeOutputEnv) nodeOutputEnv.textContent = 'Pending';

            pipelineStatusText.textContent = 'Kali environment failure detected. Awaiting user authorization to migrate to Parrot OS...';
        } else if (status === 'MIGRATING_PARROT' || status === 'RUNNING_PARROT') {
            // Migration approved: Kali remains red; execution actively transfers/runs on Parrot
            if (nodeParrot) nodeParrot.style.display = 'flex';
            if (wireFailover) wireFailover.style.display = 'flex';

            nodeWindows.className = 'pipeline-node active';
            wireKali.className = 'pipeline-connector failed';
            nodeKali.className = 'pipeline-node failed';
            if (nodeKaliEnv) nodeKaliEnv.textContent = 'Failed';

            wireFailover.className = 'pipeline-connector failover active pulsing';
            if (wireFailoverBadge) wireFailoverBadge.textContent = 'Migrating ➔';

            nodeParrot.className = 'pipeline-node active';
            if (nodeParrotEnv) nodeParrotEnv.textContent = 'Executing...';

            wireOutput.className = 'pipeline-connector pulsing';
            nodeOutput.className = 'pipeline-node';
            if (nodeOutputEnv) nodeOutputEnv.textContent = 'Pending';

            pipelineStatusText.textContent = 'Environment failure. Failing over to Parrot OS...';
        } else if (status === 'SUCCESS_PARROT_MIGRATED' || (isMigrated && status.includes('SUCCESS'))) {
            // Successful failover path:
            // Windows Host → Kali Linux (failed, red) → Parrot OS (successful recovery, green) → Final Result (green)
            // Execution finishes through Parrot OS into Final Result
            if (nodeParrot) nodeParrot.style.display = 'flex';
            if (wireFailover) wireFailover.style.display = 'flex';

            nodeWindows.className = 'pipeline-node success';
            wireKali.className = 'pipeline-connector failed';

            nodeKali.className = 'pipeline-node failed';
            if (nodeKaliEnv) nodeKaliEnv.textContent = 'Failed (Env Fault)';

            wireFailover.className = 'pipeline-connector failover success';
            if (wireFailoverBadge) wireFailoverBadge.textContent = 'Approved Migration ➔';

            nodeParrot.className = 'pipeline-node success';
            if (nodeParrotEnv) nodeParrotEnv.textContent = 'Recovered';

            wireOutput.className = 'pipeline-connector success';
            nodeOutput.className = 'pipeline-node success';
            if (nodeOutputEnv) nodeOutputEnv.textContent = 'Success (Parrot)';

            pipelineStatusText.textContent = 'Failover succeeded! Executed on Parrot OS.';
        } else if (status === 'MIGRATION_DECLINED') {
            // User declined migration: halted on Kali Linux
            if (nodeParrot) nodeParrot.style.display = 'none';
            if (wireFailover) wireFailover.style.display = 'none';

            nodeWindows.className = 'pipeline-node active';
            wireKali.className = 'pipeline-connector failed';
            nodeKali.className = 'pipeline-node failed';
            if (nodeKaliEnv) nodeKaliEnv.textContent = 'Declined';

            wireOutput.className = 'pipeline-connector failed';
            nodeOutput.className = 'pipeline-node failed';
            if (nodeOutputEnv) nodeOutputEnv.textContent = 'Halted';

            pipelineStatusText.textContent = 'Migration declined by user. Execution halted on Kali Linux.';
        } else if (status === 'MIGRATION_FAILED') {
            // Backup environment failure
            if (nodeParrot) nodeParrot.style.display = 'flex';
            if (wireFailover) wireFailover.style.display = 'flex';

            nodeWindows.className = 'pipeline-node active';
            wireKali.className = 'pipeline-connector failed';
            nodeKali.className = 'pipeline-node failed';
            if (nodeKaliEnv) nodeKaliEnv.textContent = 'Failed';

            wireFailover.className = 'pipeline-connector failover failed';
            if (wireFailoverBadge) wireFailoverBadge.textContent = 'Offline ➔';

            nodeParrot.className = 'pipeline-node failed';
            if (nodeParrotEnv) nodeParrotEnv.textContent = 'Offline';

            wireOutput.className = 'pipeline-connector failed';
            nodeOutput.className = 'pipeline-node failed';
            if (nodeOutputEnv) nodeOutputEnv.textContent = 'Failed';

            pipelineStatusText.textContent = 'Migration failed: Backup environment offline.';
        } else if (status === 'FAILED_KALI_NORMAL' || status === 'TIMEOUT' || status.includes('FAILED')) {
            // Normal program error (compiler/runtime/timeout): stopped on Kali Linux
            if (nodeParrot) nodeParrot.style.display = 'none';
            if (wireFailover) wireFailover.style.display = 'none';

            nodeWindows.className = 'pipeline-node active';
            wireKali.className = 'pipeline-connector failed';
            nodeKali.className = 'pipeline-node failed';
            if (nodeKaliEnv) nodeKaliEnv.textContent = 'Program Error';

            wireOutput.className = 'pipeline-connector failed';
            nodeOutput.className = 'pipeline-node failed';
            if (nodeOutputEnv) nodeOutputEnv.textContent = 'Failed';

            pipelineStatusText.textContent = 'Program error. Stopped on Kali Linux (No migration).';
        }
    }

    // -----------------------------------------------------------------
    // 9. Render Timeline Audit Trail
    // -----------------------------------------------------------------
    function renderTimeline(timeline) {
        if (!timelineContainer) return;
        if (!timeline || timeline.length === 0) {
            timelineContainer.innerHTML = '<div class="timeline-item" style="color:var(--text-dim);">No events yet.</div>';
            if (timelineCount) timelineCount.textContent = '0 events';
            return;
        }

        if (timelineCount) timelineCount.textContent = `${timeline.length} events`;
        timelineContainer.innerHTML = timeline.map(ev => {
            const timeStr = ev.timestamp ? ev.timestamp.split('T')[1].replace('Z', '') : '';
            return `
                <div class="timeline-item">
                    <span class="timeline-dot ${ev.status || 'info'}"></span>
                    <div class="timeline-content">
                        <span class="timeline-msg">${escapeHtml(ev.message)}</span>
                        <span class="timeline-time">${timeStr}</span>
                    </div>
                </div>
            `;
        }).join('');
        timelineContainer.scrollTop = timelineContainer.scrollHeight;
    }

    // -----------------------------------------------------------------
    // 10. Console Tabs & Forensics Report
    // -----------------------------------------------------------------
    function renderConsole(job) {
        if (!job || !consoleBody) return;

        let content = '';
        let isError = false;

        if (activeConsoleTab === 'stdout') {
            if (job.status === 'AWAITING_APPROVAL') {
                content = `[CONTINUUM - Action Required: User Decision Needed]\n` +
                          `============================================================\n` +
                          `Execution halted on Kali Linux due to an environment defect:\n` +
                          `>> ${job.failure_reason || 'Missing dependency on Kali Linux'}\n\n` +
                          `QUESTION:\n` +
                          `"Kali Linux could not execute this program because of an environment issue.\n` +
                          `Would you like to retry execution on Parrot OS?"\n\n` +
                          `STATUS: Awaiting your decision.\n` +
                          `👉 To produce output on Parrot OS: Click "Yes, Migrate to Parrot" (above or in the dialog).\n` +
                          `👉 To decline failover: Click "No, Stay on Kali".\n` +
                          `============================================================\n` +
                          `NOTE: Output of Parrot OS will be produced immediately once you click "Yes, Migrate to Parrot".`;
                isError = false;
            } else {
                content = job.stdout || (job.status.includes('SUCCESS') ? '(No stdout produced)' : 'No standard output produced.');

                const isMigratedToParrot = Boolean(job.migrated || job.status === 'SUCCESS_PARROT_MIGRATED' || (job.executed_on && job.executed_on.toLowerCase().includes('parrot')));
                if (isMigratedToParrot && content) {
                    content = content.replace(/Executing on:?\s*Kali Linux(?:\s*VM)?(\s*\(([^)]*)\))?/gi, (match, fullParen, innerParen) => {
                        return innerParen ? 'Executing on: Parrot OS (Backup Environment)' : 'Executing on: Parrot OS';
                    });
                    content = content.replace(/Primary execution target:\s*Kali Linux(?:\s*VM)?/gi, 'Active execution target: Parrot OS (Backup VM)');
                }

                if (job.status.includes('FAILED') && !job.stdout) {
                    content = `[CONTINUUM] Program execution failed.\n\nDiagnostics:\n${job.failure_reason || job.stderr || job.compiler_output}`;
                    isError = true;
                }
            }
        } else if (activeConsoleTab === 'stderr') {
            content = job.stderr || '(stderr stream is empty)';
            if (job.stderr) isError = true;
        } else if (activeConsoleTab === 'compiler') {
            content = job.compiler_output || 'Compilation finished cleanly with 0 warnings/errors.';
            if (job.compiler_output && job.compiler_output.includes('error:')) isError = true;
        } else if (activeConsoleTab === 'forensics') {
            content = generateForensicsReport(job);
        }

        consoleBody.className = `console-body ${isError ? 'error-text' : ''}`;
        consoleBody.textContent = content;

        if (autoScrollConsole) {
            consoleBody.scrollTop = consoleBody.scrollHeight;
        }
    }

    function generateForensicsReport(job) {
        const mig = job.migrations && job.migrations.length > 0 ? job.migrations[0] : null;
        let html = `=== CONTINUUM CONTINUITY FORENSICS REPORT ===\n`;
        html += `Job ID            : ${job.id}\n`;
        html += `Submission Time   : ${job.created_at}\n`;
        html += `Final Environment : ${job.executed_on || 'None'}\n`;
        html += `Final Status      : ${job.status}\n`;
        html += `Execution Time    : ${job.execution_time_ms ? job.execution_time_ms.toFixed(2) : '--'} ms\n`;
        html += `Failure Category  : ${job.failure_type || 'None'}\n`;
        html += `Failure Reason    : ${job.failure_reason || 'None (Successful execution)'}\n\n`;

        if (mig) {
            html += `--- AUTOMATIC FAILOVER TRACE ---\n`;
            html += `Source Environment : ${mig.from_env}\n`;
            html += `Target Environment : ${mig.to_env}\n`;
            html += `Migration Trigger  : ${mig.reason}\n`;
            html += `Failover Result    : ${mig.success ? 'SUCCESS (Recovered)' : 'FAILED'}\n`;
            html += `Timestamp          : ${mig.migrated_at}\n`;
            if (mig.details) {
                html += `Audit Payload      : ${mig.details}\n`;
            }
        } else {
            html += `Failover Migration : Not triggered (${job.migrated ? 'Migrated' : 'Standard single-OS execution'})\n`;
        }

        return escapeHtml(html);
    }

    consoleTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            consoleTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeConsoleTab = tab.dataset.tab;
            renderConsole(currentJob);
        });
    });

    // -----------------------------------------------------------------
    // 11. Execute Program on CONTINUUM
    // -----------------------------------------------------------------
    btnRunProgram.addEventListener('click', async () => {
        const code = codeEditor.value.trim();
        if (!code) {
            alert('Please enter C source code first.');
            return;
        }

        // Set Loading State
        btnRunProgram.classList.add('loading');
        btnRunProgram.disabled = true;
        btnRunProgram.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin-icon">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 2a10 10 0 0 1 10 10"/>
            </svg>
            <span>Executing...</span>
        `;
        const requiresInput = /\b(scanf|getchar|getc|fgets|readline)\b/.test(code);
        if (requiresInput) {
            if (stdinWaitingMsg) stdinWaitingMsg.style.display = 'inline-block';
            pipelineStatusText.textContent = 'Waiting for program input... Feeding stdin...';
        } else {
            if (stdinWaitingMsg) stdinWaitingMsg.style.display = 'none';
            pipelineStatusText.textContent = 'Orchestrating cross-OS execution pipeline...';
        }
        wireKali.className = 'pipeline-connector pulsing';

        const flags = compilerFlags.value.trim().split(/\s+/).filter(Boolean);
        const stdinVal = stdinData ? stdinData.value : "";
        const payload = {
            title: isCustomCode ? "Custom C Program" : (sampleSelect.options[sampleSelect.selectedIndex]?.text || "C Program"),
            source_code: code,
            compiler_flags: flags,
            stdin: stdinVal,
            stdin_data: stdinVal,
            timeout_seconds: parseFloat(timeoutSeconds.value) || 10.0,
            simulate_kali_env_failure: chkSimulateKaliEnv.checked,
            simulate_parrot_offline: chkSimulateParrotDown.checked,
            simulate_failure_reason: chkSimulateKaliEnv.checked ? "Simulated Kali environment dependency missing." : null
        };

        try {
            const res = await fetch('/api/jobs/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Execution request failed.');
            }

            const job = await res.json();
            currentJob = job;

            // Update UI with real result
            updateJobUI(job);
            loadJobsHistory();

            // Check if job requires user approval for failover
            if (job.status === 'AWAITING_APPROVAL') {
                showFailoverConfirmationModal(job);
            }
        } catch (err) {
            alert('Execution error: ' + err.message);
            pipelineStatusText.textContent = 'Execution encountered an error.';
        } finally {
            if (stdinWaitingMsg) stdinWaitingMsg.style.display = 'none';
            btnRunProgram.classList.remove('loading');
            btnRunProgram.disabled = false;
            btnRunProgram.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                <span>Run Program</span>
            `;
        }
    });

    // -----------------------------------------------------------------
    // 11b. User-Approved Failover Modal & Decision Actions
    // -----------------------------------------------------------------
    function showFailoverConfirmationModal(job) {
        const failureText = job.failure_reason || job.stderr || job.compiler_output || 'Environment dependency missing on Kali Linux.';
        if (failoverFailureReason) {
            failoverFailureReason.textContent = failureText;
        }
        if (inlineFailureDetails) {
            inlineFailureDetails.textContent = failureText;
        }
        if (failoverConfirmationBanner) {
            failoverConfirmationBanner.style.display = 'block';
        }
        if (btnMigrateToParrot) {
            btnMigrateToParrot.disabled = false;
            btnMigrateToParrot.innerHTML = '<span>Yes, Migrate to Parrot</span>';
        }
        if (btnStayOnKali) {
            btnStayOnKali.disabled = false;
            btnStayOnKali.innerHTML = '<span>No, Stay on Kali</span>';
        }
        if (btnBannerMigrateParrot) {
            btnBannerMigrateParrot.disabled = false;
            btnBannerMigrateParrot.innerHTML = '<span>Yes, Migrate to Parrot</span>';
        }
        if (btnBannerStayKali) {
            btnBannerStayKali.disabled = false;
            btnBannerStayKali.innerHTML = '<span>No, Stay on Kali</span>';
        }
        if (failoverModal) {
            failoverModal.classList.add('open');
        }
    }

    async function handleFailoverDecision(approved) {
        if (!currentJob) return;
        const jobId = currentJob.id;

        // Prevent duplicate migration requests
        if (btnMigrateToParrot) btnMigrateToParrot.disabled = true;
        if (btnStayOnKali) btnStayOnKali.disabled = true;
        if (btnBannerMigrateParrot) btnBannerMigrateParrot.disabled = true;
        if (btnBannerStayKali) btnBannerStayKali.disabled = true;

        if (approved) {
            const spinnerHtml = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin-icon">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 2a10 10 0 0 1 10 10"/>
                </svg>
                <span>Migrating to Parrot...</span>
            `;
            if (btnMigrateToParrot) btnMigrateToParrot.innerHTML = spinnerHtml;
            if (btnBannerMigrateParrot) btnBannerMigrateParrot.innerHTML = spinnerHtml;
            pipelineStatusText.textContent = 'User approved failover. Transferring program to Parrot OS...';
            if (nodeKali) nodeKali.className = 'pipeline-node failed';
            if (wireFailover) {
                wireFailover.className = 'pipeline-connector failover active pulsing';
                wireFailover.style.display = 'flex';
            }
            if (wireFailoverBadge) wireFailoverBadge.textContent = 'Migrating ➔';
            if (nodeParrot) {
                nodeParrot.className = 'pipeline-node active';
                nodeParrot.style.display = 'flex';
            }
            if (nodeParrotEnv) nodeParrotEnv.textContent = 'Recovering...';
        } else {
            if (btnStayOnKali) btnStayOnKali.innerHTML = '<span>Declining...</span>';
            if (btnBannerStayKali) btnBannerStayKali.innerHTML = '<span>Declining...</span>';
            pipelineStatusText.textContent = 'User declined failover. Retaining execution on Kali Linux...';
        }

        try {
            const res = await fetch(`/api/jobs/${jobId}/decision`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ approved: approved })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Migration decision failed.');
            }

            const updatedJob = await res.json();
            currentJob = updatedJob;

            if (failoverModal) failoverModal.classList.remove('open');
            if (failoverConfirmationBanner) failoverConfirmationBanner.style.display = 'none';
            updateJobUI(updatedJob);
            loadJobsHistory();
        } catch (err) {
            alert('Failover decision error: ' + err.message);
            pipelineStatusText.textContent = 'Failover decision encountered an error.';
        } finally {
            if (btnMigrateToParrot) {
                btnMigrateToParrot.disabled = false;
                btnMigrateToParrot.innerHTML = '<span>Yes, Migrate to Parrot</span>';
            }
            if (btnStayOnKali) {
                btnStayOnKali.disabled = false;
                btnStayOnKali.innerHTML = '<span>No, Stay on Kali</span>';
            }
            if (btnBannerMigrateParrot) {
                btnBannerMigrateParrot.disabled = false;
                btnBannerMigrateParrot.innerHTML = '<span>Yes, Migrate to Parrot</span>';
            }
            if (btnBannerStayKali) {
                btnBannerStayKali.disabled = false;
                btnBannerStayKali.innerHTML = '<span>No, Stay on Kali</span>';
            }
        }
    }

    if (btnMigrateToParrot) {
        btnMigrateToParrot.addEventListener('click', () => handleFailoverDecision(true));
    }
    if (btnStayOnKali) {
        btnStayOnKali.addEventListener('click', () => handleFailoverDecision(false));
    }
    if (btnCloseFailoverModal) {
        btnCloseFailoverModal.addEventListener('click', () => {
            if (failoverModal) failoverModal.classList.remove('open');
        });
    }
    if (btnBannerMigrateParrot) {
        btnBannerMigrateParrot.addEventListener('click', () => handleFailoverDecision(true));
    }
    if (btnBannerStayKali) {
        btnBannerStayKali.addEventListener('click', () => handleFailoverDecision(false));
    }

    function updateJobUI(job) {
        // Toggle inline failover confirmation banner
        if (failoverConfirmationBanner) {
            if (job.status === 'AWAITING_APPROVAL') {
                failoverConfirmationBanner.style.display = 'block';
                if (inlineFailureDetails) {
                    inlineFailureDetails.textContent = job.failure_reason || job.stderr || job.compiler_output || 'Environment dependency missing on Kali Linux.';
                }
            } else {
                failoverConfirmationBanner.style.display = 'none';
            }
        }
        // Update HUD
        if (hudJobId) hudJobId.textContent = job.id;
        if (hudTarget) hudTarget.textContent = job.executed_on || 'None';
        if (hudStatus) hudStatus.textContent = job.status;
        if (hudExitCode) hudExitCode.textContent = job.exit_code ?? '--';
        if (hudExitLatency) hudExitLatency.textContent = `Exit ${job.exit_code ?? '--'} (${job.execution_time_ms ? job.execution_time_ms.toFixed(1) : '--'}ms)`;
        
        if (hudMigrationStatus) {
            if (job.migrated || job.status === 'SUCCESS_PARROT_MIGRATED') {
                hudMigrationStatus.textContent = '⚡ Yes (Parrot)';
                hudMigrationStatus.style.color = 'var(--success-color)';
            } else if (job.status === 'MIGRATION_FAILED') {
                hudMigrationStatus.textContent = '❌ Failed';
                hudMigrationStatus.style.color = 'var(--danger-color)';
            } else if (job.status === 'MIGRATION_DECLINED') {
                hudMigrationStatus.textContent = '⛔ Declined';
                hudMigrationStatus.style.color = 'var(--warning-color)';
            } else if (job.status === 'AWAITING_APPROVAL') {
                hudMigrationStatus.textContent = '⏳ Awaiting Decision';
                hudMigrationStatus.style.color = 'var(--warning-color)';
            } else {
                hudMigrationStatus.textContent = 'No Migration';
                hudMigrationStatus.style.color = 'var(--text-main)';
            }
        }

        if (hudLatencyTime) {
            hudLatencyTime.textContent = `${job.execution_time_ms ? job.execution_time_ms.toFixed(1) : '--'} ms`;
        }

        // Status coloring
        if (job.status.includes('SUCCESS')) {
            hudStatus.style.color = 'var(--success-color)';
        } else if (job.status.includes('MIGRATED')) {
            hudStatus.style.color = 'var(--parrot-color)';
        } else if (job.status === 'AWAITING_APPROVAL' || job.status === 'MIGRATION_DECLINED') {
            hudStatus.style.color = 'var(--warning-color)';
        } else if (job.status.includes('FAILED') || job.status.includes('TIMEOUT')) {
            hudStatus.style.color = 'var(--danger-color)';
        } else {
            hudStatus.style.color = 'var(--text-main)';
        }

        updatePipelineForJob(job);
        renderTimeline(job.timeline || []);
        renderConsole(job);
    }

    // -----------------------------------------------------------------
    // 12. History Tables & Metric Computation
    // -----------------------------------------------------------------
    async function loadJobsHistory() {
        try {
            const res = await fetch('/api/jobs?limit=25');
            if (!res.ok) return;
            const jobs = await res.json();

            if (jobs && Array.isArray(jobs)) {
                const total = jobs.length;
                const kaliSuccess = jobs.filter(j => j.status === 'SUCCESS_KALI').length;
                const parrotMigrated = jobs.filter(j => j.status === 'SUCCESS_PARROT_MIGRATED' || j.migrated).length;
                const errors = jobs.filter(j => j.status.includes('FAILED') || j.status.includes('TIMEOUT')).length;

                if (metricTotalJobs) metricTotalJobs.textContent = total;
                if (metricKaliSuccess) metricKaliSuccess.textContent = kaliSuccess;
                if (metricParrotMigrated) metricParrotMigrated.textContent = parrotMigrated;
                if (metricErrors) metricErrors.textContent = errors;
            }

            if (!jobs || jobs.length === 0) {
                const emptyRow = '<tr><td colspan="9" class="empty-table-cell">No previous jobs recorded yet.</td></tr>';
                if (jobsTableBody) jobsTableBody.innerHTML = emptyRow;
                if (jobsTableBodyFull) jobsTableBodyFull.innerHTML = emptyRow;
                return;
            }

            const rowsHtml = jobs.map(j => {
                let badgeClass = 'online';
                if (j.status.includes('FAILED') || j.status.includes('TIMEOUT')) badgeClass = 'offline';
                else if (j.status === 'AWAITING_APPROVAL' || j.status === 'MIGRATION_DECLINED' || j.migrated) badgeClass = 'degraded';

                let migDisplay = 'NO';
                if (j.migrated) migDisplay = '⚡ YES (Parrot)';
                else if (j.status === 'MIGRATION_DECLINED') migDisplay = '⛔ Declined';
                else if (j.status === 'AWAITING_APPROVAL') migDisplay = '⏳ Awaiting';

                return `
                    <tr>
                        <td style="font-family:'Fira Code'; font-size:0.75rem;">${j.id}</td>
                        <td style="font-weight:600;">${escapeHtml(j.title || 'C Program')}</td>
                        <td><span class="badge ${badgeClass}">${j.status}</span></td>
                        <td>${escapeHtml(j.executed_on || '--')}</td>
                        <td style="font-family:'Fira Code';">${j.exit_code ?? '--'}</td>
                        <td>${migDisplay}</td>
                        <td style="max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHtml(j.failure_reason || '')}">
                            ${escapeHtml(j.failure_reason || 'Normal Execution')}
                        </td>
                        <td style="font-family:'Fira Code';">${j.execution_time_ms ? j.execution_time_ms.toFixed(1) + 'ms' : '--'}</td>
                        <td>
                            <button class="btn btn-secondary btn-sm btn-view-job" data-id="${j.id}">View Logs</button>
                        </td>
                    </tr>
                `;
            }).join('');

            if (jobsTableBody) jobsTableBody.innerHTML = rowsHtml;
            if (jobsTableBodyFull) jobsTableBodyFull.innerHTML = rowsHtml;

            // Attach view log listeners
            document.querySelectorAll('.btn-view-job').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const id = btn.dataset.id;
                    const r = await fetch(`/api/jobs/${id}`);
                    if (r.ok) {
                        const j = await r.json();
                        currentJob = j;
                        codeEditor.value = j.source_code;
                        compilerFlags.value = (j.compiler_flags || []).join(' ');
                        stdinData.value = j.stdin_data || '';
                        updateLineNumbers();
                        updateJobUI(j);
                        switchView('viewExecute');
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                });
            });

        } catch (err) {
            console.error('Failed to load jobs history:', err);
        }
    }

    if (btnRefreshJobs) btnRefreshJobs.addEventListener('click', loadJobsHistory);
    if (btnRefreshJobsFull) btnRefreshJobsFull.addEventListener('click', loadJobsHistory);

    // -----------------------------------------------------------------
    // 13. Settings Synchronization & Modal
    // -----------------------------------------------------------------
    function syncSettingsInputs() {
        if (settingsViewKaliUrl && inputKaliUrl) {
            settingsViewKaliUrl.value = inputKaliUrl.value;
        }
        if (settingsViewParrotUrl && inputParrotUrl) {
            settingsViewParrotUrl.value = inputParrotUrl.value;
        }
    }

    async function saveAgentConfig(kaliUrl, parrotUrl) {
        try {
            const res = await fetch('/api/config/agents', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ kali_agent_url: kaliUrl, parrot_agent_url: parrotUrl })
            });
            if (res.ok) {
                inputKaliUrl.value = kaliUrl;
                inputParrotUrl.value = parrotUrl;
                if (settingsViewKaliUrl) settingsViewKaliUrl.value = kaliUrl;
                if (settingsViewParrotUrl) settingsViewParrotUrl.value = parrotUrl;
                settingsModal.classList.remove('open');
                await checkAgents();
                return true;
            } else {
                alert('Failed to save settings.');
                return false;
            }
        } catch (err) {
            alert('Error updating agent URLs: ' + err.message);
            return false;
        }
    }

    // Modal Events
    btnOpenSettings.addEventListener('click', () => {
        settingsModal.classList.add('open');
    });
    btnCloseSettingsModal.addEventListener('click', () => {
        settingsModal.classList.remove('open');
    });
    btnCancelSettings.addEventListener('click', () => {
        settingsModal.classList.remove('open');
    });

    btnSaveSettings.addEventListener('click', async () => {
        const kaliUrl = inputKaliUrl.value.trim();
        const parrotUrl = inputParrotUrl.value.trim();
        await saveAgentConfig(kaliUrl, parrotUrl);
    });

    if (btnSaveViewSettings) {
        btnSaveViewSettings.addEventListener('click', async () => {
            const kaliUrl = settingsViewKaliUrl.value.trim();
            const parrotUrl = settingsViewParrotUrl.value.trim();
            const ok = await saveAgentConfig(kaliUrl, parrotUrl);
            if (ok) alert('Agent URLs updated and validated successfully!');
        });
    }

    if (btnPresetHostOnly) {
        btnPresetHostOnly.addEventListener('click', () => {
            if (settingsViewKaliUrl) settingsViewKaliUrl.value = 'http://192.168.56.101:8001';
            if (settingsViewParrotUrl) settingsViewParrotUrl.value = 'http://192.168.56.102:8002';
        });
    }

    if (btnPresetLocalhost) {
        btnPresetLocalhost.addEventListener('click', () => {
            if (settingsViewKaliUrl) settingsViewKaliUrl.value = 'http://127.0.0.1:8001';
            if (settingsViewParrotUrl) settingsViewParrotUrl.value = 'http://127.0.0.1:8002';
        });
    }

    // Client Preferences
    if (selectPollInterval) {
        selectPollInterval.addEventListener('change', (e) => {
            pollIntervalMs = parseInt(e.target.value, 10);
            if (pollTimer) clearInterval(pollTimer);
            if (pollIntervalMs > 0) {
                pollTimer = setInterval(checkAgents, pollIntervalMs);
            }
        });
    }

    if (selectEditorFontSize) {
        selectEditorFontSize.addEventListener('change', (e) => {
            const size = e.target.value;
            codeEditor.style.fontSize = size;
            lineNumbers.style.fontSize = size;
        });
    }

    if (chkAutoScrollConsole) {
        chkAutoScrollConsole.addEventListener('change', (e) => {
            autoScrollConsole = e.target.checked;
        });
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // -----------------------------------------------------------------
    // 14. Initializations
    // -----------------------------------------------------------------
    loadPreset('normal');
    checkAgents();
    loadJobsHistory();
    pollTimer = setInterval(checkAgents, pollIntervalMs);
});
