        function startSmartSyncPolling() {
            if (autoSyncTimer) clearInterval(autoSyncTimer);
            // Poll every 15 seconds for rapid real-time sync with database
            autoSyncTimer = setInterval(() => {
                if (!document.hidden) {
                    loadDashboardData(true);
                }
            }, 15000);

            // Ticks every second so it shows \"Synced 12s ago\" format accurately
            setInterval(updateRelativeSyncTime, 1000);
        }

        function updateRelativeSyncTime() {
            const el = document.getElementById("syncStatusSidebar");
            if (!el) return;
            const diffSec = Math.floor((Date.now() - lastSyncTimestamp) / 1000);
            if (diffSec <= 1) {
                el.textContent = "Synced just now";
            } else if (diffSec < 60) {
                el.textContent = `Synced ${diffSec}s ago`;
            } else {
                const diffMin = Math.floor(diffSec / 60);
                el.textContent = `Synced ${diffMin}m ago`;
            }
        }

        async function triggerManualRefresh() {
            const btn = document.getElementById("btnRefresh");
            if (btn) btn.classList.add("syncing");

            try {
                await loadDashboardData(false);
            } catch (err) {
                console.warn("Manual sync fallback:", err);
            }

            filterSubscribers();
            filterPayments();

            if (activeView === "overview") {
                ensureOverviewChartsReady(true);
            }

            setTimeout(() => {
                if (btn) btn.classList.remove("syncing");
                showToast("System synchronized with live cloud database", "success");
            }, 500);
        }

        // ==================== DATA FETCHING & SYNCHRONIZATION ====================
        async function loadDashboardData(isBackground = false) {
            try {
                const [resSubs, resPay] = await Promise.all([
                    fetch("/api/subscribers"),
                    fetch("/api/payments")
                ]);

                if (!resSubs.ok || !resPay.ok) {
                    throw new Error(`HTTP Error: Subs ${resSubs.status}, Pay ${resPay.status}`);
                }

                const dataSubs = await resSubs.json();
                const dataPay = await resPay.json();

                // Synchronize subscribers with live database
                if (dataSubs && Array.isArray(dataSubs.subscribers)) {
                    allSubscribers = dataSubs.subscribers;
                    saveStoredData("dh_subscribers", allSubscribers);
                }

                // Synchronize payments with live database
                if (dataPay && Array.isArray(dataPay.payments)) {
                    allPayments = dataPay.payments;
                    saveStoredData("dh_payments", allPayments);
                }

                // Synchronize reference sources with live database
                if (dataSubs && Array.isArray(dataSubs.references) && dataSubs.references.length > 0) {
                    allReferences = Array.from(new Set(["Page Lead", ...dataSubs.references]));
                    saveStoredData("dh_references", allReferences);
                }

                // Reconcile payments against active subscribers to purge deleted customer transactions
                if (typeof reconcilePaymentsWithSubscribers === "function") {
                    try { reconcilePaymentsWithSubscribers(); } catch(e) {}
                }

                // Synchronize Canva teams with live database
                let sTeams = [];
                if (dataSubs && Array.isArray(dataSubs.teams)) sTeams = dataSubs.teams;
                if (dataSubs && dataSubs.active_team && !sTeams.includes(dataSubs.active_team)) sTeams.push(dataSubs.active_team);
                if (dataSubs && dataSubs.team_name && !sTeams.includes(dataSubs.team_name)) sTeams.push(dataSubs.team_name);
                if (sTeams.length > 0) {
                    allTeams = sTeams;
                } else if (!allTeams || allTeams.length === 0) {
                    allTeams = ["Carmella Elan"];
                }
                saveStoredData("dh_teams", allTeams);

                // Scope metrics dynamically according to active team selection in navbar
                const isScoped = (selectedTeams.size > 0 && selectedTeams.size < allTeams.length);
                const scopedSubs = isScoped ? allSubscribers.filter(s => selectedTeams.has(s.team_name || "Carmella Elan")) : allSubscribers;
                const scopedPays = isScoped ? allPayments.filter(p => selectedTeams.has(p.team_name || "Carmella Elan")) : allPayments;

                const activePaidCount = scopedSubs.filter(s => s.payment_status === 'PAID').length;
                const pendingCount = scopedSubs.filter(s => s.payment_status === 'PENDING').length;
                const totalBdt = scopedPays.reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);
                const txCount = scopedPays.length;

                // Update Hero Metric Cards
                const revEl = document.getElementById("kpiRevenue");
                if (revEl) revEl.textContent = `৳${totalBdt.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                const txEl = document.getElementById("kpiTxCount");
                if (txEl) txEl.textContent = txCount;
                const paidEl = document.getElementById("kpiActivePaid");
                if (paidEl) paidEl.textContent = activePaidCount;
                const pendEl = document.getElementById("kpiPending");
                if (pendEl) pendEl.textContent = pendingCount;
                const teamsCountEl = document.getElementById("kpiTeamsCount");
                if (teamsCountEl) teamsCountEl.textContent = allTeams.length;

                // Update Navigation Badges
                const subBadge = document.getElementById("navSubBadge");
                if (subBadge) subBadge.textContent = allSubscribers.length;
                const npb = document.getElementById("navPayBadge");
                if (npb) npb.textContent = allPayments.length;
                const teamBadge = document.getElementById("navTeamBadge");
                if (teamBadge) teamBadge.textContent = allTeams.length;

                // Refresh all UI components with updated database records
                try { renderTeamPopoverOptions(); } catch(e) {}
                try { populateReferenceSelects(); } catch(e) {}
                try { renderTeamsCarousel(); } catch(e) {}
                try { renderTeamsGrid(); } catch(e) {}
                try { populateTeamSelects(); } catch(e) {}
                if (activeView === "subscribers") {
                    try { renderTeamFilterChips("subTeamChipsBar"); } catch(e) {}
                }

                const subSearchFocused = (document.activeElement === document.getElementById("searchSubInput"));
                const payInputEl = document.getElementById("searchPayInput");
                const paySearchFocused = payInputEl ? (document.activeElement === payInputEl) : false;

                if (!subSearchFocused || !isBackground) {
                    try { filterSubscribers(); } catch(e) {}
                }
                if (!paySearchFocused || !isBackground) {
                    try { filterPayments(); } catch(e) {}
                }

                try { renderOverviewRecentTable(); } catch(e) {}
                try { renderActivitiesFeed(); } catch(e) {}
                try { renderUpcomingRenewals(); } catch(e) {}
                try { renderCalendar(); } catch(e) {}

                if (activeView === "overview") {
                    try { drawAllCharts(); } catch(e) {}
                }

                lastSyncTimestamp = Date.now();
                updateRelativeSyncTime();
            } catch (err) {
                console.warn("Dashboard sync using offline/local cache:", err);
                const isScoped = (typeof selectedTeams !== "undefined" && selectedTeams.size > 0 && selectedTeams.size < allTeams.length);
                const scopedSubs = isScoped ? allSubscribers.filter(s => selectedTeams.has(s.team_name || "Carmella Elan")) : allSubscribers;
                const scopedPays = isScoped ? allPayments.filter(p => selectedTeams.has(p.team_name || "Carmella Elan")) : allPayments;

                const sPaid = scopedSubs.filter(s => s.payment_status === 'PAID').length;
                const sPending = scopedSubs.filter(s => s.payment_status === 'PENDING').length;
                const totalBdt = scopedPays.reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);

                const revEl = document.getElementById("kpiRevenue");
                if (revEl) revEl.textContent = `৳${totalBdt.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                const txEl = document.getElementById("kpiTxCount");
                if (txEl) txEl.textContent = scopedPays.length;
                const paidEl = document.getElementById("kpiActivePaid");
                if (paidEl) paidEl.textContent = sPaid;
                const pendEl = document.getElementById("kpiPending");
                if (pendEl) pendEl.textContent = sPending;
                const teamsCountEl = document.getElementById("kpiTeamsCount");
                if (teamsCountEl) teamsCountEl.textContent = allTeams.length;

                try { filterSubscribers(); } catch(e) {}
                try { filterPayments(); } catch(e) {}
                try { renderUpcomingRenewals(); } catch(e) {}
                try { populateReferenceSelects(); } catch(e) {}
                try { renderCalendar(); } catch(e) {}
                try { renderActivitiesFeed(); } catch(e) {}
            }
        }
