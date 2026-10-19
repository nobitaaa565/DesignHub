var DEFAULT_PIN = "1809";

// LocalStorage Resilience Helpers
function loadStoredData(key, fallback) {
    try {
        var val = localStorage.getItem(key);
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

// Reconcile and purge any orphaned payment records from deleted customers
function reconcilePaymentsWithSubscribers() {
    if (!Array.isArray(allSubscribers) || allSubscribers.length === 0) {
        if (Array.isArray(allPayments) && allPayments.length > 0) {
            allPayments = [];
            saveStoredData("dh_payments", allPayments);
        }
        return;
    }

    const activeEmails = new Set();
    const activeNames = new Set();
    const activeCids = new Set();

    allSubscribers.forEach(s => {
        if (s.email) {
            const e = String(s.email).toLowerCase().trim();
            activeEmails.add(e);
            if (e.includes("@")) {
                activeEmails.add(e.split("@")[0].trim());
            }
        }
        if (s.name) {
            activeNames.add(String(s.name).toLowerCase().trim());
        }
        if (s.customer_id) {
            activeCids.add(String(s.customer_id).replace('#', '').trim());
        }
    });

    const initialLen = allPayments.length;
    allPayments = allPayments.filter(p => {
        const pe = String(p.customer_email || p.email || "").toLowerCase().trim();
        const pn = String(p.name || "").toLowerCase().trim();
        const pc = String(p.customer_id || "").replace('#', '').trim();
        const peUser = pe.includes("@") ? pe.split("@")[0].trim() : pe;

        const isMatch = (
            (pe && activeEmails.has(pe)) ||
            (peUser && activeEmails.has(peUser)) ||
            (pc && activeCids.has(pc)) ||
            (pn && activeNames.has(pn)) ||
            (pn && activeEmails.has(pn)) ||
            (pe && activeNames.has(pe))
        );

        return isMatch;
    });

    if (allPayments.length !== initialLen) {
        saveStoredData("dh_payments", allPayments);
    }
}

// Global State (Synchronized dynamically with live database + local persistence)
var allTeams = loadStoredData("dh_teams", ["Carmella Elan"]);
if (!Array.isArray(allTeams) || allTeams.length === 0) {
    allTeams = ["Carmella Elan"];
}
var allSubscribers = loadStoredData("dh_subscribers", []);
var allPayments = loadStoredData("dh_payments", []);
reconcilePaymentsWithSubscribers();
var allReferences = loadStoredData("dh_references", ["Page Lead", "Admin Direct", "WhatsApp", "Personal Referral"]);
if (!Array.isArray(allReferences) || allReferences.length === 0) {
    allReferences = ["Page Lead", "Admin Direct", "WhatsApp", "Personal Referral"];
}
var selectedTeams = new Set();
var subCurrentPage = 1;
var subPageSize = 20; // Records per page: 20, 40, 60, 80, 100
var filteredSubscribersCache = [];
var chartAnimProgress = 1.0;
var chartAnimId = null;
var chartHasAnimated = false;
var isChartAnimationRunning = false;
var activeView = "overview";
var subQuickEditActive = false;
var payQuickEditActive = false;
var dirtySubRows = new Set();
var dirtyPayRows = new Set();
var lastSyncTimestamp = Date.now();
var initToday = new Date();
var calCurrentYear = initToday.getFullYear();
var calCurrentMonth = initToday.getMonth(); // 0-indexed month

// Dialog Resolvers
var confirmResolver = null;
var promptResolver = null;

// Auto Refresh Timer
var autoSyncTimer = null;

// Hoisted Dashboard State Variables
var selectedCalDay = null;
var bigCalSelectedDay = null;
var bigCalFilterType = "all";
var drawChartsDebounceTimer = null;
var revTimeframe = "30d";
var activeRevHoverX = null;
var revCanvasListenersAttached = false;
var healthPeriod = "days";
var healthOffset = 0;
var activeHealthHoverIndex = null;
var activeHealthMouseX = null;
var activeHealthMouseY = null;
var healthCanvasListenersAttached = false;
var donutSelectedTeam = "all";
var currentDrawerFilter = "all";
var currentTeamSlideIndex = 0;
var isTeamCarouselPlaying = true;
var teamCarouselAutoPlayTimer = null;
var activeTeamHealthFilter = "all";

// Package Pricing Configuration Rules (Strict: 25, 50, 99 only)
var PACKAGE_PRICING = {
    "1 Month": 25,
    "3 Months": 50,
    "6 Months": 99
};

function getPackageRate(pkg, customAmt) {
    if (customAmt !== undefined && customAmt !== null && !isNaN(customAmt) && customAmt > 0) {
        return parseFloat(customAmt);
    }
    var p = String(pkg || "").toLowerCase();
    if (p.includes("6") || p.includes("12")) return 99;
    if (p.includes("3")) return 50;
    return 25;
}

var allTeamMeta = loadStoredData("dh_teams_meta", {});
if (!allTeamMeta || typeof allTeamMeta !== "object") {
    allTeamMeta = {};
}

function getTeamExpiryInfo(teamName) {
    if (!allTeamMeta || typeof allTeamMeta !== "object") allTeamMeta = {};
    let meta = allTeamMeta[teamName] || {};
    let createdDateStr = meta.created_at;

    if (!createdDateStr) {
        // Fallback: earliest subscriber date in this team, or today
        const teamSubs = (typeof allSubscribers !== "undefined" && Array.isArray(allSubscribers)) 
            ? allSubscribers.filter(s => (s.team_name || "Carmella Elan") === teamName && (s.added_at || s.joined_at))
            : [];
        if (teamSubs.length > 0) {
            const sortedDates = teamSubs.map(s => (s.added_at || s.joined_at).substring(0, 10)).sort();
            createdDateStr = sortedDates[0];
        } else {
            const d = new Date();
            createdDateStr = d.toISOString().substring(0, 10);
        }
        allTeamMeta[teamName] = { created_at: createdDateStr };
        saveStoredData("dh_teams_meta", allTeamMeta);
    }

    // Calculate strictly 2 years from created_at
    const parts = createdDateStr.split('-');
    let expiryDateStr = "";
    if (parts.length === 3) {
        const yr = parseInt(parts[0], 10) + 2;
        expiryDateStr = `${yr}-${parts[1]}-${parts[2]}`;
    } else {
        const cDate = new Date(createdDateStr);
        cDate.setFullYear(cDate.getFullYear() + 2);
        expiryDateStr = cDate.toISOString().substring(0, 10);
    }

    const expDate = new Date(expiryDateStr + "T23:59:59");
    const nowDate = new Date();
    const diffMs = expDate - nowDate;
    const daysRemaining = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
    const isExpired = daysRemaining < 0;

    return {
        createdAt: createdDateStr,
        expiresAt: expiryDateStr,
        daysRemaining: isExpired ? 0 : daysRemaining,
        rawDays: daysRemaining,
        isExpired
    };
}

var subSortColumn = "customer_id";
var subSortDirection = "asc";
