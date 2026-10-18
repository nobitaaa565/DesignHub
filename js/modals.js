        // ==================== TOASTS & NOTIFICATIONS ====================
        function showToast(message, type = "info") {
            const container = document.getElementById("toastContainer");
            if (!container) return;
            const toast = document.createElement("div");
            toast.className = `toast toast-${type}`;

            let iconSvg = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
            `;
            if (type === "success") {
                iconSvg = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                `;
            } else if (type === "error") {
                iconSvg = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg">
                        <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
                    </svg>
                `;
            } else if (type === "warning") {
                iconSvg = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                `;
            }

            toast.innerHTML = `
                <div class="toast-content-wrap">
                    ${iconSvg}
                    <span>${message}</span>
                </div>
                <button type="button" class="toast-close-btn" title="Dismiss" aria-label="Dismiss">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            `;

            let autoCloseTimer = setTimeout(() => {
                dismissToastElement(toast);
            }, 4000);

            const closeBtn = toast.querySelector(".toast-close-btn");
            if (closeBtn) {
                closeBtn.addEventListener("click", (e) => {
                    e.stopPropagation();
                    clearTimeout(autoCloseTimer);
                    dismissToastElement(toast);
                });
            }

            container.appendChild(toast);
        }

        function dismissToastElement(toastEl) {
            if (!toastEl || toastEl.dataset.closing) return;
            toastEl.dataset.closing = "true";
            toastEl.style.opacity = "0";
            toastEl.style.transform = "translateX(50px)";
            toastEl.style.transition = "all 0.25s cubic-bezier(0.16, 1, 0.3, 1)";
            setTimeout(() => {
                if (toastEl.parentNode) toastEl.remove();
            }, 250);
        }

        // ==================== CUSTOM DIALOGS ====================
        function showAlert(title, message, isWarning = false) {
            document.getElementById("alertTitle").textContent = title;
            document.getElementById("alertMessage").textContent = message;
            const icon = document.getElementById("alertIcon");
            icon.className = isWarning ? "dialog-icon warning" : "dialog-icon danger";
            icon.innerHTML = isWarning ? `
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
            ` : `
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
            `;
            document.getElementById("alertDialog").classList.add("active");
        }

        function closeAlertDialog() {
            document.getElementById("alertDialog").classList.remove("active");
        }

        function showConfirm(title, message, isDanger = false) {
            return new Promise((resolve) => {
                confirmResolver = resolve;
                document.getElementById("dialogTitle").textContent = title;
                document.getElementById("dialogMessage").textContent = message;
                const icon = document.getElementById("dialogIcon");
                icon.className = isDanger ? "dialog-icon danger" : "dialog-icon warning";
                icon.innerHTML = isDanger ? `
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                ` : `
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                `;
                document.getElementById("confirmDialog").classList.add("active");
            });
        }

        function closeConfirmDialog(result) {
            document.getElementById("confirmDialog").classList.remove("active");
            if (confirmResolver) {
                confirmResolver(result);
                confirmResolver = null;
            }
        }

        function showPrompt(title, message, defaultValue = "") {
            return new Promise((resolve) => {
                promptResolver = resolve;
                document.getElementById("promptTitle").textContent = title;
                document.getElementById("promptMessage").textContent = message;
                const inp = document.getElementById("promptInput");
                inp.value = defaultValue;
                document.getElementById("promptDialog").classList.add("active");
                inp.focus();
            });
        }

        function closePromptDialog(result) {
            document.getElementById("promptDialog").classList.remove("active");
            if (promptResolver) {
                promptResolver(result);
                promptResolver = null;
            }
        }

        function showInviteLinkModal(email, link) {
            document.getElementById("inviteLinkInput").value = link;
            document.getElementById("inviteLinkModal").classList.add("active");
        }

        function copyInviteLink() {
            const input = document.getElementById("inviteLinkInput");
            input.select();
            input.setSelectionRange(0, 99999);
            navigator.clipboard.writeText(input.value);
            showToast("Canva invite link copied to clipboard!", "success");
            closeModal("inviteLinkModal");
        }

        // ==================== VIEW NAVIGATION ====================
        function switchMainView(viewId) {
            activeView = viewId;
            setTimeout(syncStickyHeaderOffsets, 20);

            // Nav item active state
            const navOverview = document.getElementById("navItemOverview");
            const navSubs = document.getElementById("navItemSubscribers");
            const navTeams = document.getElementById("navItemTeams");
            if (navOverview) navOverview.classList.toggle("active", viewId === "overview");
            if (navSubs) navSubs.classList.toggle("active", viewId === "subscribers");
            if (navTeams) navTeams.classList.toggle("active", viewId === "teams");

            // Views visibility
            const viewOverview = document.getElementById("viewOverview");
            const viewSubs = document.getElementById("viewSubscribers");
            const viewTeams = document.getElementById("viewTeams");
            if (viewOverview) viewOverview.style.display = (viewId === "overview") ? "block" : "none";
            if (viewSubs) viewSubs.style.display = (viewId === "subscribers") ? "block" : "none";
            if (viewTeams) viewTeams.style.display = (viewId === "teams") ? "block" : "none";

            // Hide the right auxiliary panel (Calendar & admin rail) in Subscribers tab (and Teams)
            // so the Subscriber list expands to cover the entire width!
            const auxPanel = document.querySelector('.right-auxiliary-panel');
            if (auxPanel) {
                auxPanel.style.display = (viewId === "overview") ? "flex" : "none";
            }

            // Update Breadcrumb & Page Title according to active tab name
            const pageTitles = {
                overview: "Dashboard Overview",
                subscribers: "Subscribers",
                teams: "Canva Teams"
            };
            const breadcrumbLabels = {
                overview: "Overview",
                subscribers: "Subscribers",
                teams: "Canva Teams"
            };
            const pageTitleEl = document.getElementById("pageTitleText");
            if (pageTitleEl) {
                pageTitleEl.textContent = pageTitles[viewId] || "Dashboard Overview";
            }
            const breadcrumbPageEl = document.getElementById("breadcrumbPage");
            if (breadcrumbPageEl) {
                breadcrumbPageEl.textContent = breadcrumbLabels[viewId] || "Overview";
            }

            // Sync global search input placeholder to active view
            const searchInput = document.getElementById("globalQuickSearch");
            if (searchInput) {
                const placeholders = {
                    overview: "Search customer, ID, TrxID, amount, method...",
                    subscribers: "Search subscribers by ID, email, name, amount, method, TrxID...",
                    teams: "Search teams by name..."
                };
                searchInput.placeholder = placeholders[viewId] || "Search customer, ID, TrxID...";
            }

            // Top primary action button:
            // On Canva teams tab, remove duplicate button on header (keep only 'Register New Team' on the page itself!)
            const topActionBtn = document.getElementById("btnTopPrimaryAction");
            if (topActionBtn) {
                if (viewId === "teams") {
                    topActionBtn.style.display = "none";
                } else {
                    topActionBtn.style.display = "inline-flex";
                    const actionLabel = document.getElementById("topPrimaryActionLabel");
                    if (actionLabel) actionLabel.textContent = "Enroll";
                }
            }

            if (viewId === "overview") {
                // Ensure layout reflow finishes before measuring canvas
                requestAnimationFrame(() => {
                    try { drawAllCharts(); } catch(e) {}
                    setTimeout(() => {
                        try { ensureOverviewChartsReady(!chartHasAnimated); } catch(e) {}
                    }, 25);
                });
            } else if (viewId === "subscribers") {
                try { renderTeamFilterChips("subTeamChipsBar"); } catch(e) {}
                try { filterSubscribers(); } catch(e) {}
            } else if (viewId === "teams") {
                try { renderTeamsCarousel(); } catch(e) { console.error("renderTeamsCarousel error:", e); }
                try { renderTeamsGrid(); } catch(e) { console.error("renderTeamsGrid error:", e); }
            }
        }

        function handleTopPrimaryAction() {
            if (activeView === "teams") {
                openAddTeamModal();
            } else {
                openAddModal();
            }
        }

        // Global Quick Search Handler
        function handleGlobalSearch(query) {
            const val = query || "";
            const subInput = document.getElementById("searchSubInput");
            const payInput = document.getElementById("searchPayInput");
            if (subInput) subInput.value = val;
            if (payInput) payInput.value = val;

            if (activeView === "overview") {
                if (val.trim()) {
                    switchMainView("subscribers");
                    filterSubscribers();
                }
            } else if (activeView === "subscribers") {
                filterSubscribers();
            } else if (activeView === "payments") {
                filterPayments();
            } else if (activeView === "teams") {
                filterTeams(val);
            }
        }

        function filterTeams(query) {
            renderTeamsGrid();
        }

        // ==================== TEAM FILTERING & POPOVER ====================
        function toggleTeamPopover() {
            document.getElementById("teamPopover").classList.toggle("active");
        }

        function renderTeamFilterChips(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            const allActive = (selectedTeams.size === 0 || selectedTeams.size === allTeams.length);

            let html = `
                <div class="team-chip ${allActive ? 'active' : ''}" onclick="clearAllTeamsFilter()">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
                    </svg>
                    <span>All Teams (${allTeams.length})</span>
                </div>
            `;

            allTeams.forEach(t => {
                const isSelected = selectedTeams.has(t);
                html += `
                    <div class="team-chip ${isSelected ? 'active' : ''}" onclick="toggleTeamInSelection('${t}')">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/>
                        </svg>
                        <span>${t}</span>
                    </div>
                `;
            });

            container.innerHTML = html;
        }

        function toggleTeamInSelection(team) {
            if (selectedTeams.size === 0) {
                selectedTeams.add(team);
            } else if (selectedTeams.has(team)) {
                selectedTeams.delete(team);
            } else {
                selectedTeams.add(team);
            }
            updateTeamTriggerLabel();
            subCurrentPage = 1;
            filterSubscribers();
            if (activeView === "subscribers") renderTeamFilterChips("subTeamChipsBar");
        }

        function filterToSingleTeam(team) {
            selectedTeams.clear();
            selectedTeams.add(team);
            updateTeamTriggerLabel();
            subCurrentPage = 1;
            filterSubscribers();
            if (activeView === "subscribers") renderTeamFilterChips("subTeamChipsBar");
        }

        function clearAllTeamsFilter() {
            selectedTeams.clear();
            updateTeamTriggerLabel();
            subCurrentPage = 1;
            filterSubscribers();
            if (activeView === "subscribers") renderTeamFilterChips("subTeamChipsBar");
        }

        function selectAllTeams() {
            selectedTeams.clear();
            updateTeamTriggerLabel();
            subCurrentPage = 1;
            filterSubscribers();
            if (activeView === "subscribers") renderTeamFilterChips("subTeamChipsBar");
        }

        function renderTeamPopoverOptions() {
            const list = document.getElementById("teamCheckboxList");
            if (!list) return;

            list.innerHTML = allTeams.map(t => {
                const checked = (selectedTeams.size === 0 || selectedTeams.has(t)) ? "checked" : "";
                const subCount = allSubscribers.filter(s => s.team_name === t).length;
                return `
                    <label class="team-check-label">
                        <span style="display: flex; align-items: center; gap: 0.6rem;">
                            <input type="checkbox" value="${t}" ${checked} onchange="onTeamCheckboxChange(this)" style="accent-color: var(--blue-primary); width: 16px; height: 16px;">
                            <span>${t}</span>
                        </span>
                        <span style="font-size: 0.72rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">${subCount}</span>
                    </label>
                `;
            }).join('');

            updateTeamTriggerLabel();
            populateTeamSelects();
        }

        function onTeamCheckboxChange(cb) {
            if (selectedTeams.size === 0) {
                allTeams.forEach(t => selectedTeams.add(t));
            }
            if (cb.checked) {
                selectedTeams.add(cb.value);
            } else {
                selectedTeams.delete(cb.value);
            }
            if (selectedTeams.size === allTeams.length) {
                selectedTeams.clear();
            }
            updateTeamTriggerLabel();
            subCurrentPage = 1;
            filterSubscribers();
            if (activeView === "subscribers") renderTeamFilterChips("subTeamChipsBar");
        }

        function selectAllTeamsToggle() {
            if (selectedTeams.size === 0 || selectedTeams.size === allTeams.length) {
                selectedTeams.clear();
                if (allTeams.length > 0) selectedTeams.add(allTeams[0]);
            } else {
                selectedTeams.clear();
            }
            renderTeamPopoverOptions();
            updateTeamTriggerLabel();
            subCurrentPage = 1;
            filterSubscribers();
            if (activeView === "subscribers") renderTeamFilterChips("subTeamChipsBar");
        }

        function updateTeamTriggerLabel() {
            const labelEl = document.getElementById("teamTriggerLabel");
            if (!labelEl) return;
            if (selectedTeams.size === 0 || selectedTeams.size === allTeams.length) {
                labelEl.textContent = `Teams: All (${allTeams.length})`;
                document.getElementById("kpiTeamScope").textContent = "all teams";
            } else if (selectedTeams.size === 1) {
                const single = Array.from(selectedTeams)[0];
                labelEl.textContent = single;
                document.getElementById("kpiTeamScope").textContent = single;
            } else {
                labelEl.textContent = `${selectedTeams.size} Selected`;
                document.getElementById("kpiTeamScope").textContent = `${selectedTeams.size} teams`;
            }
        }

        function applyTeamFilter() {
            document.getElementById("teamPopover").classList.remove("active");
            subCurrentPage = 1;
            filterSubscribers();
            if (activeView === "subscribers") renderTeamFilterChips("subTeamChipsBar");
            if (activeView === "payments") renderTeamFilterChips("payTeamChipsBar");
            loadDashboardData(false);
            showToast("Team filter applied", "info");
        }

        function populateTeamSelects() {
            const selects = ["editTeam", "editPayTeam", "addTeamSelect", "payTeamSelect"];
            selects.forEach(id => {
                const el = document.getElementById(id);
                if (!el) return;
                const currVal = el.value;
                el.innerHTML = allTeams.map(t => `<option value="${t}">${t}</option>`).join('');
                if (currVal && allTeams.includes(currVal)) {
                    el.value = currVal;
                }
            });
        }



        // ==================== SLIDE-IN NOTIFICATION DRAWER CONTROLLER ====================
        // currentDrawerFilter hoisted

        function toggleNotificationDrawer() {
            const drawer = document.getElementById("notificationDrawer");
            const overlay = document.getElementById("notificationDrawerOverlay");
            if (!drawer || !overlay) return;

            const isOpen = drawer.classList.contains("active");
            if (isOpen) {
                closeNotificationDrawer();
            } else {
                openNotificationDrawer();
            }
        }

        function openNotificationDrawer() {
            const drawer = document.getElementById("notificationDrawer");
            const overlay = document.getElementById("notificationDrawerOverlay");
            if (!drawer || !overlay) return;

            renderNotificationDrawer(currentDrawerFilter);
            overlay.classList.add("active");
            drawer.classList.add("active");
        }

        function closeNotificationDrawer() {
            const drawer = document.getElementById("notificationDrawer");
            const overlay = document.getElementById("notificationDrawerOverlay");
            if (drawer) drawer.classList.remove("active");
            if (overlay) overlay.classList.remove("active");
        }

        function filterNotificationDrawer(category) {
            currentDrawerFilter = category;
            ['all', 'pending', 'expiring', 'system'].forEach(c => {
                const tab = document.getElementById(`notifTab${c.charAt(0).toUpperCase() + c.slice(1)}`);
                if (tab) tab.classList.toggle("active", c === category);
            });
            renderNotificationDrawer(category);
        }

        function renderNotificationDrawer(category = 'all') {
            const container = document.getElementById("notificationListContainer");
            const badge = document.getElementById("notificationCountBadge");
            if (!container) return;

            const now = new Date();
            const notifications = [];

            // 1. Pending Verifications
            const pendingSubs = allSubscribers.filter(s => s.payment_status === 'PENDING' || s.payment_status === 'UNPAID');
            pendingSubs.forEach(s => {
                notifications.push({
                    type: 'pending',
                    urgentClass: 'urgent',
                    iconBg: 'var(--rose-light)',
                    iconColor: 'var(--rose)',
                    tag: 'Action Required',
                    time: 'Pending Verification',
                    title: `Unverified Subscriber: ${s.name || s.email}`,
                    desc: `${s.email} registered for ${s.package || '3 Months'} on ${s.team_name || 'Canva'}. Payment status is ${s.payment_status}.`,
                    actionLabel: 'Verify Member',
                    actionFn: `openAddModal()`
                });
            });

            // 2. Expiring in next 48 hours
            allSubscribers.forEach(s => {
                if (s.expires_at && s.status !== 'kicked') {
                    const exp = new Date(s.expires_at);
                    const diffHours = (exp - now) / (1000 * 60 * 60);
                    if (diffHours >= 0 && diffHours <= 48) {
                        const hrsText = diffHours < 1 ? 'Under 1 hour' : `${Math.round(diffHours)} hours left`;
                        notifications.push({
                            type: 'expiring',
                            urgentClass: 'warning',
                            iconBg: 'var(--purple-light)',
                            iconColor: 'var(--purple)',
                            tag: 'Expiring Soon',
                            time: hrsText,
                            title: `Renewal Due: ${s.name || 'Member'}`,
                            desc: `${s.email} (${s.team_name || 'Team'}) will lose Canva Pro access soon.`,
                            actionLabel: 'Copy Renewal Msg',
                            actionFn: `copyRenewalReminder('${s.email}', '${s.expires_at}', '${s.team_name || 'Canva Pro'}')`
                        });
                    }
                }
            });

            // 3. Team Capacity Alerts (300 Safe Cap Rule)
            allTeams.forEach(teamName => {
                const teamSubs = allSubscribers.filter(s => (s.team_name || 'Carmella Elan') === teamName);
                const count = teamSubs.length;
                if (count >= 300) {
                    notifications.push({
                        type: 'system',
                        urgentClass: 'danger',
                        iconBg: 'var(--rose-light)',
                        iconColor: 'var(--rose)',
                        tag: 'Safe Cap Breached (≥300)',
                        time: 'Freeze Invites',
                        title: `${teamName} reached ${count} seats (Exceeds 300 limit!)`,
                        desc: `Operational ceiling of 300 exceeded. Freeze new invites on this account and switch default team.`,
                        actionLabel: 'Audit Team Health',
                        actionFn: `switchMainView('teams'); filterToSpecificTeam('${teamName}'); closeNotificationDrawer();`
                    });
                } else if (count >= 270) {
                    notifications.push({
                        type: 'system',
                        urgentClass: 'warning',
                        iconBg: 'rgba(245, 158, 11, 0.12)',
                        iconColor: '#F59E0B',
                        tag: 'Capacity Risk (≥90%)',
                        time: 'Approaching 300',
                        title: `${teamName} is at ${count}/300 Safe Cap`,
                        desc: `Only ${300 - count} safe seats remaining before 300 ceiling. Prepare secondary team now.`,
                        actionLabel: 'Audit Team Health',
                        actionFn: `switchMainView('teams'); filterToSpecificTeam('${teamName}'); closeNotificationDrawer();`
                    });
                }
            });

            // 4. Cloud Health Status
            notifications.push({
                type: 'system',
                urgentClass: 'success',
                iconBg: 'var(--emerald-light)',
                iconColor: 'var(--emerald)',
                tag: 'Cloud Engine 24/7',
                time: 'Online',
                title: 'DesignHub Automation Healthy',
                desc: 'Telegram Poster Bot and automated sync listeners running with zero crash loops.',
                actionLabel: 'Check Status',
                actionFn: `showToast('Cloud Engine is healthy and fully connected.', 'success')`
            });

            if (badge) {
                const actionCount = pendingSubs.length;
                badge.textContent = actionCount > 0 ? `${actionCount} Action Required` : `${notifications.length} Alerts`;
            }

            const filtered = (category === 'all') ? notifications : notifications.filter(n => n.type === category);

            if (filtered.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 3rem 1rem;">
                        <div style="width: 48px; height: 48px; border-radius: 50%; background: var(--bg-subtle); display: inline-flex; align-items: center; justify-content: center; margin-bottom: 0.75rem; color: var(--emerald);">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                        </div>
                        <div style="font-size: 0.95rem; font-weight: 700; color: var(--text-dark);">All Caught Up!</div>
                        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">No active ${category} alerts requiring your attention.</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = filtered.map(item => `
                <div class="notif-card ${item.urgentClass}">
                    <button type="button" class="notif-card-dismiss-btn" onclick="dismissDrawerNotif(event, this)" title="Dismiss Notification" aria-label="Dismiss">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                    <div class="notif-icon-box" style="background: ${item.iconBg}; color: ${item.iconColor};">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                    </div>
                    <div class="notif-content">
                        <div class="notif-header-row">
                            <span class="notif-tag" style="color: ${item.iconColor};">${item.tag}</span>
                            <span class="notif-time">${item.time}</span>
                        </div>
                        <div class="notif-title">${item.title}</div>
                        <div class="notif-desc">${item.desc}</div>
                        <div class="notif-actions">
                            <button class="btn btn-primary" style="font-size: 0.72rem; padding: 0.3rem 0.75rem;" onclick="${item.actionFn}">
                                <span>${item.actionLabel}</span>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function dismissDrawerNotif(e, btn) {
            e.stopPropagation();
            const card = btn.closest(".notif-card");
            if (!card) return;
            card.style.opacity = "0";
            card.style.transform = "translateX(20px)";
            card.style.transition = "all 0.25s ease";
            setTimeout(() => {
                card.remove();
                const container = document.getElementById("notificationListContainer");
                if (container && container.querySelectorAll(".notif-card").length === 0) {
                    renderNotificationDrawer(currentDrawerFilter);
                }
            }, 250);
        }

        function markAllNotificationsRead() {
            showToast("All current notifications marked as reviewed.", "success");
            closeNotificationDrawer();
        }

        function renderUpcomingRenewals() {
            const container = document.getElementById("upcomingEventsList");
            if (!container) return;

            const expiringSoon = [...allSubscribers]
                .filter(s => s.expires_at && s.status !== 'kicked')
                .sort((a, b) => (a.expires_at || "").localeCompare(b.expires_at || ""))
                .slice(0, 3);

            if (expiringSoon.length === 0) {
                container.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 1rem;">No upcoming renewals due.</div>`;
                return;
            }

            container.innerHTML = expiringSoon.map(s => {
                const dateStr = (s.expires_at || '').substring(5, 10);
                const expDate = new Date(s.expires_at);
                const daysLeft = Math.ceil((expDate - new Date()) / (1000 * 60 * 60 * 24));
                const daysBadge = daysLeft < 0 ? 'Expired' : `${daysLeft} Days Left`;

                return `
                    <div class="event-card" onclick="openExtendModal('${s.email}')">
                        <div class="event-date-pill">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="icon-svg">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                            </svg>
                            <span>${dateStr}</span>
                            <span>•</span>
                            <span>${daysBadge}</span>
                        </div>
                        <div class="event-title">${s.email}</div>
                        <div class="event-team-tag">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg">
                                <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/>
                            </svg>
                            <span>${s.team_name || 'Carmella Elan'} (${s.package || '3 Months'})</span>
                        </div>
                    </div>
                `;
            }).join('');
        }



        // ==================== EDIT CUSTOMER MODAL ====================
        function openEditCustomerModal(email) {
            const sub = allSubscribers.find(s => s.email.toLowerCase() === email.toLowerCase());
            if (!sub) return;

            document.getElementById("editOrigEmail").value = sub.email;
            document.getElementById("editCidBadge").textContent = `#${sub.customer_id || 800}`;
            document.getElementById("editName").value = sub.name || "";
            document.getElementById("editEmail").value = sub.email;
            document.getElementById("editTrxId").value = sub.trx_id || "";

            populateTeamSelects();
            document.getElementById("editTeam").value = sub.team_name || "Carmella Elan";
            document.getElementById("editPackage").value = sub.package || "3 Months";
            document.getElementById("editPaymentStatus").value = sub.payment_status || "PENDING";
            document.getElementById("editStatus").value = sub.status || "active";
            document.getElementById("editExpiresAt").value = (sub.expires_at || "").substring(0, 10);
            if (document.getElementById("editAmount")) {
                let amt = sub.amount;
                if (amt === undefined || amt === null || amt === '') {
                    const p = (sub.package || '').toLowerCase();
                    amt = (p.includes('12') || p.includes('6')) ? 99 : p.includes('3') ? 50 : 25;
                }
                document.getElementById("editAmount").value = amt;
            }
            if (document.getElementById("editMethod")) {
                document.getElementById("editMethod").value = (sub.method || sub.provider || 'bkash').toLowerCase();
            }

            document.getElementById("editCustomerModal").classList.add("active");
        }

        async function handleSaveCustomerEdit(e) {
            e.preventDefault();
            const origEmail = document.getElementById("editOrigEmail").value;
            const name = document.getElementById("editName").value.trim();
            const email = document.getElementById("editEmail").value.trim();
            const team_name = document.getElementById("editTeam").value;
            const pkg = document.getElementById("editPackage").value;
            const payment_status = document.getElementById("editPaymentStatus").value;
            const status = document.getElementById("editStatus").value;
            const expires_at = document.getElementById("editExpiresAt").value;
            const trx_id = document.getElementById("editTrxId").value.trim();

            const amount = parseFloat(document.getElementById("editAmount")?.value || 0);
            const method = document.getElementById("editMethod")?.value || 'bkash';

            // Update local memory state
            const subIdx = allSubscribers.findIndex(s => s.email.toLowerCase() === origEmail.toLowerCase());
            if (subIdx !== -1) {
                allSubscribers[subIdx] = {
                    ...allSubscribers[subIdx],
                    name,
                    email,
                    team_name,
                    package: pkg,
                    amount,
                    method,
                    provider: method,
                    payment_status,
                    status,
                    expires_at: expires_at ? `${expires_at} 23:59:59` : allSubscribers[subIdx].expires_at,
                    trx_id
                };
            }

            try {
                await fetch("/api/subscriber/update", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        email: origEmail,
                        fields: {
                            name,
                            email,
                            team_name,
                            package: pkg,
                            payment_status,
                            status,
                            expires_at: expires_at ? `${expires_at} 23:59:59` : undefined,
                            trx_id,
                            amount,
                            method
                        }
                    })
                });
            } catch (err) {}

            closeModal("editCustomerModal");
            showToast(`Profile updated for ${email}`, "success");
            loadDashboardData(true);
        }

        async function actionModalKick() {
            const email = document.getElementById("editOrigEmail").value;
            closeModal("editCustomerModal");
            actionKick(email);
        }

        async function actionModalDelete() {
            const email = document.getElementById("editOrigEmail").value;
            closeModal("editCustomerModal");
            actionDelete(email);
        }



        // ==================== TEAMS HEALTH & CAROUSEL STATE ====================
        // currentTeamSlideIndex hoisted
        // isTeamCarouselPlaying hoisted
        // teamCarouselAutoPlayTimer hoisted
        // activeTeamHealthFilter hoisted

        function getTeamHealth(teamName) {
            const teamSubs = allSubscribers.filter(s => (s.team_name || 'Carmella Elan') === teamName);
            let count = teamSubs.length;
            let activePaid = teamSubs.filter(s => s.payment_status === 'PAID' && s.status !== 'kicked').length;
            let pending = teamSubs.filter(s => s.payment_status === 'PENDING').length;
            let expired = teamSubs.filter(s => s.status === 'expired' || s.status === 'kicked').length;


            const safeLimit = 300;
            const hardLimit = 500;
            const safeRemaining = safeLimit - count;
            const hardRemaining = hardLimit - count;
            const safePct = Math.round((count / safeLimit) * 100);
            const hardPct = Math.min(100, Math.round((count / hardLimit) * 100));

            let tier, label, color, bg, border, alertMsg, badgeClass, actionAdvice;
            if (count >= 300) {
                tier = 'critical';
                label = `Limit Exceeded (${count}/300)`;
                color = '#DC2626';
                bg = 'rgba(239, 68, 68, 0.08)';
                border = 'rgba(239, 68, 68, 0.3)';
                alertMsg = `🚨 Safe Cap Breached: Account has reached ${count} seats (exceeds 300 limit!). Freeze new invites immediately and migrate enrollment target.`;
                badgeClass = 'risk-badge-critical';
                actionAdvice = 'Freeze invites immediately & switch active team';
            } else if (count >= 270) {
                tier = 'critical';
                label = `Critical Risk (${count}/300)`;
                color = '#DC2626';
                bg = 'rgba(239, 68, 68, 0.08)';
                border = 'rgba(239, 68, 68, 0.3)';
                alertMsg = `🚨 Imminent Risk: Only ${safeRemaining} seats left before 300 operational ceiling! Prepare next Canva team now.`;
                badgeClass = 'risk-badge-critical';
                actionAdvice = 'Prepare next team & route new members';
            } else if (count >= 210) {
                tier = 'warning';
                label = `Moderate Warning (${count}/300)`;
                color = '#D97706';
                bg = 'rgba(245, 158, 11, 0.08)';
                border = 'rgba(245, 158, 11, 0.3)';
                alertMsg = `⚠️ Approaching Ceiling: ${safeRemaining} seats remaining until 300 safe cap. Monitor capacity daily.`;
                badgeClass = 'risk-badge-warning';
                actionAdvice = 'Monitor daily & ready next team';
            } else {
                tier = 'healthy';
                label = `Healthy & Safe (${count}/300)`;
                color = '#059669';
                bg = 'rgba(16, 185, 129, 0.08)';
                border = 'rgba(16, 185, 129, 0.3)';
                alertMsg = `✅ Optimal Health: Operating safely with ${safeRemaining} seats available. Active for new user invites.`;
                badgeClass = 'risk-badge-healthy';
                actionAdvice = 'Active & recommended for new invites';
            }

            return {
                teamName,
                count,
                activePaid,
                pending,
                expired,
                safeLimit,
                hardLimit,
                safeRemaining,
                hardRemaining,
                safePct,
                hardPct,
                tier,
                label,
                color,
                bg,
                border,
                alertMsg,
                badgeClass,
                actionAdvice
            };
        }

        // Return teams ALWAYS sorted by risk descending (highest seats / most risky first!)
        function getSortedTeamsByRisk() {
            return [...allTeams].map(t => getTeamHealth(t)).sort((a, b) => {
                if (b.count !== a.count) return b.count - a.count;
                return b.activePaid - a.activePaid;
            });
        }

        function renderTeamsCarousel() {
            const container = document.getElementById("teamsHealthCarousel");
            if (!container) return;

            const sidecardCountEl = document.getElementById("sidecardTeamsCount");
            if (sidecardCountEl) sidecardCountEl.textContent = allTeams.length;

            const sorted = getSortedTeamsByRisk();
            if (sorted.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 2rem 1rem; color: var(--text-muted);">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 0.5rem;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/></svg>
                        <div style="font-weight: 700; color: var(--text-dark);">No Canva Teams Registered</div>
                        <div style="font-size: 0.8rem; margin-top: 0.2rem;">Click 'Register New Team' above to configure team health tracking.</div>
                    </div>
                `;
                return;
            }

            if (currentTeamSlideIndex >= sorted.length) currentTeamSlideIndex = 0;
            if (currentTeamSlideIndex < 0) currentTeamSlideIndex = sorted.length - 1;

            const critCount = sorted.filter(t => t.tier === 'critical').length;
            const warnCount = sorted.filter(t => t.tier === 'warning').length;
            const healthyCount = sorted.filter(t => t.tier === 'healthy').length;

            const current = sorted[currentTeamSlideIndex];

            const slidesHtml = sorted.map((team) => `
                <div class="team-carousel-slide">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.15rem; flex-wrap: wrap; gap: 0.75rem;">
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <div style="width: 42px; height: 42px; border-radius: 12px; background: ${team.bg}; color: ${team.color}; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/></svg>
                            </div>
                            <div>
                                <div style="font-size: 1.25rem; font-weight: 800; color: var(--text-dark); display: flex; align-items: center; gap: 0.55rem;">
                                    <span>${team.teamName}</span>
                                    <span class="health-beep-dot ${team.tier === 'critical' ? 'red' : team.tier === 'warning' ? 'yellow' : 'green'}" title="${team.label}"></span>
                                </div>
                                <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.1rem;">${team.activePaid} Active Paid Subscribers</div>
                            </div>
                        </div>

                        <button class="btn btn-secondary" style="font-size: 0.82rem; padding: 0.5rem 1rem;" onclick="filterToSpecificTeam('${team.teamName}')">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                            <span>Members</span>
                        </button>
                    </div>

                    <!-- Single Clean Capacity Bar -->
                    <div style="margin: 1rem 0 1.25rem 0;">
                        <div style="display: flex; justify-content: space-between; align-items: baseline; font-size: 0.84rem; margin-bottom: 0.45rem;">
                            <span style="font-weight: 700; color: var(--text-dark);">
                                <strong>${team.count}</strong> / 300 Seats
                            </span>
                            <span style="font-weight: 800; color: ${team.color};">
                                ${team.safePct}%
                            </span>
                        </div>
                        <div class="dual-meter-track" style="height: 10px;">
                            <div class="dual-meter-fill" style="width: ${Math.min(100, team.safePct)}%; background: ${team.color};"></div>
                        </div>
                    </div>

                    <!-- Clean Mini Metrics Strip -->
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem;">
                        <div style="background: var(--bg-subtle); padding: 0.6rem 0.75rem; border-radius: 10px; text-align: center;">
                            <div style="font-size: 0.68rem; color: var(--text-muted); font-weight: 700; letter-spacing: 0.04em;">CAPACITY</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: ${team.color};">${team.safePct}%</div>
                        </div>
                        <div style="background: var(--bg-subtle); padding: 0.6rem 0.75rem; border-radius: 10px; text-align: center;">
                            <div style="font-size: 0.68rem; color: var(--text-muted); font-weight: 700; letter-spacing: 0.04em;">ACTIVE PAID</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #047857;">${team.activePaid}</div>
                        </div>
                        <div style="background: var(--bg-subtle); padding: 0.6rem 0.75rem; border-radius: 10px; text-align: center;">
                            <div style="font-size: 0.68rem; color: var(--text-muted); font-weight: 700; letter-spacing: 0.04em;">PENDING</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #D97706;">${team.pending}</div>
                        </div>
                    </div>
                </div>
            `).join('');

            const dotsHtml = sorted.length > 1 ? `
                <div class="team-carousel-dots" id="teamCarouselDotsContainer">
                    ${sorted.map((t, idx) => `
                        <div class="carousel-dot ${idx === currentTeamSlideIndex ? 'active' : ''}" 
                             style="${idx === currentTeamSlideIndex ? `background: ${t.color};` : ''}"
                             onclick="goToTeamSlide(${idx})"
                             title="Slide ${idx + 1}: ${t.teamName} (${t.count}/300)"></div>
                    `).join('')}
                </div>
            ` : '';

            container.innerHTML = `
                <div class="carousel-header-bar">
                    <div class="carousel-title-group">
                        <div class="carousel-title-icon" id="teamCarouselHeaderIcon" style="background: ${current.bg}; color: ${current.color}; width: 38px; height: 38px;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                            </svg>
                        </div>
                        <div>
                            <div style="font-size: 1.25rem; font-weight: 800; color: var(--text-dark); display: flex; align-items: center; gap: 0.55rem; letter-spacing: -0.02em;">
                                <span>Team Health Risk Radar</span>
                            </div>
                        </div>
                    </div>

                    <div style="display: flex; align-items: center; gap: 0.85rem; flex-wrap: wrap;">
                        <div class="carousel-tag-row">
                            <span class="team-stat-tag tag-red" title="Critical">🔴 ${critCount}</span>
                            <span class="team-stat-tag tag-amber" title="Warning">🟠 ${warnCount}</span>
                            <span class="team-stat-tag tag-green" title="Healthy">🟢 ${healthyCount}</span>
                        </div>

                        <div class="carousel-nav-controls">
                            <button class="carousel-btn" id="teamCarouselPlayPauseBtn" onclick="toggleTeamCarouselAutoPlay()" title="${isTeamCarouselPlaying ? 'Pause Slideshow' : 'Resume Auto-Slideshow'}">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                    ${isTeamCarouselPlaying ? '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>' : '<polygon points="5 3 19 12 5 21 5 3"/>'}
                                </svg>
                            </button>
                            <button class="carousel-btn" onclick="prevTeamSlide()" title="Previous Team">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
                            </button>
                            <span class="carousel-counter-pill" id="teamCarouselCounter">${currentTeamSlideIndex + 1} / ${sorted.length}</span>
                            <button class="carousel-btn" onclick="nextTeamSlide()" title="Next Team">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Silky Smooth Sliding Track Viewport -->
                <div class="team-carousel-viewport" id="teamCarouselViewport" onmouseenter="pauseTeamCarouselOnHover()" onmouseleave="resumeTeamCarouselOnHover()">
                    <div class="team-carousel-track" id="teamCarouselTrack">
                        ${slidesHtml}
                    </div>
                </div>

                ${dotsHtml}
            `;

            updateTeamSlidePosition(currentTeamSlideIndex, false);
            initTeamCarouselTouchSwipe();
            resetTeamCarouselTimer(sorted.length);
        }

        function updateTeamSlidePosition(idx, animated = true) {
            const track = document.getElementById("teamCarouselTrack");
            if (!track) return;
            const sorted = getSortedTeamsByRisk();
            if (sorted.length === 0) return;

            if (animated) {
                track.style.transition = "transform 0.45s cubic-bezier(0.22, 1, 0.36, 1)";
            } else {
                track.style.transition = "none";
            }
            track.style.transform = `translateX(-${idx * 100}%)`;

            const current = sorted[idx];

            // Update counter pill
            const counterEl = document.getElementById("teamCarouselCounter");
            if (counterEl) counterEl.textContent = `${idx + 1} / ${sorted.length}`;

            // Update dots
            const dots = document.querySelectorAll("#teamCarouselDotsContainer .carousel-dot");
            dots.forEach((dot, dIdx) => {
                if (dIdx === idx) {
                    dot.classList.add("active");
                    dot.style.background = current?.color || "var(--blue-primary)";
                } else {
                    dot.classList.remove("active");
                    dot.style.background = "var(--border)";
                }
            });

            // Update header icon tint
            const iconBox = document.getElementById("teamCarouselHeaderIcon");
            if (iconBox && current) {
                iconBox.style.background = current.bg;
                iconBox.style.color = current.color;
            }
        }

        function prevTeamSlide() {
            const sorted = getSortedTeamsByRisk();
            if (sorted.length <= 1) return;
            currentTeamSlideIndex = (currentTeamSlideIndex - 1 + sorted.length) % sorted.length;
            updateTeamSlidePosition(currentTeamSlideIndex, true);
            resetTeamCarouselTimer(sorted.length);
        }

        function nextTeamSlide() {
            const sorted = getSortedTeamsByRisk();
            if (sorted.length <= 1) return;
            currentTeamSlideIndex = (currentTeamSlideIndex + 1) % sorted.length;
            updateTeamSlidePosition(currentTeamSlideIndex, true);
            resetTeamCarouselTimer(sorted.length);
        }

        function goToTeamSlide(idx) {
            const sorted = getSortedTeamsByRisk();
            if (idx < 0 || idx >= sorted.length) return;
            currentTeamSlideIndex = idx;
            updateTeamSlidePosition(currentTeamSlideIndex, true);
            resetTeamCarouselTimer(sorted.length);
        }

        function toggleTeamCarouselAutoPlay() {
            isTeamCarouselPlaying = !isTeamCarouselPlaying;
            const btn = document.getElementById("teamCarouselPlayPauseBtn");
            if (btn) {
                btn.title = isTeamCarouselPlaying ? 'Pause Slideshow' : 'Resume Auto-Slideshow';
                btn.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        ${isTeamCarouselPlaying ? '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>' : '<polygon points="5 3 19 12 5 21 5 3"/>'}
                    </svg>
                `;
            }

            const sorted = getSortedTeamsByRisk();
            resetTeamCarouselTimer(sorted.length);
            showToast(isTeamCarouselPlaying ? "Slideshow auto-advance resumed" : "Slideshow paused", "info");
        }

        function pauseTeamCarouselOnHover() {
            if (teamCarouselAutoPlayTimer) clearInterval(teamCarouselAutoPlayTimer);
        }

        function resumeTeamCarouselOnHover() {
            const sorted = getSortedTeamsByRisk();
            resetTeamCarouselTimer(sorted.length);
        }

        function resetTeamCarouselTimer(totalSlides) {
            if (teamCarouselAutoPlayTimer) clearInterval(teamCarouselAutoPlayTimer);
            if (isTeamCarouselPlaying && totalSlides > 1) {
                teamCarouselAutoPlayTimer = setInterval(() => {
                    nextTeamSlide();
                }, 6000);
            }
        }

        function initTeamCarouselTouchSwipe() {
            const vp = document.getElementById("teamCarouselViewport");
            if (!vp) return;

            // 1. Touchpad / Trackpad Two-Finger Horizontal Swipe
            // STRICT GUARANTEE: In 1 attempt it slides only once.
            // Immediately allows another slide on the next attempt without moving cursor outside!
            let wheelAccumX = 0;
            let lastSlideTimestamp = 0;
            let wheelIdleTimer = null;

            vp.addEventListener("wheel", (e) => {
                const isHorizontal = Math.abs(e.deltaX) > Math.abs(e.deltaY) || e.shiftKey;
                const delta = e.shiftKey ? e.deltaY : e.deltaX;

                // Ignore pure vertical scrolling or micro-jitter inertia (< 6px)
                if (!isHorizontal || Math.abs(delta) < 6) return;

                e.preventDefault();
                pauseTeamCarouselOnHover();

                const now = Date.now();
                // 240ms debounce window absorbs the single swipe's inertia tail
                if (now - lastSlideTimestamp > 240) {
                    // Reset accumulator if user reverses swipe direction
                    if ((delta > 0 && wheelAccumX < 0) || (delta < 0 && wheelAccumX > 0)) {
                        wheelAccumX = 0;
                    }
                    wheelAccumX += delta;

                    // Deliberate swipe threshold
                    if (Math.abs(wheelAccumX) >= 18) {
                        if (wheelAccumX > 0) {
                            nextTeamSlide(); // Swipe right to left -> advance 1 card
                        } else {
                            prevTeamSlide(); // Swipe left to right -> advance 1 card
                        }
                        lastSlideTimestamp = now;
                        wheelAccumX = 0;
                    }
                }

                if (wheelIdleTimer) clearTimeout(wheelIdleTimer);
                wheelIdleTimer = setTimeout(() => {
                    wheelAccumX = 0;
                    resumeTeamCarouselOnHover();
                }, 150);
            }, { passive: false });

            // 2. Desktop Mouse / Pointer Drag Gesture
            // HTML5 PointerCapture guarantees pointerup fires every single time,
            // allowing consecutive slides right inside the container without cursor exit!
            let isPointerDown = false;
            let pointerStartX = 0;
            let pointerStartY = 0;
            let pointerMoved = false;

            vp.style.cursor = "grab";
            vp.style.touchAction = "pan-y";

            // Prevent native browser text/image ghost dragging
            vp.addEventListener("dragstart", (e) => e.preventDefault());

            vp.addEventListener("pointerdown", (e) => {
                if (e.button !== 0) return; // Only primary left mouse button
                if (e.target.closest("button") || e.target.closest("a") || e.target.closest(".carousel-dot")) return;

                isPointerDown = true;
                pointerStartX = e.clientX;
                pointerStartY = e.clientY;
                pointerMoved = false;
                vp.style.cursor = "grabbing";
                try {
                    vp.setPointerCapture(e.pointerId);
                } catch (err) {}
                pauseTeamCarouselOnHover();
            });

            vp.addEventListener("pointermove", (e) => {
                if (!isPointerDown) return;
                const diffX = pointerStartX - e.clientX;
                const diffY = pointerStartY - e.clientY;
                if (Math.abs(diffX) > 8 && Math.abs(diffX) > Math.abs(diffY)) {
                    pointerMoved = true;
                }
            });

            const finishPointerDrag = (e) => {
                if (!isPointerDown) return;
                isPointerDown = false;
                vp.style.cursor = "grab";
                try {
                    if (e.pointerId && vp.hasPointerCapture(e.pointerId)) {
                        vp.releasePointerCapture(e.pointerId);
                    }
                } catch (err) {}

                if (pointerMoved) {
                    const diffX = pointerStartX - e.clientX;
                    // Drag threshold: 28px
                    if (Math.abs(diffX) >= 28) {
                        if (diffX > 0) {
                            nextTeamSlide(); // Dragged right to left -> exactly 1 card
                        } else {
                            prevTeamSlide(); // Dragged left to right -> exactly 1 card
                        }
                    }
                }
                pointerMoved = false;
                resumeTeamCarouselOnHover();
            };

            vp.addEventListener("pointerup", finishPointerDrag);
            vp.addEventListener("pointercancel", finishPointerDrag);
        }

        function renderTeamsHealthFilterChips(sortedTeams) {
            const container = document.getElementById("teamsHealthFilterChips");
            const summaryEl = document.getElementById("teamsHealthQuickSummary");
            if (!container) return;

            const total = sortedTeams.length;
            const crit = sortedTeams.filter(t => t.tier === 'critical').length;
            const warn = sortedTeams.filter(t => t.tier === 'warning').length;
            const healthy = sortedTeams.filter(t => t.tier === 'healthy').length;

            container.innerHTML = `
                <div class="team-health-chip ${activeTeamHealthFilter === 'all' ? 'active' : ''}" onclick="setTeamHealthFilter('all')">
                    <span>All (${total})</span>
                </div>
                <div class="team-health-chip chip-critical ${activeTeamHealthFilter === 'critical' ? 'active' : ''}" onclick="setTeamHealthFilter('critical')">
                    <span>🔴 ${crit}</span>
                </div>
                <div class="team-health-chip chip-warning ${activeTeamHealthFilter === 'warning' ? 'active' : ''}" onclick="setTeamHealthFilter('warning')">
                    <span>🟠 ${warn}</span>
                </div>
                <div class="team-health-chip chip-healthy ${activeTeamHealthFilter === 'healthy' ? 'active' : ''}" onclick="setTeamHealthFilter('healthy')">
                    <span>🟢 ${healthy}</span>
                </div>
            `;

            if (summaryEl) {
                summaryEl.innerHTML = '';
            }
        }

        function setTeamHealthFilter(tier) {
            activeTeamHealthFilter = tier;
            renderTeamsGrid();
        }

        function renderTeamsGrid() {
            const grid = document.getElementById("teamsCardsGrid");
            if (!grid) return;

            const sortedTeams = getSortedTeamsByRisk();
            renderTeamsHealthFilterChips(sortedTeams);

            // Filter by active health tier
            let filtered = sortedTeams;
            if (activeTeamHealthFilter !== 'all') {
                filtered = sortedTeams.filter(t => t.tier === activeTeamHealthFilter);
            }

            // Quick search filter if text exists
            const searchVal = (document.getElementById("globalQuickSearch")?.value || "").toLowerCase().trim();
            if (searchVal && activeView === "teams") {
                filtered = filtered.filter(t => t.teamName.toLowerCase().includes(searchVal));
            }

            if (filtered.length === 0) {
                grid.innerHTML = `
                    <div style="grid-column: 1 / -1; padding: 3rem 1.5rem; text-align: center; background: #FFFFFF; border-radius: var(--radius-card); border: 1px dashed var(--border);">
                        <div style="width: 44px; height: 44px; border-radius: 50%; background: var(--bg-subtle); display: inline-flex; align-items: center; justify-content: center; color: var(--text-muted); margin-bottom: 0.75rem;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                        </div>
                        <div style="font-weight: 700; color: var(--text-dark); margin-bottom: 0.25rem;">No Teams in Selected Filter</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted); cursor: pointer; color: var(--blue-primary); font-weight: 600;" onclick="setTeamHealthFilter('all')">Reset filter to view all teams</div>
                    </div>
                `;
                return;
            }

            grid.innerHTML = filtered.map((health) => {
                return `
                    <div class="team-card-item" style="border-top: 3px solid ${health.color};">
                        <div>
                            <div class="team-card-header">
                                <div class="team-title">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-svg" style="color: ${health.color};">
                                        <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/>
                                    </svg>
                                    <span title="${health.teamName}">${health.teamName}</span>
                                </div>
                                <span class="health-beep-dot ${health.tier === 'critical' ? 'red' : health.tier === 'warning' ? 'yellow' : 'green'}" title="${health.label}"></span>
                            </div>

                            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.35rem;">
                                <div style="font-size: 0.84rem; color: var(--text-body); font-weight: 700;">
                                    <strong>${health.count}</strong> / 300 Seats
                                </div>
                                <div style="font-size: 0.76rem; font-weight: 700; color: ${health.color};">
                                    ${health.safePct}%
                                </div>
                            </div>

                            <div class="dual-meter-track" style="height: 8px; margin-bottom: 0.85rem;" title="${health.count} / 300 Seats (${health.safePct}%)">
                                <div class="dual-meter-fill" style="width: ${Math.min(100, health.safePct)}%; background: ${health.color};"></div>
                            </div>

                            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-top: 0.35rem;">
                                <span>${health.activePaid} Active Paid</span>
                                <span>${health.pending} Pending</span>
                            </div>
                        </div>

                        <div style="display: flex; gap: 0.5rem; margin-top: 1.15rem; border-top: 1px solid var(--border-subtle); padding-top: 0.85rem;">
                            <button class="btn btn-secondary" style="flex: 1; font-size: 0.76rem; padding: 0.45rem 0.65rem;" onclick="filterToSpecificTeam('${health.teamName}')" title="View Members">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                                <span>Members</span>
                            </button>
                            <button class="btn btn-secondary btn-action-delete" style="font-size: 0.76rem; padding: 0.45rem 0.65rem;" onclick="actionDeleteTeam('${health.teamName}')" title="Delete Team">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
                            </button>
                        </div>
                    </div>
                `;
            }).join('') + `
                <div class="team-card-item" style="border: 2px dashed var(--border); background: var(--bg-subtle); align-items: center; justify-content: center; cursor: pointer; min-height: 190px;" onclick="openAddTeamModal()">
                    <div style="text-align: center;">
                        <div style="width: 44px; height: 44px; border-radius: 50%; background: var(--blue-light); color: var(--blue-primary); display: inline-flex; align-items: center; justify-content: center; margin-bottom: 0.75rem;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                            </svg>
                        </div>
                        <div style="font-weight: 800; font-size: 1rem; color: var(--text-dark);">Add Canva Team</div>
                        <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.2rem;">Connect a new team seat pool</div>
                    </div>
                </div>
            `;
        }

        function openTeamHealthModal(teamName) {
            const health = getTeamHealth(teamName);
            const modal = document.getElementById("teamHealthModal");
            if (!modal) return;

            document.getElementById("teamHealthModalTitle").textContent = `${health.teamName} Health Audit`;
            document.getElementById("teamHealthModalSubtitle").textContent = `Operational Limit: 300 Seats • Absolute Cap: 500`;

            const iconEl = document.getElementById("teamHealthModalIcon");
            if (iconEl) {
                iconEl.style.background = health.bg;
                iconEl.style.color = health.color;
            }

            const bodyEl = document.getElementById("teamHealthModalBody");
            if (bodyEl) {
                bodyEl.innerHTML = `
                    <div style="background: ${health.bg}; border: 1px solid ${health.border}; border-radius: 14px; padding: 1rem 1.25rem; display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem;">
                        <div>
                            <div style="font-size: 0.72rem; font-weight: 800; text-transform: uppercase; color: ${health.color}; letter-spacing: 0.05em;">Current Health Tier</div>
                            <div style="font-size: 1.15rem; font-weight: 800; color: ${health.color}; margin-top: 0.15rem;">${health.label}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 0.72rem; color: var(--text-muted); font-weight: 600;">Safe Cap Utilization</div>
                            <div style="font-size: 1.35rem; font-weight: 800; color: ${health.color};">${health.safePct}%</div>
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1.25rem;">
                        <div style="background: var(--bg-subtle); border-radius: 12px; padding: 0.85rem 1rem; border: 1px solid var(--border);">
                            <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;">TOTAL ALLOCATED</div>
                            <div style="font-size: 1.2rem; font-weight: 800; color: var(--text-dark); margin-top: 0.2rem;">${health.count} <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">/ 300 safe</span></div>
                            <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.15rem;">Canva hard cap: 500</div>
                        </div>
                        <div style="background: var(--bg-subtle); border-radius: 12px; padding: 0.85rem 1rem; border: 1px solid var(--border);">
                            <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;">SAFE HEADROOM</div>
                            <div style="font-size: 1.2rem; font-weight: 800; color: ${health.color}; margin-top: 0.2rem;">
                                ${health.safeRemaining < 0 ? `+${Math.abs(health.safeRemaining)} Exceeded!` : `${health.safeRemaining} seats`}
                            </div>
                            <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.15rem;">Until 300 operational ceiling</div>
                        </div>
                        <div style="background: var(--bg-subtle); border-radius: 12px; padding: 0.85rem 1rem; border: 1px solid var(--border);">
                            <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;">ACTIVE PAID MEMBERS</div>
                            <div style="font-size: 1.2rem; font-weight: 800; color: #047857; margin-top: 0.2rem;">${health.activePaid}</div>
                            <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.15rem;">Verified paid subscribers</div>
                        </div>
                        <div style="background: var(--bg-subtle); border-radius: 12px; padding: 0.85rem 1rem; border: 1px solid var(--border);">
                            <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;">PENDING / UNVERIFIED</div>
                            <div style="font-size: 1.2rem; font-weight: 800; color: #D97706; margin-top: 0.2rem;">${health.pending}</div>
                            <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.15rem;">In validation pipeline</div>
                        </div>
                    </div>

                    <div style="margin-bottom: 1.25rem;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 700; color: var(--text-dark); margin-bottom: 0.4rem;">
                            <span>Visual Capacity Meter (0 to 500)</span>
                            <span style="color: ${health.color};">${health.count} / 500 (${health.hardPct}%)</span>
                        </div>
                        <div class="dual-meter-track" style="height: 14px;">
                            <div class="dual-meter-safe-marker" title="300 Safe Cap Marker"></div>
                            <div class="dual-meter-fill" style="width: ${health.hardPct}%; background: ${health.color};"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted); margin-top: 0.35rem;">
                            <span>0</span>
                            <span style="font-weight: 800; color: #0F172A;">▲ 300 Operational Ceiling (60%)</span>
                            <span>500 Canva Limit (100%)</span>
                        </div>
                    </div>

                    <div style="background: #FFFFFF; border: 1px solid var(--border); border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                        <div style="font-size: 0.8rem; font-weight: 800; color: var(--text-dark); margin-bottom: 0.65rem; display: flex; align-items: center; gap: 0.4rem;">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                            <span>Team Health Rules & Operational Compliance</span>
                        </div>
                        
                        <div style="display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.78rem;">
                            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.35rem 0; border-bottom: 1px solid var(--border-subtle);">
                                <span style="color: var(--text-body);">Rule 1: Operational Safe Ceiling (≤ 300)</span>
                                <span style="font-weight: 700; color: ${health.count <= 300 ? '#059669' : '#DC2626'};">
                                    ${health.count <= 300 ? '✓ PASSED (' + health.safeRemaining + ' seats remaining)' : '✗ BREACHED (Exceeded by ' + (health.count - 300) + ')'}
                                </span>
                            </div>
                            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.35rem 0; border-bottom: 1px solid var(--border-subtle);">
                                <span style="color: var(--text-body);">Rule 2: Canva Account Limit (≤ 500)</span>
                                <span style="font-weight: 700; color: ${health.count < 500 ? '#059669' : '#DC2626'};">
                                    ${health.count < 500 ? '✓ PASSED (' + health.hardRemaining + ' remaining)' : '✗ FULL (Canva hard block)'}
                                </span>
                            </div>
                            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.35rem 0;">
                                <span style="color: var(--text-body);">Rule 3: Recommended Action</span>
                                <span style="font-weight: 700; color: ${health.color}; text-align: right; max-width: 250px;">
                                    ${health.actionAdvice}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div class="team-health-alert-box" style="background: ${health.bg}; border: 1px solid ${health.border}; color: ${health.color}; margin-top: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="flex-shrink: 0; margin-top: 1px;">
                            ${health.tier === 'critical' ? '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>' : health.tier === 'warning' ? '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>' : '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'}
                        </svg>
                        <div>
                            <div style="font-weight: 800; font-size: 0.82rem; margin-bottom: 0.15rem;">Admin Action Directive</div>
                            <div style="font-size: 0.76rem; line-height: 1.4;">${health.alertMsg}</div>
                        </div>
                    </div>
                `;
            }

            const viewBtn = document.getElementById("btnTeamModalViewMembers");
            if (viewBtn) {
                viewBtn.onclick = () => {
                    closeModal("teamHealthModal");
                    filterToSpecificTeam(health.teamName);
                };
            }

            const copyBtn = document.getElementById("btnTeamModalCopyLink");
            if (copyBtn) {
                copyBtn.onclick = () => {
                    closeModal("teamHealthModal");
                    openInviteModal(health.teamName);
                };
            }

            modal.classList.add("active");
        }

        function openAllTeamsHealthSummary() {
            const sorted = getSortedTeamsByRisk();
            const crit = sorted.filter(t => t.tier === 'critical');
            const warn = sorted.filter(t => t.tier === 'warning');
            const safe = sorted.filter(t => t.tier === 'healthy');

            let message = `Teams Health Rules Overview:\n\n• Limit per account: 500 members\n• Operational safe ceiling: 300 members (We never cross 300!)\n\nHealth Ranges:\n🔴 Critical (≥270 seats or ≥300): ${crit.length} team(s)\n🟠 Warning (210-269 seats): ${warn.length} team(s)\n🟢 Healthy (<210 seats): ${safe.length} team(s)\n\nTeams are automatically ranked with the most at-risk accounts featured first.`;
            showConfirm("Canva Teams Health Rules", message, false);
        }

        function filterToSpecificTeam(teamName) {
            selectedTeams.clear();
            selectedTeams.add(teamName);
            switchMainView("subscribers");
            applyTeamFilter();
        }

        async function actionDeleteTeam(teamName) {
            const confirmed = await showConfirm(
                "Delete Canva Team?",
                `Are you sure you want to remove '${teamName}' from the roster? Subscriber records will remain in database.`,
                true
            );
            if (confirmed) {
                allTeams = allTeams.filter(t => t !== teamName);
                if (allTeams.length === 0) allTeams = ["Carmella Elan"];
                saveStoredData("dh_teams", allTeams);
                selectedTeams.delete(teamName);

                renderTeamPopoverOptions();
                renderTeamsCarousel();
                renderTeamsGrid();
                populateTeamSelects();
                updateOverviewKPICards();
                showToast(`Team '${teamName}' removed`, "error");

                try {
                    await fetch("/api/team/delete", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ team_name: teamName })
                    });
                    loadDashboardData(true);
                } catch (err) {
                    console.warn("Server sync error for delete team:", err);
                }
            }
        }

        function openAddTeamModal() {
            document.getElementById("addTeamModal").classList.add("active");
            document.getElementById("newTeamInput").focus();
        }

        async function handleAddTeam(e) {
            e.preventDefault();
            const input = document.getElementById("newTeamInput");
            const team_name = input.value.trim();
            if (!team_name) return;

            if (!allTeams.includes(team_name)) {
                allTeams.push(team_name);
                saveStoredData("dh_teams", allTeams);
            }

            closeModal("addTeamModal");
            input.value = "";
            selectedTeams.clear();
            selectedTeams.add(team_name);

            renderTeamPopoverOptions();
            renderTeamsCarousel();
            renderTeamsGrid();
            populateTeamSelects();
            updateOverviewKPICards();
            if (activeView === "overview") { try { drawAllCharts(); } catch(e) {} }

            showToast(`Team '${team_name}' registered successfully!`, "success");

            try {
                await fetch("/api/team/add", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ team_name })
                });
                loadDashboardData(true);
            } catch (err) {
                console.warn("Server sync error for add team, kept locally:", err);
            }
        }

        // ==================== OTHER MODALS & ACTIONS ====================
        function openAddModal() {
            populateTeamSelects();
            document.getElementById("addModal").classList.add("active");
            document.getElementById("addEmail").focus();
        }

        function openExtendModal(email) {
            document.getElementById("extEmail").value = email;
            document.getElementById("extEmailDisplay").value = email;
            document.getElementById("extendModal").classList.add("active");
        }

        function openRecordPaymentModal() {
            populateTeamSelects();
            document.getElementById("recordPayModal").classList.add("active");
            document.getElementById("payEmail").focus();
        }

        function openModal(id) {
            const el = document.getElementById(id);
            if (el) el.classList.add("active");
        }

        function closeModal(id) {
            const el = document.getElementById(id);
            if (el) el.classList.remove("active");
        }

        function toggleAddPaidFields() {
            const isPaid = document.getElementById("addIsPaid").checked;
            document.getElementById("addPaidFields").style.display = isPaid ? "block" : "none";
        }

        function onAddPackageChange() {
            const pkg = document.getElementById("addPackage")?.value || "";
            const amtInput = document.getElementById("addAmount");
            if (!amtInput) return;
            if (pkg.includes("6")) {
                amtInput.value = "99";
            } else if (pkg.includes("3")) {
                amtInput.value = "50";
            } else {
                amtInput.value = "25";
            }
        }

        function setAddRate(amt) {
            const amtInput = document.getElementById("addAmount");
            if (amtInput) amtInput.value = amt;
        }

        function onPayPackageChange() {
            const pkg = document.getElementById("payPackage")?.value || "";
            const amtInput = document.getElementById("payAmount");
            if (!amtInput) return;
            if (pkg.includes("6")) {
                amtInput.value = "99.00";
            } else if (pkg.includes("3")) {
                amtInput.value = "50.00";
            } else {
                amtInput.value = "25.00";
            }
        }

        function setPayAmount(amt) {
            const amtInput = document.getElementById("payAmount");
            if (amtInput) amtInput.value = Number(amt).toFixed(2);
        }

        function onEditPayPackageChange() {
            const pkg = document.getElementById("editPayPackage")?.value || "";
            const amtInput = document.getElementById("editPayAmount");
            if (!amtInput) return;
            if (pkg.includes("6")) {
                amtInput.value = "99.00";
            } else if (pkg.includes("3")) {
                amtInput.value = "50.00";
            } else {
                amtInput.value = "25.00";
            }
        }

        async function handleAddSubscriber(e) {
            e.preventDefault();
            const email = document.getElementById("addEmail").value.trim();
            const name = document.getElementById("addName").value.trim();
            const team_name = document.getElementById("addTeamSelect").value || (allTeams[0] || "Carmella Elan");
            const pkg = document.getElementById("addPackage").value;
            const isPaid = document.getElementById("addIsPaid").checked;
            const provider = document.getElementById("addProvider").value;
            const trxId = document.getElementById("addTrxId").value.trim();
            const amountInput = document.getElementById("addAmount");
            const amount = parseFloat(amountInput ? amountInput.value : 0) || (pkg.includes("6") ? 99 : pkg.includes("3") ? 50 : 25);

            let days = 30;
            if (pkg.includes("6")) days = 180;
            else if (pkg.includes("3")) days = 90;

            const now = new Date();
            const exp = new Date(now.getTime() + days * 24 * 60 * 60 * 1000);
            const nowStr = now.toISOString().replace('T', ' ').substring(0, 19);
            const expStr = exp.toISOString().replace('T', ' ').substring(0, 19);

            const nextCid = allSubscribers.reduce((max, s) => Math.max(max, parseInt(s.customer_id || 800)), 800) + 1;

            const newSub = {
                customer_id: nextCid,
                email: email,
                name: name,
                team_name: team_name,
                package: pkg,
                payment_status: isPaid ? 'PAID' : 'PENDING',
                status: 'active',
                added_at: nowStr,
                expires_at: expStr,
                trx_id: trxId,
                amount: amount,
                method: provider,
                provider: provider
            };

            allSubscribers = allSubscribers.filter(s => s.email.toLowerCase() !== email.toLowerCase());
            allSubscribers.unshift(newSub);
            saveStoredData("dh_subscribers", allSubscribers);

            if (isPaid) {
                const newPay = {
                    id: Date.now(),
                    customer_id: nextCid,
                    customer_email: email,
                    email: email,
                    name: name,
                    package: pkg,
                    amount: amount,
                    currency: "BDT",
                    provider: provider,
                    trx_id: trxId,
                    paid_at: nowStr,
                    notes: "Enrollment payment",
                    team_name: team_name
                };
                allPayments.unshift(newPay);
                saveStoredData("dh_payments", allPayments);
            }

            closeModal("addModal");
            document.getElementById("addEmail").value = "";
            document.getElementById("addName").value = "";
            document.getElementById("addTrxId").value = "";
            document.getElementById("addIsPaid").checked = false;
            toggleAddPaidFields();

            updateOverviewKPICards();
            filterSubscribers();
            filterPayments();
            renderOverviewRecentTable();
            renderActivitiesFeed();
            renderUpcomingRenewals();
            renderCalendar();
            renderTeamsCarousel();
            renderTeamsGrid();
            if (activeView === "overview") { try { drawAllCharts(); } catch(e) {} }

            showToast(`Customer ${email} enrolled in ${team_name} (৳${amount})`, "success");

            try {
                await fetch("/api/subscriber/add", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, name, package: pkg, is_paid: isPaid, provider, trx_id: trxId, amount, team_name })
                });
                loadDashboardData(true);
            } catch (err) {
                console.warn("Server sync error for add subscriber:", err);
            }
        }

        async function handleExtendSubscriber(e) {
            e.preventDefault();
            const email = document.getElementById("extEmail").value;
            const pkg = document.getElementById("extPackage").value;

            let addDays = 30;
            let addRate = 25;
            if (pkg.includes("6")) { addDays = 180; addRate = 99; }
            else if (pkg.includes("3")) { addDays = 90; addRate = 50; }

            const sub = allSubscribers.find(s => s.email.toLowerCase() === email.toLowerCase());
            if (sub) {
                const baseDate = (sub.expires_at && new Date(sub.expires_at) > new Date()) ? new Date(sub.expires_at) : new Date();
                const newExp = new Date(baseDate.getTime() + addDays * 24 * 60 * 60 * 1000);
                sub.expires_at = newExp.toISOString().replace('T', ' ').substring(0, 19);
                sub.package = pkg;
                sub.status = 'active';
                sub.amount = addRate;
                saveStoredData("dh_subscribers", allSubscribers);
            }

            closeModal("extendModal");
            updateOverviewKPICards();
            filterSubscribers();
            renderUpcomingRenewals();
            renderCalendar();
            showToast(`Subscription extended for ${email}`, "success");

            try {
                await fetch("/api/subscriber/extend", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, package: pkg })
                });
                loadDashboardData(true);
            } catch (err) {
                console.warn("Server sync error for extend:", err);
            }
        }

        async function handleRecordManualPayment(e) {
            e.preventDefault();
            const email = document.getElementById("payEmail").value.trim();
            const amount = parseFloat(document.getElementById("payAmount").value);
            const team_name = document.getElementById("payTeamSelect").value || (allTeams[0] || "Carmella Elan");
            const provider = document.getElementById("payProvider").value;
            const trx_id = document.getElementById("payTrxId").value.trim();
            const pkg = document.getElementById("payPackage").value;
            const notes = document.getElementById("payNotes").value.trim();

            const nextId = Date.now();
            const sub = allSubscribers.find(s => s.email.toLowerCase() === email.toLowerCase());
            const cid = sub ? (sub.customer_id || 800) : 800 + allPayments.length + 1;
            const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19);

            const newPay = {
                id: nextId,
                customer_id: cid,
                customer_email: email,
                email: email,
                name: sub ? (sub.name || "") : "",
                package: pkg,
                amount: amount,
                currency: "BDT",
                provider: provider,
                trx_id: trx_id,
                paid_at: nowStr,
                notes: notes || "Manual Entry",
                team_name: team_name
            };

            allPayments.unshift(newPay);
            saveStoredData("dh_payments", allPayments);

            if (sub) {
                sub.payment_status = "PAID";
                sub.status = "active";
                sub.amount = amount;
                sub.trx_id = trx_id || sub.trx_id;
                sub.provider = provider;
                sub.method = provider;
                saveStoredData("dh_subscribers", allSubscribers);
            }

            closeModal("recordPayModal");
            document.getElementById("payEmail").value = "";
            document.getElementById("payAmount").value = "50.00";
            document.getElementById("payTrxId").value = "";
            document.getElementById("payNotes").value = "";

            updateOverviewKPICards();
            filterPayments();
            filterSubscribers();
            renderOverviewRecentTable();
            renderActivitiesFeed();
            renderCalendar();
            if (activeView === "overview") { try { drawAllCharts(); } catch(e) {} }

            showToast(`Payment of ৳${amount} logged for ${email}`, "success");

            try {
                await fetch("/api/payment/add", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, amount, provider, trx_id, package: pkg, notes, team_name })
                });
                loadDashboardData(true);
            } catch (err) {
                console.warn("Server sync error for payment add:", err);
            }
        }

        async function actionMarkPaid(email) {
            const trx = await showPrompt("Confirm Payment", `Enter bKash/Nagad TrxID for ${email} (Optional):`, "");
            if (trx !== null) {
                const sub = allSubscribers.find(s => s.email.toLowerCase() === email.toLowerCase());
                const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19);
                const pkg = sub ? (sub.package || "3 Months") : "3 Months";
                const amount = sub && sub.amount ? sub.amount : (pkg.includes("6") ? 99 : pkg.includes("3") ? 50 : 25);
                const team_name = sub ? (sub.team_name || "Carmella Elan") : "Carmella Elan";
                const prov = sub ? (sub.provider || sub.method || "bKash") : "bKash";

                if (sub) {
                    sub.payment_status = 'PAID';
                    sub.status = 'active';
                    sub.trx_id = trx || sub.trx_id;
                    sub.amount = amount;
                    saveStoredData("dh_subscribers", allSubscribers);
                }

                const newPay = {
                    id: Date.now(),
                    customer_id: sub ? sub.customer_id : 800,
                    customer_email: email,
                    email: email,
                    name: sub ? sub.name : "",
                    package: pkg,
                    amount: amount,
                    currency: "BDT",
                    provider: prov,
                    trx_id: trx || "",
                    paid_at: nowStr,
                    notes: "Marked Paid from Subscriber View",
                    team_name: team_name
                };
                allPayments.unshift(newPay);
                saveStoredData("dh_payments", allPayments);

                updateOverviewKPICards();
                filterSubscribers();
                filterPayments();
                renderOverviewRecentTable();
                renderActivitiesFeed();
                renderCalendar();

                showToast(`Payment marked as PAID for ${email} (৳${amount})`, "success");

                try {
                    await fetch("/api/subscriber/paid", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email, trx_id: trx, amount, provider: prov })
                    });
                    loadDashboardData(true);
                } catch (err) {
                    console.warn("Server sync error for mark paid:", err);
                }
            }
        }

        async function actionGenerateLink(email) {
            const res = await fetch("/api/invite/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, minutes: 10 })
            });
            const data = await res.json();
            if (data && data.link) {
                showInviteLinkModal(email, data.link);
            }
        }

        async function actionKick(email) {
            const confirmed = await showConfirm(
                "Revoke Canva Pro Seat?",
                `Are you sure you want to KICK ${email}? This will revoke their team membership.`,
                true
            );
            if (confirmed) {
                const sub = allSubscribers.find(s => s.email.toLowerCase() === email.toLowerCase());
                if (sub) {
                    sub.status = 'kicked';
                    sub.payment_status = 'REVOKED';
                    saveStoredData("dh_subscribers", allSubscribers);
                }

                updateOverviewKPICards();
                filterSubscribers();
                renderUpcomingRenewals();
                renderCalendar();
                showToast(`Member kicked: ${email}`, "warning");

                try {
                    await fetch("/api/subscriber/kick", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email })
                    });
                    loadDashboardData(true);
                } catch (err) {
                    console.warn("Server sync error for kick:", err);
                }
            }
        }

        async function actionDelete(email) {
            const confirmed = await showConfirm(
                "Permanently Delete Customer?",
                `Are you sure you want to delete ${email}? All record data will be permanently deleted.`,
                true
            );
            if (confirmed) {
                allSubscribers = allSubscribers.filter(s => s.email.toLowerCase() !== email.toLowerCase());
                saveStoredData("dh_subscribers", allSubscribers);

                updateOverviewKPICards();
                filterSubscribers();
                renderUpcomingRenewals();
                renderCalendar();
                showToast(`Deleted ${email}`, "error");

                try {
                    await fetch("/api/subscriber/delete", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email })
                    });
                    loadDashboardData(true);
                } catch (err) {
                    console.warn("Server sync error for delete:", err);
                }
            }
        }
