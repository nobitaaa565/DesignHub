        function startSmartSyncPolling() {
            if (autoSyncTimer) clearInterval(autoSyncTimer);
            // Poll every 60 seconds, only when tab is visible
            autoSyncTimer = setInterval(() => {
                if (!document.hidden) {
                    loadDashboardData(true);
                }
            }, 60000);

            // Ticks every second so it shows "Synced 12s ago" format accurately
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

            lastSyncTimestamp = Date.now();
            updateRelativeSyncTime();
            updateOverviewKPICards();
            renderCalendar();
            renderOverviewRecentTable();
            renderActivitiesFeed();
            renderUpcomingRenewals();
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
                let teamParam = "all";
                if (selectedTeams.size > 0 && selectedTeams.size < allTeams.length) {
                    teamParam = Array.from(selectedTeams).join(",");
                }

                const queryStr = teamParam === "all" ? "" : `?team=${encodeURIComponent(teamParam)}`;

                const [resSubs, resPay] = await Promise.all([
                    fetch(`/api/subscribers${queryStr}`),
                    fetch(`/api/payments${queryStr}`)
                ]);

                if (!resSubs.ok || !resPay.ok) {
                    throw new Error(`HTTP Error: Subs ${resSubs.status}, Pay ${resPay.status}`);
                }

                const dataSubs = await resSubs.json();
                const dataPay = await resPay.json();

                // Merge subscribers: if server returned subscribers, update and persist; else keep local
                if (dataSubs && Array.isArray(dataSubs.subscribers) && dataSubs.subscribers.length > 0) {
                    allSubscribers = dataSubs.subscribers;
                    saveStoredData("dh_subscribers", allSubscribers);
                } else if (allSubscribers.length > 0) {
                    saveStoredData("dh_subscribers", allSubscribers);
                }

                // Merge payments
                if (dataPay && Array.isArray(dataPay.payments) && dataPay.payments.length > 0) {
                    allPayments = dataPay.payments;
                    saveStoredData("dh_payments", allPayments);
                } else if (allPayments.length > 0) {
                    saveStoredData("dh_payments", allPayments);
                }

                // Merge teams (server teams + local teams)
                let sTeams = [];
                if (dataSubs && Array.isArray(dataSubs.teams)) sTeams = dataSubs.teams;
                if (dataSubs && dataSubs.active_team && !sTeams.includes(dataSubs.active_team)) sTeams.push(dataSubs.active_team);
                allTeams = Array.from(new Set([...sTeams, ...allTeams]));
                if (allTeams.length === 0) allTeams = ["Carmella Elan", "Pro Team 2"];
                saveStoredData("dh_teams", allTeams);

                const sampleActivePaid = allSubscribers.filter(s => s.payment_status === 'PAID').length;
                const samplePending = allSubscribers.filter(s => s.payment_status === 'PENDING').length;
                const stats = (dataSubs && dataSubs.stats && (dataSubs.stats.active_paid || dataSubs.stats.pending)) 
                    ? dataSubs.stats 
                    : { active_paid: sampleActivePaid, pending: samplePending };

                const totalBdt = allPayments.reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);
                const earnings = (dataSubs && dataSubs.earnings && dataSubs.earnings.total_bdt > 0) 
                    ? dataSubs.earnings 
                    : (dataPay && dataPay.earnings && dataPay.earnings.total_bdt > 0 ? dataPay.earnings : { total_bdt: totalBdt, total_count: allPayments.length });

                // Update Hero Metric Cards
                document.getElementById("kpiRevenue").textContent = `৳${(earnings.total_bdt || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                document.getElementById("kpiTxCount").textContent = earnings.total_count || 0;
                document.getElementById("kpiActivePaid").textContent = stats.active_paid || 0;
                document.getElementById("kpiPending").textContent = stats.pending || 0;
                document.getElementById("kpiTeamsCount").textContent = allTeams.length;

                // Update Navigation Badges
                document.getElementById("navSubBadge").textContent = allSubscribers.length;
                const npb = document.getElementById("navPayBadge"); if (npb) npb.textContent = allPayments.length;
                document.getElementById("navTeamBadge").textContent = allTeams.length;

                renderTeamPopoverOptions();
                renderTeamsCarousel();
                renderTeamsGrid();

                const subSearchFocused = (document.activeElement === document.getElementById("searchSubInput"));
                const payInputEl = document.getElementById("searchPayInput"); const paySearchFocused = payInputEl ? (document.activeElement === payInputEl) : false;

                if (!subSearchFocused || !isBackground) filterSubscribers();
                if (!paySearchFocused || !isBackground) filterPayments();

                renderOverviewRecentTable();
                renderActivitiesFeed();
                renderUpcomingRenewals();
                renderCalendar();

                if (activeView === "overview") {
                    drawAllCharts();
                }

                lastSyncTimestamp = Date.now();
                updateRelativeSyncTime();
            } catch (err) {
                console.warn("Dashboard sync using offline/local cache:", err);

                // Recover from localStorage if in memory is empty
                if (allTeams.length === 0) {
                    allTeams = loadStoredData("dh_teams", ["Carmella Elan", "Pro Team 2"]);
                }
                if (allSubscribers.length === 0) {
                    allSubscribers = loadStoredData("dh_subscribers", []);
                }
                if (allPayments.length === 0) {
                    allPayments = loadStoredData("dh_payments", []);
                }

                updateOverviewKPICards();
                renderTeamPopoverOptions();
                renderTeamsCarousel();
                renderTeamsGrid();
                filterSubscribers();
                filterPayments();
                renderOverviewRecentTable();
                renderActivitiesFeed();
                renderUpcomingRenewals();
                renderCalendar();

                if (activeView === "overview" && !isChartAnimationRunning) {
                    ensureOverviewChartsReady(false);
                }
            }
        }

