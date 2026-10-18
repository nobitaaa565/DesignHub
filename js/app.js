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
            const sPaid = stats ? stats.active_paid : allSubscribers.filter(s => s.payment_status === 'PAID').length;
            const sPend = stats ? stats.pending : allSubscribers.filter(s => s.payment_status !== 'PAID').length;
            const totalBdt = earnings ? earnings.total_bdt : allPayments.reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);
            const txCount = earnings ? earnings.total_count : allPayments.length;

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


            // Render all UI elements IMMEDIATELY so page is never blank on reload/load!
            updateOverviewKPICards();
            renderTeamPopoverOptions();
            renderTeamsCarousel();
            renderTeamsGrid();
            renderOverviewRecentTable();
            renderActivitiesFeed();
            renderUpcomingRenewals();
            filterSubscribers();
            filterPayments();
            renderCalendar();

            // Fire opening animations for charts after layout settles so animation is always seen on login!
            setTimeout(() => {
                ensureOverviewChartsReady(true);
            }, 60);

            // Sync with backend asynchronously
            loadDashboardData(false);
            startSmartSyncPolling();

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
