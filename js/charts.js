        // ==================== PURE CANVAS CHARTS (OPENING ANIMATIONS & AUTOMATIC RELOAD DISPLAY) ====================
        // drawChartsDebounceTimer hoisted

        function triggerChartOpeningAnimation() {
            if (activeView !== "overview") return;
            const overviewEl = document.getElementById("viewOverview");
            if (!overviewEl || overviewEl.style.display === "none") return;

            chartHasAnimated = true;
            isChartAnimationRunning = true;
            if (chartAnimId) cancelAnimationFrame(chartAnimId);

            const startTime = performance.now();
            const duration = 750; // ms smooth opening duration

            function step(now) {
                const elapsed = now - startTime;
                const rawProgress = Math.min(1, elapsed / duration);
                // easeOutCubic: 1 - (1 - t)^3
                chartAnimProgress = 1 - Math.pow(1 - rawProgress, 3);

                drawRevenueTimelineChart(chartAnimProgress);
                drawPackageDonutChart(chartAnimProgress);
                drawAttendanceBarChart(chartAnimProgress);

                if (rawProgress < 1) {
                    chartAnimId = requestAnimationFrame(step);
                } else {
                    chartAnimProgress = 1.0;
                    isChartAnimationRunning = false;
                    drawRevenueTimelineChart(1.0);
                    drawPackageDonutChart(1.0);
                    drawAttendanceBarChart(1.0);
                }
            }

            chartAnimId = requestAnimationFrame(step);
        }

        function ensureOverviewChartsReady(withAnimation = true, attempts = 0) {
            if (activeView !== "overview") return;
            const overviewEl = document.getElementById("viewOverview");
            if (!overviewEl || overviewEl.style.display === "none") return;

            const revC = document.getElementById("revenueCanvas");
            const w = revC && revC.parentElement ? revC.parentElement.clientWidth : 0;
            const h = revC && revC.parentElement ? revC.parentElement.clientHeight : 0;

            if (w <= 10 || h <= 10) {
                if (attempts < 30) {
                    setTimeout(() => ensureOverviewChartsReady(withAnimation, attempts + 1), 35);
                }
                return;
            }

            if (withAnimation) {
                triggerChartOpeningAnimation();
            } else if (!isChartAnimationRunning) {
                drawAllCharts();
            }
        }

        function drawAllCharts() {
            if (activeView !== "overview") return;
            const overviewEl = document.getElementById("viewOverview");
            if (!overviewEl || overviewEl.style.display === "none") return;

            // If an opening animation is currently active, DO NOT interrupt it!
            if (isChartAnimationRunning) return;

            if (drawChartsDebounceTimer) cancelAnimationFrame(drawChartsDebounceTimer);
            drawChartsDebounceTimer = requestAnimationFrame(() => {
                drawRevenueTimelineChart(1.0);
                drawPackageDonutChart(1.0);
                drawAttendanceBarChart(1.0);
            });
        }

        // ==================== CHART CONTROLS & TIMEFRAMES ====================
        // revTimeframe hoisted
        // activeRevHoverX hoisted
        // revCanvasListenersAttached hoisted

        function toggleRevTimeframeDropdown(e) {
            if (e) e.stopPropagation();
            const menu = document.getElementById("revTimeframeMenu");
            if (menu) menu.classList.toggle("active");
            const healthMenu = document.getElementById("healthPeriodMenu");
            if (healthMenu) healthMenu.classList.remove("active");
        }

        function setRevTimeframe(tf, e) {
            if (e) e.stopPropagation();
            revTimeframe = tf;
            const labels = { '7d': 'Past 7 Days', '14d': 'Past 14 Days', '30d': 'Past 30 Days', 'all': 'All Time' };
            const lbl = document.getElementById("revTimeframeLabel");
            if (lbl) lbl.textContent = labels[tf] || '30 Days';

            document.querySelectorAll("#revTimeframeMenu .cute-dropdown-item").forEach(item => {
                item.classList.remove("active");
            });
            if (e && e.target) e.target.classList.add("active");

            const menu = document.getElementById("revTimeframeMenu");
            if (menu) menu.classList.remove("active");

            activeRevHoverX = null;
            drawRevenueTimelineChart();
        }

        // healthPeriod hoisted
        // activeHealthHoverIndex hoisted
        // activeHealthMouseX hoisted
        // healthCanvasListenersAttached hoisted

        function toggleHealthPeriodDropdown(e) {
            if (e) e.stopPropagation();
            const menu = document.getElementById("healthPeriodMenu");
            if (menu) menu.classList.toggle("active");
            const revMenu = document.getElementById("revTimeframeMenu");
            if (revMenu) revMenu.classList.remove("active");
        }

        function setHealthPeriod(period, e) {
            if (e) e.stopPropagation();
            healthPeriod = period;
            const labels = { daily: "Daily (7 Days)", weekly: "Weekly (Days)", monthly: "Monthly (4 Weeks)" };
            const lbl = document.getElementById("healthPeriodLabel");
            if (lbl) lbl.textContent = labels[period] || "Weekly";

            document.querySelectorAll("#healthPeriodMenu .cute-dropdown-item").forEach(item => {
                item.classList.remove("active");
            });
            if (e && e.target) e.target.classList.add("active");

            const menu = document.getElementById("healthPeriodMenu");
            if (menu) menu.classList.remove("active");

            activeHealthHoverIndex = null;
            drawAttendanceBarChart();
        }

        // Close dropdowns on outside click
        document.addEventListener("click", () => {
            const rm = document.getElementById("revTimeframeMenu");
            if (rm) rm.classList.remove("active");
            const hm = document.getElementById("healthPeriodMenu");
            if (hm) hm.classList.remove("active");
            const dm = document.getElementById("donutTeamMenu");
            if (dm) dm.classList.remove("active");
        });

        // ==================== EARNINGS FLOW (WITH VISIBLE PIN CIRCLES & CLEAN HOVER) ====================
        
        // ==================== SUBSCRIBERS PLAN SHARE (DONUT CHART & TEAM FILTER) ====================
        // donutSelectedTeam hoisted

        function toggleDonutTeamDropdown(e) {
            if (e) e.stopPropagation();
            const menu = document.getElementById("donutTeamMenu");
            if (!menu) return;

            menu.innerHTML = `
                <div class="cute-dropdown-item ${donutSelectedTeam === 'all' ? 'active' : ''}" onclick="setDonutTeam('all', event)">All Teams</div>
                ${allTeams.map(t => `
                    <div class="cute-dropdown-item ${donutSelectedTeam === t ? 'active' : ''}" onclick="setDonutTeam('${t.replace(/'/g, "\\'")}', event)">${t}</div>
                `).join('')}
            `;
            menu.classList.toggle("active");

            const rm = document.getElementById("revTimeframeMenu");
            if (rm) rm.classList.remove("active");
            const hm = document.getElementById("healthPeriodMenu");
            if (hm) hm.classList.remove("active");
        }

        function setDonutTeam(t, e) {
            if (e) e.stopPropagation();
            donutSelectedTeam = t;
            const lbl = document.getElementById("donutTeamLabel");
            if (lbl) lbl.textContent = t === 'all' ? 'All Teams' : t;
            const menu = document.getElementById("donutTeamMenu");
            if (menu) menu.classList.remove("active");
            drawPackageDonutChart();
        }

        function drawPackageDonutChart(animProgress = 1.0) {
            const canvas = document.getElementById("packageCanvas");
            if (!canvas) return;
            const parent = canvas.parentElement;
            if (!parent) return;

            const w = Math.floor(parent.clientWidth);
            const h = Math.floor(parent.clientHeight);
            if (w <= 10 || h <= 10) return;

            const dpr = window.devicePixelRatio || 1;
            canvas.width = Math.floor(w * dpr);
            canvas.height = Math.floor(h * dpr);
            canvas.style.width = w + "px";
            canvas.style.height = h + "px";

            const ctx = canvas.getContext("2d");
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.scale(dpr, dpr);
            ctx.clearRect(0, 0, w, h);

            let filtered = allSubscribers;
            if (donutSelectedTeam !== "all") {
                filtered = allSubscribers.filter(s => (s.team_name || "Carmella Elan") === donutSelectedTeam);
            }

            let m1 = 0, m3 = 0, m6 = 0;
            filtered.forEach(s => {
                const p = (s.package || "").toLowerCase();
                if (p.includes("6") || p.includes("12") || p.includes("year")) m6++;
                else if (p.includes("3")) m3++;
                else m1++;
            });

            const total = m1 + m3 + m6;
            const legendEl = document.getElementById("donutCustomLegend");

            if (total === 0) {
                ctx.fillStyle = "#8E9BAE";
                ctx.font = "600 12px 'Plus Jakarta Sans', sans-serif";
                ctx.textAlign = "center";
                ctx.fillText("No members enrolled in this team", w / 2, h / 2);
                if (legendEl) {
                    legendEl.className = "donut-legend-grid";
                    legendEl.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 0.5rem;">No active subscription plans for ${donutSelectedTeam}</div>`;
                }
                return;
            }

            const slices = [
                { label: "1 Month (৳25)", count: m1, color: "#0062FF" },
                { label: "3 Months (৳50)", count: m3, color: "#7C3AED" },
                { label: "6 Months (৳99)", count: m6, color: "#0D9488" }
            ].filter(s => s.count > 0);

            const cx = w / 2;
            const cy = h / 2 - 2;
            const outerR = Math.min(cx, cy) - 10;
            const innerR = outerR * 0.62;

            const prog = Math.max(0, Math.min(1, animProgress));
            const sweepLimit = Math.PI * 2 * prog;
            let currentAngle = -Math.PI / 2;
            const baseStart = -Math.PI / 2;

            slices.forEach(slice => {
                const sliceAngle = (slice.count / total) * (Math.PI * 2);
                const sStart = currentAngle;
                const sEnd = sStart + sliceAngle;
                currentAngle += sliceAngle;

                const maxAllowed = baseStart + sweepLimit;
                if (maxAllowed > sStart) {
                    const drawEnd = Math.min(sEnd, maxAllowed);
                    ctx.beginPath();
                    ctx.arc(cx, cy, outerR, sStart, drawEnd);
                    ctx.arc(cx, cy, innerR, drawEnd, sStart, true);
                    ctx.closePath();
                    ctx.fillStyle = slice.color;
                    ctx.fill();
                }
            });

            // Center Badge: Dynamic counting up animation!
            const displayCount = Math.round(total * prog);
            ctx.fillStyle = "#0F172A";
            ctx.font = "800 20px 'JetBrains Mono', monospace";
            ctx.textAlign = "center";
            ctx.fillText(displayCount.toString(), cx, cy + 3);

            ctx.fillStyle = "#8E9BAE";
            ctx.font = "700 9.5px 'Plus Jakarta Sans', sans-serif";
            ctx.fillText("MEMBERS", cx, cy + 18);

            // Update Custom Legend on bottom of card with appropriate 2x2 grid tiles
            if (legendEl) {
                legendEl.className = "donut-legend-grid";
                legendEl.innerHTML = slices.map(s => {
                    const pct = Math.round((s.count / total) * 100);
                    return `
                        <div class="donut-legend-tile">
                            <div class="donut-legend-info">
                                <span class="donut-legend-dot" style="background: ${s.color};"></span>
                                <span class="donut-legend-title">${s.label}</span>
                            </div>
                            <div class="donut-legend-metrics">
                                <span class="donut-legend-num">${s.count}</span>
                                <span class="donut-legend-pct-pill" style="color: ${s.color}; background: ${s.color}15; border: 1px solid ${s.color}25;">${pct}%</span>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }

        function drawRevenueTimelineChart(animProgress = 1.0) {
            const canvas = document.getElementById("revenueCanvas");
            if (!canvas) return;
            const parent = canvas.parentElement;
            if (!parent) return;

            const w = Math.floor(parent.clientWidth);
            const h = Math.floor(parent.clientHeight);
            if (w <= 10 || h <= 10) return;

            const dpr = window.devicePixelRatio || 1;
            canvas.width = Math.floor(w * dpr);
            canvas.height = Math.floor(h * dpr);
            canvas.style.width = w + "px";
            canvas.style.height = h + "px";

            const ctx = canvas.getContext("2d");
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.scale(dpr, dpr);
            ctx.clearRect(0, 0, w, h);

            // Generate timeline points strictly from REAL payments
            let points = [];
            const totalActualRevenue = allPayments.reduce((acc, p) => acc + (parseFloat(p.amount) || 0), 0);

            let numDays = 7;
            if (revTimeframe === '14d') numDays = 14;
            else if (revTimeframe === 'all') numDays = 30;

            const now = new Date();
            const daySlots = [];
            for (let i = numDays - 1; i >= 0; i--) {
                const d = new Date(now);
                d.setDate(d.getDate() - i);
                const y = d.getFullYear();
                const m = String(d.getMonth() + 1).padStart(2, '0');
                const day = String(d.getDate()).padStart(2, '0');
                const dateStr = `${y}-${m}-${day}`;
                const label = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                daySlots.push({ dateStr, label, endOfDay: new Date(`${dateStr}T23:59:59`).getTime() });
            }

            if (allPayments.length === 0) {
                points = daySlots.map(slot => ({
                    date: slot.label,
                    earnings: 0
                }));
            } else {
                const sortedPay = [...allPayments].sort((a, b) => {
                    const ta = a.paid_at ? new Date(a.paid_at.replace(' ', 'T')).getTime() : 0;
                    const tb = b.paid_at ? new Date(b.paid_at.replace(' ', 'T')).getTime() : 0;
                    return ta - tb;
                });

                points = daySlots.map(slot => {
                    const earnedUpToDay = sortedPay
                        .filter(p => {
                            if (!p.paid_at) return false;
                            const pt = new Date(p.paid_at.replace(' ', 'T')).getTime();
                            return pt <= slot.endOfDay;
                        })
                        .reduce((sum, p) => sum + (parseFloat(p.amount) || 0), 0);
                    return {
                        date: slot.label,
                        earnings: Math.round(earnedUpToDay)
                    };
                });
            }

            // Compute realistic Y-axis scale based on clean multiples of 25 (e.g. 25, 50, 75, 100, 150...)
            const maxEarnings = Math.max(...points.map(p => p.earnings), 0);

            // Candidate step sizes holding strict multiples of 25 (e.g. 25, 50, 75, 100, 150, 200, 300...)
            const candidateSteps = [25, 50, 75, 100, 125, 150, 200, 250, 300, 500, 1000, 2500, 5000];
            let step = 25;
            let gridLines = 4;

            const rawTargetMax = maxEarnings > 0 ? maxEarnings * 1.18 : 100;
            const targetMax = Math.max(100, rawTargetMax);

            for (const s of candidateSteps) {
                if (s * 4 >= targetMax) {
                    step = s;
                    break;
                }
            }
            if (step * 4 < targetMax) {
                step = Math.ceil(targetMax / (4 * 25)) * 25;
            }

            // Number of intervals (between 3 and 5)
            gridLines = Math.min(5, Math.max(3, Math.ceil(targetMax / step)));
            const maxVal = step * gridLines;

            const paddingLeft = 52;
            const paddingRight = 32;
            const paddingTop = 36;
            const paddingBottom = 34;
            const drawW = w - paddingLeft - paddingRight;
            const drawH = h - paddingTop - paddingBottom;
            if (drawW <= 10 || drawH <= 10) return;

            // Draw Background Horizontal Grid Lines with clean multiples of 25
            ctx.strokeStyle = "#F1F5F9";
            ctx.lineWidth = 1;
            for (let i = 0; i <= gridLines; i++) {
                const y = paddingTop + (drawH / gridLines) * i;
                ctx.beginPath();
                ctx.moveTo(paddingLeft, y);
                ctx.lineTo(w - paddingRight, y);
                ctx.stroke();

                // Axis label in BDT (৳) holding strict multiple of 25 pattern (25, 50, 75, 100...)
                const val = step * (gridLines - i);
                ctx.fillStyle = "#8E9BAE";
                ctx.font = "600 10px 'JetBrains Mono', monospace";
                ctx.textAlign = "right";
                const labelText = val >= 10000 ? `${(val / 1000).toFixed(0)}K` : val.toLocaleString('en-US');
                ctx.fillText(`৳${labelText}`, paddingLeft - 8, y + 3.5);
            }

            // Calculate Canvas Coordinates for each point (smooth rising opening animation)
            const prog = Math.max(0, Math.min(1, animProgress));
            const ptsCoords = points.map((p, idx) => {
                const x = paddingLeft + (idx / Math.max(1, points.length - 1)) * drawW;
                const targetY = paddingTop + drawH - (p.earnings / maxVal) * drawH;
                const baseY = paddingTop + drawH;
                const yEarn = baseY - (baseY - targetY) * prog;
                return { x, yEarn, data: p };
            });

            // Draw Area Fill Gradient (Emerald #10B981)
            const gradRev = ctx.createLinearGradient(0, paddingTop, 0, paddingTop + drawH);
            gradRev.addColorStop(0, "rgba(16, 185, 129, 0.25)");
            gradRev.addColorStop(1, "rgba(16, 185, 129, 0.0)");

            ctx.beginPath();
            ctx.moveTo(ptsCoords[0].x, paddingTop + drawH);
            ptsCoords.forEach((pt, i) => {
                if (i === 0) {
                    ctx.lineTo(pt.x, pt.yEarn);
                } else {
                    const prev = ptsCoords[i - 1];
                    const cx = (prev.x + pt.x) / 2;
                    ctx.bezierCurveTo(cx, prev.yEarn, cx, pt.yEarn, pt.x, pt.yEarn);
                }
            });
            ctx.lineTo(ptsCoords[ptsCoords.length - 1].x, paddingTop + drawH);
            ctx.closePath();
            ctx.fillStyle = gradRev;
            ctx.fill();

            // Stroke Actual Earnings Spline Line
            ctx.beginPath();
            ptsCoords.forEach((pt, i) => {
                if (i === 0) {
                    ctx.moveTo(pt.x, pt.yEarn);
                } else {
                    const prev = ptsCoords[i - 1];
                    const cx = (prev.x + pt.x) / 2;
                    ctx.bezierCurveTo(cx, prev.yEarn, cx, pt.yEarn, pt.x, pt.yEarn);
                }
            });
            ctx.strokeStyle = "#10B981";
            ctx.lineWidth = 3.2;
            ctx.lineCap = "round";
            ctx.stroke();

            // 1. Draw Dates on X-axis (Clean, no tiny circles on every day)
            ptsCoords.forEach((pt) => {
                ctx.fillStyle = "#8E9BAE";
                ctx.font = "600 10px 'Plus Jakarta Sans', sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(pt.data.date, pt.x, paddingTop + drawH + 18);
            });

            // 2. The highest tiny circle should ALWAYS show on the spline once animated
            if (prog >= 0.95) {
                const highestPt = ptsCoords.reduce((max, p) => p.data.earnings > max.data.earnings ? p : max, ptsCoords[0]);
                ctx.fillStyle = "#FFFFFF";
                ctx.beginPath();
                ctx.arc(highestPt.x, highestPt.yEarn, 5, 0, Math.PI * 2);
                ctx.fill();
                ctx.strokeStyle = "#10B981";
                ctx.lineWidth = 2.8;
                ctx.stroke();
            }

            // 3. Smooth Hover: snaps cleanly to each day showing ONLY 1 EXACT VERIFIED AMOUNT for that day!
            if (prog >= 0.95 && activeRevHoverX !== null) {
                const clampedX = Math.max(ptsCoords[0].x, Math.min(ptsCoords[ptsCoords.length - 1].x, activeRevHoverX));

                // Find closest day point
                let closestIdx = 0;
                let minDist = Infinity;
                ptsCoords.forEach((p, idx) => {
                    const dist = Math.abs(p.x - clampedX);
                    if (dist < minDist) {
                        minDist = dist;
                        closestIdx = idx;
                    }
                });
                const activeDayPt = ptsCoords[closestIdx];

                // Subtle vertical dashed guideline at this day
                ctx.save();
                ctx.beginPath();
                ctx.setLineDash([3, 3]);
                ctx.strokeStyle = "rgba(16, 185, 129, 0.45)";
                ctx.lineWidth = 1.5;
                ctx.moveTo(activeDayPt.x, paddingTop);
                ctx.lineTo(activeDayPt.x, paddingTop + drawH);
                ctx.stroke();
                ctx.restore();

                // Glowing halo on active day point
                ctx.fillStyle = "rgba(16, 185, 129, 0.22)";
                ctx.beginPath();
                ctx.arc(activeDayPt.x, activeDayPt.yEarn, 12, 0, Math.PI * 2);
                ctx.fill();

                // Pin circle on active day point
                ctx.fillStyle = "#FFFFFF";
                ctx.beginPath();
                ctx.arc(activeDayPt.x, activeDayPt.yEarn, 6, 0, Math.PI * 2);
                ctx.fill();
                ctx.strokeStyle = "#047857";
                ctx.lineWidth = 3.5;
                ctx.stroke();

                // Exact single amount for this day
                const earnFormatted = `৳${activeDayPt.data.earnings.toLocaleString('en-US')}`;
                const tipW = 120;
                const tipH = 46;
                let tipX = activeDayPt.x - tipW / 2;
                tipX = Math.max(paddingLeft, Math.min(w - paddingRight - tipW, tipX));
                let tipY = activeDayPt.yEarn - tipH - 12;
                if (tipY < 6) tipY = activeDayPt.yEarn + 16;

                ctx.save();
                ctx.shadowColor = "rgba(15, 23, 42, 0.16)";
                ctx.shadowBlur = 10;
                ctx.shadowOffsetY = 4;
                ctx.fillStyle = "#0F172A";
                ctx.beginPath();
                ctx.roundRect(tipX, tipY, tipW, tipH, 9);
                ctx.fill();
                ctx.restore();

                // Date label in crisp white
                ctx.fillStyle = "#F8FAFC";
                ctx.font = "700 10px 'Plus Jakarta Sans', sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(activeDayPt.data.date, tipX + tipW / 2, tipY + 16);

                // Exact single earnings amount for this day in light green
                ctx.fillStyle = "#A7F3D0";
                ctx.font = "800 13px 'JetBrains Mono', monospace";
                ctx.textAlign = "center";
                ctx.fillText(earnFormatted, tipX + tipW / 2, tipY + 34);
            }

            // Attach canvas mouse hover listener once
            if (!revCanvasListenersAttached) {
                revCanvasListenersAttached = true;

                canvas.addEventListener("mousemove", (e) => {
                    const rect = canvas.getBoundingClientRect();
                    activeRevHoverX = e.clientX - rect.left;
                    drawRevenueTimelineChart();
                });

                canvas.addEventListener("mouseleave", () => {
                    activeRevHoverX = null;
                    drawRevenueTimelineChart();
                });
            }
        }

        // ==================== SUBSCRIPTION HEALTH (CAPSULE BARS WITH DYNAMIC NUMBERS) ====================
        function drawAttendanceBarChart(animProgress = 1.0) {
            const canvas = document.getElementById("attendanceCanvas");
            if (!canvas) return;
            const parent = canvas.parentElement;
            if (!parent) return;

            const w = Math.floor(parent.clientWidth);
            const h = Math.floor(parent.clientHeight);
            if (w <= 10 || h <= 10) return;

            const dpr = window.devicePixelRatio || 1;
            canvas.width = Math.floor(w * dpr);
            canvas.height = Math.floor(h * dpr);
            canvas.style.width = w + "px";
            canvas.style.height = h + "px";

            const ctx = canvas.getContext("2d");
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.scale(dpr, dpr);
            ctx.clearRect(0, 0, w, h);

            // Build dynamic data buckets strictly from REAL allSubscribers and allPayments
            let buckets = [];
            const now = new Date();

            if (healthPeriod === 'daily') {
                for (let i = 6; i >= 0; i--) {
                    const d = new Date(now);
                    d.setDate(d.getDate() - i);
                    const y = d.getFullYear();
                    const m = String(d.getMonth() + 1).padStart(2, '0');
                    const day = String(d.getDate()).padStart(2, '0');
                    const dateStr = `${y}-${m}-${day}`;
                    const label = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

                    const dayPaid = allPayments.filter(p => p.paid_at && p.paid_at.startsWith(dateStr)).length;
                    const dayPending = allSubscribers.filter(s => s.payment_status === 'PENDING' && ((s.added_at && s.added_at.startsWith(dateStr)) || (s.joined_at && s.joined_at.startsWith(dateStr)))).length;

                    buckets.push({
                        label,
                        paid: dayPaid,
                        pending: dayPending
                    });
                }
            } else if (healthPeriod === 'monthly') {
                const weekLabels = ["Week 1", "Week 2", "Week 3", "Week 4"];
                const currentMonth = now.getMonth();
                const currentYear = now.getFullYear();

                buckets = weekLabels.map((lbl, idx) => {
                    const startDay = idx * 7 + 1;
                    const endDay = idx === 3 ? 31 : (idx + 1) * 7;

                    const weekPaid = allPayments.filter(p => {
                        if (!p.paid_at) return false;
                        const pd = new Date(p.paid_at.replace(' ', 'T'));
                        return pd.getFullYear() === currentYear && pd.getMonth() === currentMonth && pd.getDate() >= startDay && pd.getDate() <= endDay;
                    }).length;

                    const weekPending = allSubscribers.filter(s => {
                        if (s.payment_status !== 'PENDING') return false;
                        const dateStr = s.added_at || s.joined_at;
                        if (!dateStr) return false;
                        const sd = new Date(dateStr.replace(' ', 'T'));
                        return sd.getFullYear() === currentYear && sd.getMonth() === currentMonth && sd.getDate() >= startDay && sd.getDate() <= endDay;
                    }).length;

                    return {
                        label: lbl,
                        paid: weekPaid,
                        pending: weekPending
                    };
                });
            } else {
                // Default: Weekly (Mon - Sun of current week)
                const weekDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
                const dayIndices = [1, 2, 3, 4, 5, 6, 0]; // Monday = 1, Sunday = 0

                buckets = weekDays.map((lbl, i) => {
                    const targetDayIndex = dayIndices[i];
                    const dayPaid = allPayments.filter(p => {
                        if (!p.paid_at) return false;
                        const pd = new Date(p.paid_at.replace(' ', 'T'));
                        return pd.getDay() === targetDayIndex;
                    }).length;

                    const dayPending = allSubscribers.filter(s => {
                        if (s.payment_status !== 'PENDING') return false;
                        const dateStr = s.added_at || s.joined_at;
                        if (!dateStr) return false;
                        const sd = new Date(dateStr.replace(' ', 'T'));
                        return sd.getDay() === targetDayIndex;
                    }).length;

                    return {
                        label: lbl,
                        paid: dayPaid,
                        pending: dayPending
                    };
                });
            }

            // Determine dynamic highest number on height bar
            const highestInPeriod = Math.max(...buckets.map(b => b.paid + b.pending), 1);
            let yCeil = 6;
            if (highestInPeriod > 30) yCeil = Math.ceil(highestInPeriod / 10) * 10;
            else if (highestInPeriod > 20) yCeil = 30;
            else if (highestInPeriod > 15) yCeil = 20;
            else if (highestInPeriod > 10) yCeil = 16;
            else if (highestInPeriod > 5) yCeil = 12;
            else yCeil = 6;

            const paddingLeft = 40;
            const paddingRight = 20;
            const paddingTop = 26;
            const paddingBottom = 34;
            const drawW = w - paddingLeft - paddingRight;
            const drawH = h - paddingTop - paddingBottom;
            if (drawW <= 10 || drawH <= 10) return;

            // Draw Background Horizontal Grid Lines with Direct Integer Numbers (NO PERCENTAGES!)
            ctx.strokeStyle = "#F1F5F9";
            ctx.lineWidth = 1;
            const gridLines = 4;
            for (let i = 0; i <= gridLines; i++) {
                const y = paddingTop + (drawH / gridLines) * i;
                ctx.beginPath();
                ctx.moveTo(paddingLeft, y);
                ctx.lineTo(w - paddingRight, y);
                ctx.stroke();

                // Direct number on left bar
                const directNum = Math.round(yCeil * (1 - i / gridLines));
                ctx.fillStyle = "#8E9BAE";
                ctx.font = "600 10px 'JetBrains Mono', monospace";
                ctx.textAlign = "right";
                ctx.fillText(directNum.toString(), paddingLeft - 8, y + 3.5);
            }

            const slotW = drawW / buckets.length;
            // INCREASED BAR WIDTH: Much bolder and wider capsule bars as requested by user!
            const barW = Math.min(52, Math.max(34, slotW * 0.65));
            const baseY = paddingTop + drawH;

            const barCoords = [];

        // activeHealthHoverIndex hoisted
            if (activeHealthMouseX !== null) {
                buckets.forEach((b, idx) => {
                    const cx = paddingLeft + slotW * idx + slotW / 2;
                    if (Math.abs(cx - activeHealthMouseX) <= slotW / 2) {
                        activeHealthHoverIndex = idx;
                    }
                });
            }

            const prog = Math.max(0, Math.min(1, animProgress));
            buckets.forEach((b, idx) => {
                const cx = paddingLeft + slotW * idx + slotW / 2;
                const totalSubs = b.paid + b.pending;
                const paidH = (b.paid / yCeil) * drawH * prog;
                const pendingH = (b.pending / yCeil) * drawH * prog;
                const totalBarH = Math.max(4 * prog, paidH + pendingH);

                barCoords.push({ cx, baseY, barW, totalBarH, paidH, pendingH, data: b });

                const isHovered = (activeHealthHoverIndex === idx);

                // Draw Capsule Bar Background Track (Subtle soft gray slot)
                ctx.fillStyle = isHovered ? "#E2E8F0" : "#F8FAFC";
                ctx.beginPath();
                ctx.roundRect(cx - barW / 2, paddingTop, barW, drawH, 10);
                ctx.fill();

                // Lower Segment: Paid (Emerald Green #10B981)
                if (paidH > 0) {
                    ctx.fillStyle = "#10B981";
                    ctx.beginPath();
                    const radii = (pendingH <= 1) ? 10 : [0, 0, 10, 10];
                    ctx.roundRect(cx - barW / 2, baseY - paidH, barW, paidH, radii);
                    ctx.fill();
                }

                // Upper Segment: Pending (Modern Indigo #6366F1)
                if (pendingH > 0) {
                    ctx.fillStyle = "#6366F1";
                    ctx.beginPath();
                    const radii = (paidH <= 1) ? 10 : [10, 10, 0, 0];
                    ctx.roundRect(cx - barW / 2, baseY - totalBarH, barW, pendingH, radii);
                    ctx.fill();
                }

                // If hovered, draw subtle glowing outline around the active bar
                if (isHovered) {
                    ctx.strokeStyle = "rgba(0, 98, 255, 0.6)";
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.roundRect(cx - barW / 2 - 1, baseY - totalBarH - 1, barW + 2, totalBarH + 2, 10);
                    ctx.stroke();
                }

                // Bottom Period Label
                ctx.fillStyle = isHovered ? "#0062FF" : "#8E9BAE";
                ctx.font = isHovered ? "800 11px 'Plus Jakarta Sans', sans-serif" : "700 10.5px 'Plus Jakarta Sans', sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(b.label, cx, baseY + 18);
            });

            // If a bar is hovered, render informative hover tooltip
            if (activeHealthHoverIndex !== null && barCoords[activeHealthHoverIndex]) {
                const hBar = barCoords[activeHealthHoverIndex];
                const b = hBar.data;
                const tipW = 120;
                const tipH = 50;
                let tipX = hBar.cx - tipW / 2;
                tipX = Math.max(paddingLeft, Math.min(w - paddingRight - tipW, tipX));
                let tipY = hBar.baseY - hBar.totalBarH - tipH - 8;
                if (tipY < 4) tipY = hBar.baseY - hBar.totalBarH + 12;

                ctx.save();
                ctx.shadowColor = "rgba(15, 23, 42, 0.15)";
                ctx.shadowBlur = 10;
                ctx.shadowOffsetY = 3;
                ctx.fillStyle = "#0F172A";
                ctx.beginPath();
                ctx.roundRect(tipX, tipY, tipW, tipH, 8);
                ctx.fill();
                ctx.restore();

                ctx.fillStyle = "#FFFFFF";
                ctx.font = "700 10px 'Plus Jakarta Sans', sans-serif";
                ctx.textAlign = "left";
                ctx.fillText(`${b.label} (Total: ${b.paid + b.pending})`, tipX + 8, tipY + 16);

                ctx.fillStyle = "#10B981";
                ctx.font = "700 10px 'JetBrains Mono', monospace";
                ctx.fillText(`● Paid: ${b.paid}`, tipX + 8, tipY + 31);

                ctx.fillStyle = "#A5B4FC";
                ctx.font = "700 10px 'JetBrains Mono', monospace";
                ctx.fillText(`● Pending: ${b.pending}`, tipX + 8, tipY + 44);
            }

            // Attach canvas mouse hover listener once (stores mouse position globally so monthly/weekly/daily always work accurately)
            if (!healthCanvasListenersAttached) {
                healthCanvasListenersAttached = true;

                canvas.addEventListener("mousemove", (e) => {
                    const rect = canvas.getBoundingClientRect();
                    activeHealthMouseX = e.clientX - rect.left;
                    drawAttendanceBarChart();
                });

                canvas.addEventListener("mouseleave", () => {
                    activeHealthMouseX = null;
                    drawAttendanceBarChart();
                });
            }
        }

