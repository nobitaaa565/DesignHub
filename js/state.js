        const DEFAULT_PIN = "1809";

        // LocalStorage Resilience Helpers
        function loadStoredData(key, fallback) {
            try {
                const val = localStorage.getItem(key);
                return val ? JSON.parse(val) : fallback;
            } catch (e) {
                return fallback;
            }
        }
        function saveStoredData(key, val) {
            try {
                localStorage.setItem(key, JSON.stringify(val));
            } catch (e) {}
        }

        // Global State (Synchronized dynamically with live database + local persistence)
        let allTeams = loadStoredData("dh_teams", ["Carmella Elan", "Pro Team 2"]);
        if (!Array.isArray(allTeams) || allTeams.length === 0) {
            allTeams = ["Carmella Elan", "Pro Team 2"];
        }
        let allSubscribers = loadStoredData("dh_subscribers", []);
        let allPayments = loadStoredData("dh_payments", []);
        let selectedTeams = new Set();
        let subCurrentPage = 1;
        let subPageSize = 20; // Records per page: 20, 40, 60, 80, 100
        let filteredSubscribersCache = [];
        let chartAnimProgress = 1.0;
        let chartAnimId = null;
        let chartHasAnimated = false;
        let isChartAnimationRunning = false;
        let activeView = "overview";
        let subQuickEditActive = false;
        let payQuickEditActive = false;
        let dirtySubRows = new Set();
        let dirtyPayRows = new Set();
        let lastSyncTimestamp = Date.now();
        const initToday = new Date();
        let calCurrentYear = initToday.getFullYear();
        let calCurrentMonth = initToday.getMonth(); // 0-indexed month

        // Dialog Resolvers
        let confirmResolver = null;
        let promptResolver = null;

        // Auto Refresh Timer (Free-Tier Safe: Pauses when tab is inactive)
        let autoSyncTimer = null;

        // Hoisted Dashboard State Variables (Prevents TDZ ReferenceErrors)
        // selectedCalDay hoisted to script top
        let bigCalSelectedDay = null;
        let bigCalFilterType = "all";
        // drawChartsDebounceTimer hoisted
        let revTimeframe = "30d";
        let activeRevHoverX = null;
        let revCanvasListenersAttached = false;
        let healthPeriod = "weekly";
        let activeHealthHoverIndex = null;
        let activeHealthMouseX = null;
        let healthCanvasListenersAttached = false;
        // donutSelectedTeam hoisted
        donutSelectedTeam = donutSelectedTeam || all;
        let currentDrawerFilter = "all";
        let currentTeamSlideIndex = 0;
        let isTeamCarouselPlaying = true;
        let teamCarouselAutoPlayTimer = null;
        let activeTeamHealthFilter = "all";


// Package Pricing Configuration Rules (Strict)
const PACKAGE_PRICING = {
    "1 Month": 25,
    "3 Months": 50,
    "6 Months": 99
};

function getPackageRate(pkg, customAmt) {
    if (customAmt !== undefined && customAmt !== null && !isNaN(customAmt) && customAmt > 0) {
        return parseFloat(customAmt);
    }
    const p = String(pkg || "").toLowerCase();
    if (p.includes("6") || p.includes("12")) return 99;
    if (p.includes("3")) return 50;
    return 25;
}
