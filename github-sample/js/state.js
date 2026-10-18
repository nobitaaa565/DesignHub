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

// Global State (Synchronized dynamically with live database + local persistence)
var allTeams = loadStoredData("dh_teams", ["Carmella Elan"]);
if (!Array.isArray(allTeams) || allTeams.length === 0) {
    allTeams = ["Carmella Elan"];
}
var allSubscribers = loadStoredData("dh_subscribers", []);
var allPayments = loadStoredData("dh_payments", []);
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
var healthPeriod = "weekly";
var activeHealthHoverIndex = null;
var activeHealthMouseX = null;
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
