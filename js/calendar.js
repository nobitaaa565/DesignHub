        // ==================== MINI CALENDAR & UPCOMING RENEWALS ====================
        // selectedCalDay hoisted to script top

        function renderCalendar() {
            try {
                const grid = document.getElementById("calendarDaysGrid");
                const title = document.getElementById("calendarMonthYear");
                if (!grid || !title) return;

                if (typeof calCurrentYear !== 'number' || isNaN(calCurrentYear)) calCurrentYear = 2026;
                if (typeof calCurrentMonth !== 'number' || isNaN(calCurrentMonth)) calCurrentMonth = 9;

                const months = [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ];
                title.textContent = `${months[calCurrentMonth]} ${calCurrentYear}`;

                const firstDayIndex = new Date(calCurrentYear, calCurrentMonth, 1).getDay();
                const lastDay = new Date(calCurrentYear, calCurrentMonth + 1, 0).getDate();
                const prevLastDay = new Date(calCurrentYear, calCurrentMonth, 0).getDate();

                const today = new Date();
                const isCurrentMonth = (today.getFullYear() === calCurrentYear && today.getMonth() === calCurrentMonth);
                const currentDayDate = today.getDate();

                // Safe set of days with subscription expiries
                const expiryDays = new Set();
                allSubscribers.forEach(s => {
                    if (s.expires_at) {
                        const safeStr = String(s.expires_at).trim().replace(' ', 'T');
                        const d = new Date(safeStr);
                        if (!isNaN(d.getTime()) && d.getFullYear() === calCurrentYear && d.getMonth() === calCurrentMonth) {
                            expiryDays.add(d.getDate());
                        }
                    }
                });

                let cells = "";

                // Prev month padding
                for (let x = firstDayIndex; x > 0; x--) {
                    cells += `<div class="cal-day-cell other-month">${prevLastDay - x + 1}</div>`;
                }

                // Current month days
                for (let i = 1; i <= lastDay; i++) {
                    const isToday = isCurrentMonth && (i === currentDayDate);
                    const isSelected = (selectedCalDay === i);
                    const hasExpiry = expiryDays.has(i);

                    let dotsHtml = "";
                    if (hasExpiry) {
                        dotsHtml = `<div class="cal-dots-container"><span class="cal-dot dot-expiry" title="Subscription Expiry Due"></span></div>`;
                    }

                    cells += `
                        <div class="cal-day-cell ${isToday ? 'current-day' : ''} ${isSelected ? 'selected-day' : ''} ${hasExpiry ? 'has-event' : ''}" onclick="onCalendarDayClick(${i})">
                            ${i}
                            ${dotsHtml}
                        </div>
                    `;
                }

                // Next month padding
                const totalCells = firstDayIndex + lastDay;
                const remaining = (totalCells % 7 === 0) ? 0 : 7 - (totalCells % 7);
                for (let j = 1; j <= remaining; j++) {
                    cells += `<div class="cal-day-cell other-month">${j}</div>`;
                }

                grid.innerHTML = cells;
            } catch (err) {
                console.error("renderCalendar error:", err);
            }
        }

        function navCalendarMonth(delta) {
            calCurrentMonth += delta;
            if (calCurrentMonth < 0) {
                calCurrentMonth = 11;
                calCurrentYear--;
            } else if (calCurrentMonth > 11) {
                calCurrentMonth = 0;
                calCurrentYear++;
            }
            selectedCalDay = null;
            renderCalendar();
        }

        function jumpCalendarToday() {
            const today = new Date();
            calCurrentMonth = today.getMonth();
            calCurrentYear = today.getFullYear();
            selectedCalDay = today.getDate();
            renderCalendar();
            onCalendarDayClick(selectedCalDay);
        }

        function onCalendarDayClick(day) {
            selectedCalDay = day;
            renderCalendar();

            const months = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ];
            const dateStr = `${months[calCurrentMonth]} ${day}, ${calCurrentYear}`;
            document.getElementById("dayInspectorTitle").textContent = dateStr;

            // Find expiries on this day
            const expiries = allSubscribers.filter(s => {
                if (!s.expires_at) return false;
                const d = new Date(s.expires_at);
                return d.getFullYear() === calCurrentYear && d.getMonth() === calCurrentMonth && d.getDate() === day;
            });

            // Find payments on this day
            const payments = allPayments.filter(p => {
                if (!p.paid_at) return false;
                const d = new Date(p.paid_at);
                return d.getFullYear() === calCurrentYear && d.getMonth() === calCurrentMonth && d.getDate() === day;
            });

            const subtitle = document.getElementById("dayInspectorSubtitle");
            if (subtitle) {
                subtitle.textContent = `${expiries.length} Expiries • ${payments.length} Payments`;
            }

            const content = document.getElementById("dayInspectorContent");
            if (!content) return;

            let html = "";

            if (expiries.length === 0 && payments.length === 0) {
                html = `
                    <div style="text-align: center; padding: 2.25rem 1rem;">
                        <div style="width: 48px; height: 48px; border-radius: 50%; background: var(--bg-subtle); display: inline-flex; align-items: center; justify-content: center; margin-bottom: 0.75rem; color: var(--text-muted);">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                            </svg>
                        </div>
                        <div style="font-size: 0.95rem; font-weight: 700; color: var(--text-dark);">No Events Scheduled</div>
                        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">No subscriber memberships expire or transactions recorded on this date.</p>
                    </div>
                `;
            } else {
                if (expiries.length > 0) {
                    html += `
                        <div style="font-size: 0.75rem; font-weight: 800; color: var(--rose); text-transform: uppercase; margin-bottom: 0.5rem; letter-spacing: 0.04em;">
                            ⚠️ Expiring Memberships (${expiries.length})
                        </div>
                    `;
                    expiries.forEach(s => {
                        html += `
                            <div class="day-inspector-item" style="border-left: 3.5px solid var(--rose);">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                    <div>
                                        <div style="font-weight: 700; font-size: 0.88rem; color: var(--text-dark);">${s.name || 'Member'}</div>
                                        <div style="font-size: 0.78rem; color: var(--text-muted);">${s.email}</div>
                                        <div style="font-size: 0.74rem; color: var(--blue-primary); font-weight: 600; margin-top: 0.2rem;">${s.team_name || 'Team'} • ${s.package || '3 Months'}</div>
                                    </div>
                                    <button class="btn btn-secondary" style="font-size: 0.72rem; padding: 0.3rem 0.65rem;" onclick="copyRenewalReminder('${s.email}', '${s.expires_at}', '${s.team_name || 'Canva Pro'}')">
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                                        </svg>
                                        <span>Copy Reminder</span>
                                    </button>
                                </div>
                            </div>
                        `;
                    });
                }

                if (payments.length > 0) {
                    html += `
                        <div style="font-size: 0.75rem; font-weight: 800; color: var(--emerald); text-transform: uppercase; margin-top: 1rem; margin-bottom: 0.5rem; letter-spacing: 0.04em;">
                            ✓ Verified Transactions (${payments.length})
                        </div>
                    `;
                    payments.forEach(p => {
                        html += `
                            <div class="day-inspector-item" style="border-left: 3.5px solid var(--emerald);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="font-weight: 800; font-size: 0.92rem; color: var(--emerald);">৳${parseFloat(p.amount || 0).toFixed(2)}</div>
                                        <div style="font-size: 0.78rem; color: var(--text-dark);">${p.customer_email || 'Customer'}</div>
                                        <div style="font-size: 0.72rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">TrxID: ${p.trx_id || 'N/A'} • ${(p.provider || 'bKash').toUpperCase()}</div>
                                    </div>
                                    <span class="badge badge-success" style="font-size: 0.7rem;">Verified</span>
                                </div>
                            </div>
                        `;
                    });
                }
            }

            content.innerHTML = html;

            // Hook up "View in Roster" button
            const btnFilter = document.getElementById("btnFilterRosterByDay");
            if (btnFilter) {
                btnFilter.onclick = () => {
                    closeModal("dayInspectorModal");
                    switchMainView("subscribers");
                    const padMonth = String(calCurrentMonth + 1).padStart(2, '0');
                    const padDay = String(day).padStart(2, '0');
                    const dateFilterQuery = `${calCurrentYear}-${padMonth}-${padDay}`;
                    const searchInput = document.getElementById("globalQuickSearch");
                    if (searchInput) {
                        searchInput.value = dateFilterQuery;
                        filterSubscribers();
                    }
                };
            }

            openModal("dayInspectorModal");
        }


        // ==================== EXPANDED BIG CALENDAR CONTROLLER ====================
        // bigCalSelectedDay hoisted
        // bigCalFilterType hoisted

        function openBigCalendarModal() {
            try {
                const today = new Date();
                if (selectedCalDay) {
                    bigCalSelectedDay = selectedCalDay;
                } else if (today.getFullYear() === calCurrentYear && today.getMonth() === calCurrentMonth) {
                    bigCalSelectedDay = today.getDate();
                } else {
                    bigCalSelectedDay = 1;
                }

                // Populate team filter options in big calendar
                const teamSelect = document.getElementById("bigCalTeamFilter");
                if (teamSelect) {
                    const currentVal = teamSelect.value || "ALL";
                    let opts = `<option value="ALL">All Canva Teams</option>`;
                    allTeams.forEach(t => {
                        opts += `<option value="${t}">${t}</option>`;
                    });
                    teamSelect.innerHTML = opts;
                    if (currentVal && (currentVal === "ALL" || allTeams.includes(currentVal))) {
                        teamSelect.value = currentVal;
                    } else {
                        teamSelect.value = "ALL";
                    }
                }

                renderBigCalendar();

                const modal = document.getElementById("bigCalendarModal");
                if (modal) {
                    modal.classList.add("active");
                }
            } catch (err) {
                console.error("Error opening big calendar modal:", err);
                // Fallback direct open
                const modal = document.getElementById("bigCalendarModal");
                if (modal) modal.classList.add("active");
            }
        }

        function navBigCalendarMonth(delta) {
            calCurrentMonth += delta;
            if (calCurrentMonth < 0) {
                calCurrentMonth = 11;
                calCurrentYear--;
            } else if (calCurrentMonth > 11) {
                calCurrentMonth = 0;
                calCurrentYear++;
            }
            bigCalSelectedDay = 1;
            selectedCalDay = null;
            renderCalendar(); // Keep mini calendar synced
            renderBigCalendar();
        }

        function jumpBigCalendarToday() {
            const today = new Date();
            calCurrentMonth = today.getMonth();
            calCurrentYear = today.getFullYear();
            bigCalSelectedDay = today.getDate();
            selectedCalDay = today.getDate();
            renderCalendar(); // Keep mini calendar synced
            renderBigCalendar();
        }

        function setBigCalendarFilter(type) {
            bigCalFilterType = type;
            const chips = ['all', 'expiries', 'payments', 'pending'];
            chips.forEach(c => {
                const el = document.getElementById(`bigCalFilter_${c}`);
                if (el) el.classList.toggle("active", c === type);
            });
            renderBigCalendar();
        }

        function renderBigCalendar() {
            const titleEl = document.getElementById("bigCalMonthYear");
            const gridEl = document.getElementById("bigCalDaysGrid");
            const statsRibbonEl = document.getElementById("bigCalStatsRibbon");
            if (!titleEl || !gridEl) return;

            const months = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ];
            titleEl.textContent = `${months[calCurrentMonth]} ${calCurrentYear}`;

            const firstDayIndex = new Date(calCurrentYear, calCurrentMonth, 1).getDay();
            const lastDay = new Date(calCurrentYear, calCurrentMonth + 1, 0).getDate();
            const prevLastDay = new Date(calCurrentYear, calCurrentMonth, 0).getDate();

            const today = new Date();
            const isCurrentMonth = (today.getFullYear() === calCurrentYear && today.getMonth() === calCurrentMonth);
            const currentDayDate = today.getDate();

            const selectedTeam = document.getElementById("bigCalTeamFilter")?.value || "ALL";
            const searchVal = (document.getElementById("bigCalSearchInput")?.value || "").toLowerCase().trim();

            // Group events for the month
            const dayEvents = {};
            for (let d = 1; d <= lastDay; d++) {
                dayEvents[d] = { expiries: [], payments: [], pending: [] };
            }

            let monthTotalExpiries = 0;
            let monthTotalExpRevenue = 0;
            let monthTotalPayments = 0;
            let monthTotalPayRevenue = 0;
            let monthTotalPending = 0;

            allSubscribers.forEach(s => {
                if (selectedTeam !== "ALL" && (s.team_name || "Carmella Elan") !== selectedTeam) return;
                if (searchVal) {
                    const matchName = (s.name || '').toLowerCase().includes(searchVal);
                    const matchEmail = (s.email || '').toLowerCase().includes(searchVal);
                    const matchTrx = (s.trx_id || '').toLowerCase().includes(searchVal);
                    if (!matchName && !matchEmail && !matchTrx) return;
                }

                if (s.expires_at) {
                    const d = new Date(s.expires_at);
                    if (d.getFullYear() === calCurrentYear && d.getMonth() === calCurrentMonth) {
                        const dayNum = d.getDate();
                        if (dayEvents[dayNum]) {
                            dayEvents[dayNum].expiries.push(s);
                            monthTotalExpiries++;
                            const pkgStr = (s.package || '').toLowerCase();
                            const amt = pkgStr.includes("12") ? 1200 : (pkgStr.includes("6") ? 650 : 350);
                            monthTotalExpRevenue += amt;
                        }
                    }
                }

                if (s.payment_status === 'PENDING') {
                    const d = new Date(s.added_at || s.expires_at);
                    if (d && d.getFullYear() === calCurrentYear && d.getMonth() === calCurrentMonth) {
                        const dayNum = d.getDate();
                        if (dayEvents[dayNum]) {
                            dayEvents[dayNum].pending.push(s);
                            monthTotalPending++;
                        }
                    }
                }
            });

            allPayments.forEach(p => {
                if (selectedTeam !== "ALL" && (p.team_name || "Carmella Elan") !== selectedTeam) return;
                if (searchVal) {
                    const matchName = (p.name || '').toLowerCase().includes(searchVal);
                    const matchEmail = (p.email || '').toLowerCase().includes(searchVal);
                    const matchTrx = (p.trx_id || '').toLowerCase().includes(searchVal);
                    if (!matchName && !matchEmail && !matchTrx) return;
                }

                if (p.paid_at) {
                    const d = new Date(p.paid_at);
                    if (d.getFullYear() === calCurrentYear && d.getMonth() === calCurrentMonth) {
                        const dayNum = d.getDate();
                        if (dayEvents[dayNum]) {
                            dayEvents[dayNum].payments.push(p);
                            monthTotalPayments++;
                            monthTotalPayRevenue += (parseFloat(p.amount) || 0);
                        }
                    }
                }
            });

            // Find busiest expiry day
            let peakDay = null;
            let peakCount = 0;
            for (let d = 1; d <= lastDay; d++) {
                if (dayEvents[d].expiries.length > peakCount) {
                    peakCount = dayEvents[d].expiries.length;
                    peakDay = d;
                }
            }

            // Render Stats Ribbon
            if (statsRibbonEl) {
                statsRibbonEl.innerHTML = `
                    <div class="big-cal-kpi-card">
                        <div class="big-cal-kpi-icon" style="background: rgba(239, 68, 68, 0.12); color: #DC2626;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/></svg>
                        </div>
                        <div>
                            <div style="font-size: 0.68rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">MONTHLY EXPIRIES</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #DC2626;">${monthTotalExpiries} <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 600;">(~৳${monthTotalExpRevenue.toLocaleString('en-US')})</span></div>
                        </div>
                    </div>

                    <div class="big-cal-kpi-card">
                        <div class="big-cal-kpi-icon" style="background: rgba(16, 185, 129, 0.12); color: #059669;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
                        </div>
                        <div>
                            <div style="font-size: 0.68rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">VERIFIED PAYMENTS</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #059669;">৳${monthTotalPayRevenue.toLocaleString('en-US')} <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 600;">(${monthTotalPayments} Trx)</span></div>
                        </div>
                    </div>

                    <div class="big-cal-kpi-card">
                        <div class="big-cal-kpi-icon" style="background: rgba(245, 158, 11, 0.12); color: #D97706;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        </div>
                        <div>
                            <div style="font-size: 0.68rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">PENDING ORDERS</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #D97706;">${monthTotalPending} <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 600;">Orders</span></div>
                        </div>
                    </div>

                    <div class="big-cal-kpi-card">
                        <div class="big-cal-kpi-icon" style="background: var(--blue-light); color: var(--blue-primary);">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
                        </div>
                        <div>
                            <div style="font-size: 0.68rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">BUSIEST EXPIRY DAY</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: var(--text-dark);">
                                ${peakDay ? `${months[calCurrentMonth].slice(0, 3)} ${peakDay} (${peakCount})` : 'None'}
                            </div>
                        </div>
                    </div>
                `;
            }

            // Generate grid cells
            let cellsHtml = '';

            // Prev month padding
            for (let x = firstDayIndex; x > 0; x--) {
                const pDay = prevLastDay - x + 1;
                cellsHtml += `
                    <div class="big-cal-cell other-month">
                        <div class="big-cal-cell-top">
                            <span class="big-cal-day-num" style="color: var(--text-faint);">${pDay}</span>
                        </div>
                    </div>
                `;
            }

            if (!bigCalSelectedDay || bigCalSelectedDay > lastDay) {
                bigCalSelectedDay = isCurrentMonth ? currentDayDate : 1;
            }

            // Days of current month
            for (let day = 1; day <= lastDay; day++) {
                const isToday = isCurrentMonth && (day === currentDayDate);
                const isSelected = (day === bigCalSelectedDay);
                const ev = dayEvents[day];

                const showExpiries = (bigCalFilterType === 'all' || bigCalFilterType === 'expiries') && ev.expiries.length > 0;
                const showPayments = (bigCalFilterType === 'all' || bigCalFilterType === 'payments') && ev.payments.length > 0;
                const showPending = (bigCalFilterType === 'all' || bigCalFilterType === 'pending') && ev.pending.length > 0;

                let badgesHtml = '';
                if (showExpiries) {
                    badgesHtml += `
                        <div class="big-cal-badge badge-expiry" title="${ev.expiries.length} Expiries">
                            <span>⚠️ ${ev.expiries.length} Due</span>
                        </div>
                    `;
                }
                if (showPayments) {
                    const paySum = ev.payments.reduce((acc, p) => acc + (parseFloat(p.amount) || 0), 0);
                    badgesHtml += `
                        <div class="big-cal-badge badge-payment" title="${ev.payments.length} Payments (৳${paySum})">
                            <span>💳 ${ev.payments.length} Paid (৳${paySum})</span>
                        </div>
                    `;
                }
                if (showPending) {
                    badgesHtml += `
                        <div class="big-cal-badge badge-pending" title="${ev.pending.length} Pending">
                            <span>🕒 ${ev.pending.length} Pending</span>
                        </div>
                    `;
                }

                cellsHtml += `
                    <div class="big-cal-cell ${isToday ? 'current-day' : ''} ${isSelected ? 'selected-day' : ''}" onclick="onBigCalendarDayClick(${day})">
                        <div class="big-cal-cell-top">
                            <span class="big-cal-day-num">${day}</span>
                            ${isToday ? '<span class="big-cal-today-badge">Today</span>' : ''}
                        </div>
                        <div class="big-cal-badges-list">
                            ${badgesHtml}
                        </div>
                    </div>
                `;
            }

            // Next month padding
            const totalCells = firstDayIndex + lastDay;
            const remaining = (totalCells % 7 === 0) ? 0 : 7 - (totalCells % 7);
            for (let j = 1; j <= remaining; j++) {
                cellsHtml += `
                    <div class="big-cal-cell other-month">
                        <div class="big-cal-cell-top">
                            <span class="big-cal-day-num" style="color: var(--text-faint);">${j}</span>
                        </div>
                    </div>
                `;
            }

            gridEl.innerHTML = cellsHtml;

            // Render the selected day sidebar
            renderBigCalendarDaySidebar(bigCalSelectedDay, dayEvents[bigCalSelectedDay] || { expiries: [], payments: [], pending: [] });
        }

        function onBigCalendarDayClick(day) {
            bigCalSelectedDay = day;
            selectedCalDay = day;
            renderBigCalendar();
            renderCalendar(); // Keep mini calendar synced
        }

        function renderBigCalendarDaySidebar(day, ev) {
            const sidebar = document.getElementById("bigCalDaySidebar");
            if (!sidebar) return;

            const months = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ];
            const dateObj = new Date(calCurrentYear, calCurrentMonth, day);
            const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
            const dayName = dayNames[dateObj.getDay()];
            const dateStr = `${dayName}, ${months[calCurrentMonth]} ${day}, ${calCurrentYear}`;

            const expCount = ev ? ev.expiries.length : 0;
            const payCount = ev ? ev.payments.length : 0;
            const pendCount = ev ? ev.pending.length : 0;
            const paySum = ev ? ev.payments.reduce((acc, p) => acc + (parseFloat(p.amount) || 0), 0) : 0;

            let itemsHtml = '';

            if (expCount === 0 && payCount === 0 && pendCount === 0) {
                itemsHtml = `
                    <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted);">
                        <div style="width: 44px; height: 44px; border-radius: 50%; background: #FFFFFF; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 0.75rem; border: 1px solid var(--border);">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                        </div>
                        <div style="font-weight: 700; color: var(--text-dark); font-size: 0.9rem;">No Schedule on this Date</div>
                        <div style="font-size: 0.78rem; margin-top: 0.25rem;">No expiring memberships, verified payments, or pending orders on this day.</div>
                    </div>
                `;
            } else {
                // Expiries section
                if (expCount > 0) {
                    itemsHtml += `
                        <div style="font-size: 0.72rem; font-weight: 800; color: var(--rose); text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.05em; display: flex; align-items: center; justify-content: space-between;">
                            <span>⚠️ EXPIRING MEMBERSHIPS (${expCount})</span>
                        </div>
                    `;
                    ev.expiries.forEach(s => {
                        itemsHtml += `
                            <div class="big-cal-item-card" style="border-left: 3.5px solid var(--rose);">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                    <div>
                                        <div style="font-weight: 800; font-size: 0.85rem; color: var(--text-dark);">${s.name || 'Member'}</div>
                                        <div style="font-size: 0.76rem; color: var(--text-muted); word-break: break-all;">${s.email}</div>
                                        <div style="font-size: 0.72rem; color: var(--blue-primary); font-weight: 700; margin-top: 0.25rem;">
                                            ${s.team_name || 'Carmella Elan'} • ${s.package || '3 Months'}
                                        </div>
                                    </div>
                                </div>
                                <div style="display: flex; gap: 0.4rem; margin-top: 0.55rem; padding-top: 0.45rem; border-top: 1px solid var(--border-subtle);">
                                    <button class="btn btn-secondary" style="flex: 1; font-size: 0.72rem; padding: 0.3rem 0.5rem;" onclick="copyRenewalReminder('${s.email}', '${s.expires_at}', '${s.team_name || 'Canva Pro'}')">
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                                        <span>Copy Reminder</span>
                                    </button>
                                    <button class="btn btn-secondary" style="font-size: 0.72rem; padding: 0.3rem 0.55rem;" onclick="jumpToSubscriberInTable('${s.email}')" title="Find in Roster">
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                                    </button>
                                </div>
                            </div>
                        `;
                    });
                }

                // Payments section
                if (payCount > 0) {
                    itemsHtml += `
                        <div style="font-size: 0.72rem; font-weight: 800; color: var(--emerald); text-transform: uppercase; margin: 0.75rem 0 0.4rem 0; letter-spacing: 0.05em; display: flex; align-items: center; justify-content: space-between;">
                            <span>💳 VERIFIED PAYMENTS (${payCount} • ৳${paySum})</span>
                        </div>
                    `;
                    ev.payments.forEach(p => {
                        itemsHtml += `
                            <div class="big-cal-item-card" style="border-left: 3.5px solid var(--emerald);">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                    <div>
                                        <div style="font-weight: 800; font-size: 0.85rem; color: var(--text-dark);">৳${p.amount} • ${p.provider || 'bKash'}</div>
                                        <div style="font-size: 0.75rem; color: var(--text-muted);">${p.name || p.email}</div>
                                        <div style="font-size: 0.72rem; color: var(--text-body); font-family: monospace; margin-top: 0.2rem;">
                                            TrxID: <strong>${p.trx_id || 'N/A'}</strong>
                                        </div>
                                    </div>
                                    <button class="btn btn-secondary" style="font-size: 0.72rem; padding: 0.25rem 0.45rem;" onclick="copyTextToClipboard('${p.trx_id}', 'TrxID Copied!')" title="Copy TrxID">
                                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                                    </button>
                                </div>
                            </div>
                        `;
                    });
                }

                // Pending section
                if (pendCount > 0) {
                    itemsHtml += `
                        <div style="font-size: 0.72rem; font-weight: 800; color: #D97706; text-transform: uppercase; margin: 0.75rem 0 0.4rem 0; letter-spacing: 0.05em;">
                            <span>🕒 PENDING ORDERS (${pendCount})</span>
                        </div>
                    `;
                    ev.pending.forEach(s => {
                        itemsHtml += `
                            <div class="big-cal-item-card" style="border-left: 3.5px solid #D97706;">
                                <div style="font-weight: 800; font-size: 0.84rem; color: var(--text-dark);">${s.name || 'Customer'}</div>
                                <div style="font-size: 0.75rem; color: var(--text-muted);">${s.email}</div>
                                <div style="font-size: 0.72rem; color: #D97706; font-weight: 700; margin-top: 0.2rem;">
                                    ${s.package || '3 Months'} • Awaiting Verification
                                </div>
                            </div>
                        `;
                    });
                }
            }

            const totalItems = expCount + payCount + pendCount;
            sidebar.innerHTML = `
                <div class="big-cal-sidebar-header">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.25rem;">
                        <span style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: var(--blue-primary); letter-spacing: 0.05em;">Selected Date Schedule</span>
                        <span class="team-stat-tag tag-amber" style="font-size: 0.68rem; padding: 0.15rem 0.5rem;">${totalItems} ${totalItems === 1 ? 'event' : 'events'}</span>
                    </div>
                    <div style="font-size: 0.95rem; font-weight: 800; color: var(--text-dark);">${dateStr}</div>
                    <div style="font-size: 0.74rem; color: var(--text-muted); margin-top: 0.15rem;">
                        ${expCount} Expiries • ${payCount} Payments (৳${paySum}) ${pendCount > 0 ? `• ${pendCount} Pending` : ''}
                    </div>
                </div>

                <div class="big-cal-sidebar-list">
                    ${itemsHtml}
                </div>
            `;
        }

        function viewBigCalDayInTable() {
            closeModal("bigCalendarModal");
            if (!bigCalSelectedDay) return;
            const padMonth = String(calCurrentMonth + 1).padStart(2, '0');
            const padDay = String(bigCalSelectedDay).padStart(2, '0');
            const isoDateStr = `${calCurrentYear}-${padMonth}-${padDay}`;
            switchMainView("subscribers");
            const searchInput = document.getElementById("searchSubInput");
            if (searchInput) {
                searchInput.value = isoDateStr;
                filterSubscribers();
            }
        }

        function jumpToSubscriberInTable(email) {
            closeModal("bigCalendarModal");
            switchMainView("subscribers");
            const searchInput = document.getElementById("searchSubInput");
            if (searchInput) {
                searchInput.value = email;
                filterSubscribers();
            }
        }

        function copyTextToClipboard(text, msg) {
            if (!text) return;
            navigator.clipboard.writeText(text);
            showToast(msg || "Copied to clipboard!", "success");
        }

        function copyRenewalReminder(email, expDate, teamName) {
            const cleanDate = expDate ? expDate.substring(0, 10) : "today";
            const message = `Assalamu Alaikum! Your Canva Pro access for ${email} (${teamName}) is due for renewal on ${cleanDate}. To ensure continuous access without interruption, please confirm your renewal. Thank you! - DesignHub Admin`;
            navigator.clipboard.writeText(message);
            showToast(`Renewal reminder message for ${email} copied!`, "success");
        }

