        // ==================== AUTH & INITIALIZATION ====================
        
        // Keep sticky secondary toolbars dynamically aligned beneath .top-navbar
        function syncStickyHeaderOffsets() {
            const nav = document.querySelector('.top-navbar');
            if (nav) {
                const h = nav.offsetHeight;
                document.documentElement.style.setProperty('--top-nav-height', h + 'px');
            }
        }
        window.addEventListener('resize', syncStickyHeaderOffsets);
        window.addEventListener('DOMContentLoaded', syncStickyHeaderOffsets);

        window.addEventListener("DOMContentLoaded", () => {
            syncStickyHeaderOffsets();
            const now = new Date();
            calCurrentYear = now.getFullYear();
            calCurrentMonth = now.getMonth();

            const isAuth = sessionStorage.getItem("dh_auth");
            if (isAuth === "true") {
                document.getElementById("authScreen").style.display = "none";
                document.getElementById("mainDashboard").style.display = "flex";
                initDashboard();
            } else {
                document.getElementById("authScreen").style.display = "flex";
                document.getElementById("mainDashboard").style.display = "none";
                document.getElementById("pinInput").focus();
            }

            // Close team popover when clicked outside
            document.addEventListener("click", (e) => {
                const popover = document.getElementById("teamPopover");
                const btn = document.querySelector(".btn-team-trigger");
                if (popover && popover.classList.contains("active")) {
                    if (!popover.contains(e.target) && !btn.contains(e.target)) {
                        popover.classList.remove("active");
                    }
                }
            });

            // Keyboard shortcut: Escape closes active modals and drawers
            document.addEventListener("keydown", (e) => {
                if (e.key === "Escape") {
                    document.querySelectorAll(".modal-overlay.active").forEach(m => m.classList.remove("active"));
                    if (document.getElementById("notificationDrawer")?.classList.contains("active")) {
                        closeNotificationDrawer();
                    }
                }
            });

            // Smart visibility-based auto-refresh (Zero Render Free-Tier CPU waste)
            document.addEventListener("visibilitychange", () => {
                if (!document.hidden && sessionStorage.getItem("dh_auth") === "true") {
                    loadDashboardData(true);
                }
            });
        });

        function verifyPin() {
            const input = document.getElementById("pinInput").value.trim();
            if (input === DEFAULT_PIN || input === "1809792261" || input === "5272016689") {
                sessionStorage.setItem("dh_auth", "true");
                document.getElementById("authScreen").style.display = "none";
                document.getElementById("mainDashboard").style.display = "flex";
                chartHasAnimated = false; // Always play opening animation when logging in
                initDashboard();
                showToast("Welcome to DesignHub Admin OS", "success");
            } else {
                document.getElementById("pinError").style.display = "block";
            }
        }

        function logout() {
            sessionStorage.removeItem("dh_auth");
            document.getElementById("mainDashboard").style.display = "none";
            document.getElementById("authScreen").style.display = "flex";
            document.getElementById("pinInput").value = "";
            document.getElementById("pinError").style.display = "none";
            chartHasAnimated = false;
            if (autoSyncTimer) clearInterval(autoSyncTimer);
        }

        function updateOverviewKPICards(stats, earnings) {
            const isScoped = (typeof selectedTeams !== "undefined" && selectedTeams.size > 0 && selectedTeams.size < allTeams.length);
            const targetSubs = isScoped ? allSubscribers.filter(s => selectedTeams.has(s.team_name || "Carmella Elan")) : allSubscribers;
            const targetPays = isScoped ? allPayments.filter(p => selectedTeams.has(p.team_name || "Carmella Elan")) : allPayments;

            const sPaid = targetSubs.filter(s => s.payment_status === 'PAID').length;
            const sPend = targetSubs.filter(s => s.payment_status !== 'PAID').length;
            // Always dynamically recalculate strictly from target payments to prevent stale revenue leaks on delete
            const totalBdt = targetPays.reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);
            const txCount = targetPays.length;

            const kpiRev = document.getElementById("kpiRevenue");
            if (kpiRev) kpiRev.textContent = `৳${(totalBdt || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            const kpiTx = document.getElementById("kpiTxCount");
            if (kpiTx) kpiTx.textContent = txCount || 0;
            const kpiPaid = document.getElementById("kpiActivePaid");
            if (kpiPaid) kpiPaid.textContent = sPaid || 0;
            const kpiPend = document.getElementById("kpiPending");
            if (kpiPend) kpiPend.textContent = sPend || 0;
            const kpiTeams = document.getElementById("kpiTeamsCount");
            if (kpiTeams) kpiTeams.textContent = allTeams.length;

            const navSub = document.getElementById("navSubBadge");
            if (navSub) navSub.textContent = allSubscribers.length;
            const navPay = document.getElementById("navPayBadge");
            if (navPay) navPay.textContent = allPayments.length;
            const navTeam = document.getElementById("navTeamBadge");
            if (navTeam) navTeam.textContent = allTeams.length;
        }

        function initDashboard() {
            // Reconcile allPayments against allSubscribers immediately on boot
            if (typeof reconcilePaymentsWithSubscribers === "function") {
                try { reconcilePaymentsWithSubscribers(); } catch(e) {}
            }

            // Render all UI elements IMMEDIATELY with defensive try-catches
            try { updateOverviewKPICards(); } catch(e) { console.error("KPICards:", e); }
            try { renderTeamPopoverOptions(); } catch(e) { console.error("TeamPopover:", e); }
            try { renderTeamsCarousel(); } catch(e) { console.error("TeamsCarousel:", e); }
            try { renderTeamsGrid(); } catch(e) { console.error("TeamsGrid:", e); }
            try { renderOverviewRecentTable(); } catch(e) { console.error("RecentTable:", e); }
            try { renderActivitiesFeed(); } catch(e) { console.error("ActivitiesFeed:", e); }
            try { renderUpcomingRenewals(); } catch(e) { console.error("UpcomingRenewals:", e); }
            try { filterSubscribers(); } catch(e) { console.error("FilterSubs:", e); }
            try { filterPayments(); } catch(e) { console.error("FilterPays:", e); }
            try { renderCalendar(); } catch(e) { console.error("Calendar:", e); }

            // Ensure charts draw immediately AND with animation
            try { drawAllCharts(); } catch(e) { console.error("Initial drawAllCharts:", e); }
            setTimeout(() => {
                try { ensureOverviewChartsReady(true); } catch(e) { console.error("ensureChartsReady:", e); }
            }, 60);

            // Sync with backend asynchronously
            try { loadDashboardData(false); } catch(e) {}
            try { startSmartSyncPolling(); } catch(e) {}

            // Window resize keeps charts crisp
            window.addEventListener("resize", () => {
                if (activeView === "overview" && !isChartAnimationRunning) {
                    drawAllCharts();
                }
            });
        }



// Global Window Listeners & Bootstrapping
window.addEventListener("DOMContentLoaded", () => {
    // If PIN is already entered in session or testing
    const authScreen = document.getElementById("authScreen");
    if (sessionStorage.getItem("dh_auth") === "true") {
        if (authScreen) authScreen.style.display = "none";
        const main = document.getElementById("mainDashboard");
        if (main) main.style.display = "flex";
        initDashboard();
    }
});

// Auto close popovers when clicked outside
document.addEventListener("click", (e) => {
    const pop = document.getElementById("teamPopover");
    const trigger = document.querySelector(".btn-team-trigger");
    if (pop && trigger && pop.classList.contains("active")) {
        if (!pop.contains(e.target) && !trigger.contains(e.target)) {
            pop.classList.remove("active");
        }
    }
});
