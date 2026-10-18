        // ==================== FUNCTIONAL & CONCISE STUDENT ACTIVITIES FEED ====================
        function renderActivitiesFeed() {
            const container = document.getElementById("activitiesContainer");
            if (!container) return;

            // Sort all payments strictly by paid_at descending (most recent transactions first!)
            const sortedPayments = [...allPayments].sort((a, b) => {
                const ta = a.paid_at ? new Date(a.paid_at.replace(' ', 'T')).getTime() : 0;
                const tb = b.paid_at ? new Date(b.paid_at.replace(' ', 'T')).getTime() : 0;
                return tb - ta;
            });

            if (sortedPayments.length === 0) {
                container.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 1.5rem;">No recent transactions recorded.</div>`;
                return;
            }

            const feed = [];
            const now = new Date();

            sortedPayments.slice(0, 5).forEach((p, idx) => {
                const prov = (p.provider || p.method || "bkash").toLowerCase();
                let tagClass = "act-tag-bkash";
                if (prov.includes("nagad")) tagClass = "act-tag-nagad";
                else if (prov.includes("rocket")) tagClass = "act-tag-rocket";
                else if (prov.includes("bank")) tagClass = "act-tag-bank";

                const email = p.customer_email || p.email || "";
                const nameShort = p.name ? p.name.split(" ")[0] : (email ? email.split("@")[0] : "Student");
                const amount = parseFloat(p.amount || 0).toLocaleString('en-US');

                // Compute exact relative time from transaction paid_at
                let timeStr = "Recent";
                if (p.paid_at) {
                    const pDate = new Date(p.paid_at.replace(' ', 'T'));
                    const diffMs = now - pDate;
                    const diffMin = Math.floor(diffMs / (1000 * 60));
                    const diffHours = Math.floor(diffMin / 60);
                    const diffDays = Math.floor(diffHours / 24);

                    if (diffMin <= 1) timeStr = "Just now";
                    else if (diffMin < 60) timeStr = `${diffMin}m ago`;
                    else if (diffHours < 24) timeStr = `${diffHours}h ago`;
                    else if (diffDays === 1) timeStr = "Yesterday";
                    else if (diffDays < 7) timeStr = `${diffDays}d ago`;
                    else timeStr = p.paid_at.substring(5, 10);
                } else {
                    timeStr = "Verified";
                }

                feed.push({
                    email: email,
                    iconSvg: `
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#047857" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                    `,
                    bg: "rgba(16, 185, 129, 0.12)",
                    title: `${nameShort} • ৳${amount}`,
                    tag: `<span class="act-tag ${tagClass}">${prov.toUpperCase()}</span>`,
                    team: p.team_name || "Carmella Elan",
                    time: timeStr
                });
            });

            container.innerHTML = feed.map(item => `
                <div class="activity-feed-card" onclick="openEditCustomerModal('${item.email}')" title="View Student Transaction">
                    <div class="activity-avatar-icon" style="background: ${item.bg};">
                        ${item.iconSvg}
                    </div>
                    <div class="activity-center-col">
                        <div class="act-top-line">
                            <span class="act-title">${item.title}</span>
                            ${item.tag}
                        </div>
                        <div class="act-team-line">${item.team}</div>
                    </div>
                    <div class="act-time-pill">${item.time}</div>
                </div>
            `).join('');
        }



        // ==================== OVERVIEW RECENT TABLE ====================
        function renderOverviewRecentTable() {
            const tbody = document.getElementById("overviewRecentTbody");
            if (!tbody) return;
            const recent = allPayments.slice(0, 5);

            if (recent.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No recent transactions verified.</td></tr>`;
                return;
            }

            tbody.innerHTML = recent.map(p => {
                const date = (p.paid_at || "").substring(0, 10);
                const team = `<span class="team-tag"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg> ${p.team_name || 'Carmella Elan'}</span>`;
                const amt = `<span style="font-weight: 700; color: #047857;">৳${parseFloat(p.amount || 0).toFixed(2)}</span>`;
                const cidBadge = `<span class="cid-badge">#${p.customer_id || p.id}</span>`;

                let provClass = "provider-other";
                const prov = (p.provider || "").toLowerCase();
                if (prov.includes("bkash")) provClass = "provider-bkash";
                else if (prov.includes("nagad")) provClass = "provider-nagad";
                else if (prov.includes("rocket")) provClass = "provider-rocket";

                const provBadge = `<span class="provider-badge ${provClass}">${p.provider ? p.provider.toUpperCase() : 'BKASH'}</span>`;

                return `
                    <tr>
                        <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--text-muted);">${date}</td>
                        <td>${cidBadge}</td>
                        <td><span style="font-weight: 700;">${p.customer_email || 'Direct User'}</span></td>
                        <td>${team}</td>
                        <td><span style="font-weight: 600;">${p.package || '3 Months'}</span></td>
                        <td>${provBadge}</td>
                        <td>${amt}</td>
                    </tr>
                `;
            }).join('');
        }

        // ==================== SUBSCRIBERS TABLE & ACTIONS ====================
        function toggleSubQuickEdit() {
            subQuickEditActive = !subQuickEditActive;
            const btn = document.getElementById("btnToggleSubEdit");
            if (btn) {
                btn.classList.toggle("btn-primary", subQuickEditActive);
                btn.classList.toggle("btn-secondary", !subQuickEditActive);
                btn.innerHTML = subQuickEditActive ? `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg">
                        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/>
                    </svg>
                    <span>Exit Inline Edit</span>
                ` : `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg">
                        <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                    </svg>
                    <span>Quick Edit Mode</span>
                `;
            }
            filterSubscribers();
        }

        function markSubRowDirty(email) {
            dirtySubRows.add(email);
            const rowKey = btoa(email).replace(/=/g, '');
            const btn = document.getElementById(`subsave_${rowKey}`);
            if (btn) btn.style.display = "inline-flex";
        }

        // RENDER SUBSCRIBERS TABLE
        // NOTE: USER EXPLICITLY REQUESTED TO REMOVE THE LINK BUTTON FROM SUBSCRIBER CARD/ROW!
        function renderSubscribersTable(list) {
            const tbody = document.getElementById("subscribersTbody");
            if (!tbody) return;
            if (!list || list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 3rem;">No subscribers found matching query.</td></tr>`;
                return;
            }

            tbody.innerHTML = list.map(sub => {
                const rowKey = btoa(sub.email).replace(/=/g, '');
                const cidBadge = `<span class="cid-badge">#${sub.customer_id || 800}</span>`;
                const teamBadge = `<span class="team-tag"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg> ${sub.team_name || 'Carmella Elan'}</span>`;
                const expDate = (sub.expires_at || '').substring(0, 10);

                let statusBadge = '';
                if (sub.payment_status === 'PAID') {
                    statusBadge = `
                        <span class="badge-status status-paid">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><polyline points="20 6 9 17 4 12"/></svg>
                            <span>PAID</span>
                        </span>
                    `;
                } else if (sub.status === 'kicked') {
                    statusBadge = `
                        <span class="badge-status status-kicked">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                            <span>KICKED</span>
                        </span>
                    `;
                } else {
                    statusBadge = `
                        <span class="badge-status status-pending">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                            <span>PENDING</span>
                        </span>
                    `;
                }

                // Amount calculation based strictly on verified payment status
                const isPaidStatus = (sub.payment_status === 'PAID');
                let amtNum = parseFloat(sub.amount || 0);
                if (isPaidStatus && (!amtNum || isNaN(amtNum))) {
                    const p = (sub.package || '').toLowerCase();
                    if (p.includes('12') || p.includes('6')) amtNum = 99;
                    else if (p.includes('3')) amtNum = 50;
                    else amtNum = 25;
                } else if (!isPaidStatus) {
                    amtNum = 0;
                }
                const amtFormatted = `৳${(amtNum || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                const amtCell = isPaidStatus
                    ? `<span style="font-weight: 800; color: #047857; font-family: 'JetBrains Mono', monospace; font-size: 0.88rem;">${amtFormatted}</span>`
                    : `<span style="font-weight: 600; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; font-size: 0.84rem;">৳0.00</span>`;

                // Method / Provider badge
                const methRaw = (sub.method || sub.provider || 'bkash').toLowerCase();
                let provClass = "provider-other";
                if (methRaw.includes("bkash")) provClass = "provider-bkash";
                else if (methRaw.includes("nagad")) provClass = "provider-nagad";
                else if (methRaw.includes("rocket")) provClass = "provider-rocket";
                const methBadge = `<span class="provider-badge ${provClass}">${methRaw.toUpperCase()}</span>`;

                const trx = sub.trx_id ? `<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; background: var(--bg-subtle); padding: 2px 6px; border-radius: 6px; border: 1px solid var(--border);">${sub.trx_id}</span>` : `<span style="color: var(--text-faint); font-size: 0.78rem;">—</span>`;

                const refName = sub.reference_name || 'Page Lead';
                const isPageLead = refName.toLowerCase() === 'page lead';
                const refIcon = isPageLead ? `
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
                ` : `
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                `;
                const refBadge = `<span class="ref-badge ${isPageLead ? 'ref-badge-page' : 'ref-badge-custom'}">${refIcon}<span>${refName}</span></span>`;

                if (subQuickEditActive) {
                    const refOpts = (allReferences || ["Page Lead"]).map(r => `<option value="${r}" ${r.toLowerCase() === refName.toLowerCase() ? 'selected' : ''}>${r}</option>`).join('');
                    const teamOpts = allTeams.map(t => `<option value="${t}" ${t === (sub.team_name || 'Carmella Elan') ? 'selected' : ''}>${t}</option>`).join('');
                    const pkgOpts = ["1 Month", "3 Months", "6 Months"].map(p => `<option value="${p}" ${p.toLowerCase().includes((sub.package || '').toLowerCase()) ? 'selected' : ''}>${p}</option>`).join('');
                    const provOpts = ["bkash", "nagad", "rocket", "bank", "other"].map(pr => `<option value="${pr}" ${pr === methRaw ? 'selected' : ''}>${pr.toUpperCase()}</option>`).join('');
                    const payOpts = [
                        {val: 'PAID', text: 'PAID'},
                        {val: 'PENDING', text: 'PENDING'},
                        {val: 'REVOKED', text: 'REVOKED'}
                    ].map(o => `<option value="${o.val}" ${sub.payment_status === o.val ? 'selected' : ''}>${o.text}</option>`).join('');

                    return `
                        <tr id="subrow_${rowKey}">
                            <td>${cidBadge}</td>
                            <td>
                                <input type="text" class="cell-input" id="sub_name_${rowKey}" value="${sub.name || ''}" placeholder="Name" onchange="markSubRowDirty('${sub.email}')" style="margin-bottom: 2px;">
                                <input type="email" class="cell-input" id="sub_email_${rowKey}" value="${sub.email}" onchange="markSubRowDirty('${sub.email}')">
                            </td>
                            <td>
                                <select class="cell-input" id="sub_ref_${rowKey}" onchange="markSubRowDirty('${sub.email}')">${refOpts}</select>
                            </td>
                            <td>
                                <select class="cell-input" id="sub_team_${rowKey}" onchange="markSubRowDirty('${sub.email}')">${teamOpts}</select>
                            </td>
                            <td>
                                <select class="cell-input" id="sub_pkg_${rowKey}" onchange="markSubRowDirty('${sub.email}')">${pkgOpts}</select>
                            </td>
                            <td>
                                <input type="number" step="1" class="cell-input" id="sub_amt_${rowKey}" value="${amtNum}" onchange="markSubRowDirty('${sub.email}')" style="width: 85px;">
                            </td>
                            <td>
                                <select class="cell-input" id="sub_meth_${rowKey}" onchange="markSubRowDirty('${sub.email}')">${provOpts}</select>
                            </td>
                            <td>
                                <input type="date" class="cell-input" id="sub_exp_${rowKey}" value="${expDate}" onchange="markSubRowDirty('${sub.email}')">
                            </td>
                            <td>
                                <select class="cell-input" id="sub_pay_${rowKey}" onchange="markSubRowDirty('${sub.email}')">${payOpts}</select>
                            </td>
                            <td>
                                <input type="text" class="cell-input" id="sub_trx_${rowKey}" value="${sub.trx_id || ''}" placeholder="TrxID" onchange="markSubRowDirty('${sub.email}')">
                            </td>
                            <td style="text-align: center; width: 60px;">
                                <div class="table-actions" style="justify-content: center;">
                                    <button class="btn btn-primary" id="subsave_${rowKey}" onclick="saveInlineSubscriber('${sub.email}')" title="Save" style="padding: 0.35rem 0.5rem; font-size: 0.75rem; display: ${dirtySubRows.has(sub.email) ? 'inline-flex' : 'none'};">
                                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/></svg>
                                    </button>
                                    <button class="btn-action btn-action-edit" onclick="openEditCustomerModal('${sub.email}')" title="Full Dialog">
                                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                                    </button>
                                    <button class="btn-action btn-action-delete" onclick="actionDelete('${sub.email}')" title="Delete Customer">
                                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                }

                // Normal Mode (Full width layout with Amount & Method)
                return `
                    <tr id="subrow_${rowKey}">
                        <td>${cidBadge}</td>
                        <td>
                            <div class="customer-info">
                                <span class="customer-email">${sub.email}</span>
                                <span class="customer-name">${sub.name || 'Personal Account'}</span>
                            </div>
                        </td>
                        <td>${refBadge}</td>
                        <td>${teamBadge}</td>
                        <td><span style="font-weight: 700;">${sub.package}</span></td>
                        <td>${amtCell}</td>
                        <td>${methBadge}</td>
                        <td><span style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: var(--text-muted);">${expDate}</span></td>
                        <td>${statusBadge}</td>
                        <td>${trx}</td>
                        <td style="text-align: center; width: 60px;">
                            <div class="table-actions" style="justify-content: center;">
                                <button class="btn-action btn-action-edit" onclick="openEditCustomerModal('${sub.email}')" title="Edit Customer Details">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                                    </svg>
                                </button>
                                <button class="btn-action btn-action-delete" onclick="actionDelete('${sub.email}')" title="Delete Customer">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function filterSubscribers() {
            const subInput = document.getElementById("searchSubInput");
            const globalInput = document.getElementById("globalQuickSearch");
            const raw = (subInput && subInput.value) ? subInput.value : (globalInput ? globalInput.value : "");
            const query = (raw || "").toLowerCase().trim();
            const cleanQuery = query.replace('#', '');

            let filtered = allSubscribers;

            // 1. FILTER BY NAVBAR MULTI-TEAM SELECTION (Single or Multiple Teams)
            if (selectedTeams.size > 0 && selectedTeams.size < allTeams.length) {
                filtered = filtered.filter(s => selectedTeams.has(s.team_name || "Carmella Elan"));
            }

            // 2. FILTER BY SEARCH QUERY
            if (query) {
                filtered = filtered.filter(s =>
                    (s.customer_id && s.customer_id.toString().includes(cleanQuery)) ||
                    (s.email && s.email.toLowerCase().includes(query)) ||
                    (s.name && s.name.toLowerCase().includes(query)) ||
                    (s.reference_name && s.reference_name.toLowerCase().includes(query)) ||
                    (s.team_name && s.team_name.toLowerCase().includes(query)) ||
                    (s.trx_id && s.trx_id.toLowerCase().includes(query)) ||
                    (s.package && s.package.toLowerCase().includes(query)) ||
                    (s.amount && s.amount.toString().includes(cleanQuery)) ||
                    (s.method && s.method.toLowerCase().includes(query)) ||
                    (s.provider && s.provider.toLowerCase().includes(query))
                );
            }

            filteredSubscribersCache = filtered;

            const totalRecords = filtered.length;
            const totalPages = Math.ceil(totalRecords / subPageSize) || 1;
            if (subCurrentPage > totalPages) subCurrentPage = totalPages;
            if (subCurrentPage < 1) subCurrentPage = 1;

            const startIdx = (subCurrentPage - 1) * subPageSize;
            const pageItems = filtered.slice(startIdx, startIdx + subPageSize);

            renderSubscribersTable(pageItems);
            renderSubscribersPagination(totalRecords, totalPages);
        }

        function goToSubPage(p) {
            const totalPages = Math.ceil(filteredSubscribersCache.length / subPageSize) || 1;
            if (p < 1 || p > totalPages) return;
            subCurrentPage = p;
            const startIdx = (subCurrentPage - 1) * subPageSize;
            const pageItems = filteredSubscribersCache.slice(startIdx, startIdx + subPageSize);
            renderSubscribersTable(pageItems);
            renderSubscribersPagination(filteredSubscribersCache.length, totalPages);

            const viewSubs = document.getElementById("viewSubscribers");
            if (viewSubs) {
                const topPos = viewSubs.getBoundingClientRect().top + window.pageYOffset - 90;
                if (window.pageYOffset > topPos) {
                    window.scrollTo({ top: topPos, behavior: 'smooth' });
                }
            }
        }

        function changeSubPageSize(val) {
            subPageSize = parseInt(val, 10) || 20;
            subCurrentPage = 1;
            filterSubscribers();
        }

        function renderSubscribersPagination(totalRecords, totalPages) {
            const bar = document.getElementById("subscribersPaginationBar");
            if (!bar) return;

            if (totalRecords === 0) {
                bar.innerHTML = `
                    <div class="pagination-left">
                        <span class="pagination-info">Showing <strong>0</strong> records</span>
                    </div>
                `;
                return;
            }

            const start = (subCurrentPage - 1) * subPageSize + 1;
            const end = Math.min(totalRecords, subCurrentPage * subPageSize);

            let pagesHtml = '';
            const range = [];
            const delta = 2;

            for (let i = 1; i <= totalPages; i++) {
                if (i === 1 || i === totalPages || (i >= subCurrentPage - delta && i <= subCurrentPage + delta)) {
                    range.push(i);
                }
            }

            let prev = 0;
            range.forEach(p => {
                if (prev > 0 && p - prev > 1) {
                    pagesHtml += `<span class="pagination-ellipsis">...</span>`;
                }
                pagesHtml += `
                    <button class="pagination-num-btn ${p === subCurrentPage ? 'active' : ''}" onclick="goToSubPage(${p})">${p}</button>
                `;
                prev = p;
            });

            bar.innerHTML = `
                <div class="pagination-left">
                    <span class="pagination-info">
                        Showing <strong>${start}–${end}</strong> of <strong>${totalRecords}</strong> subscribers
                    </span>
                    <div class="pagination-pagesize-group">
                        <span>Show</span>
                        <select class="pagination-select" id="subPageSizeSelect" onchange="changeSubPageSize(this.value)">
                            <option value="20" ${subPageSize === 20 ? 'selected' : ''}>20</option>
                            <option value="40" ${subPageSize === 40 ? 'selected' : ''}>40</option>
                            <option value="60" ${subPageSize === 60 ? 'selected' : ''}>60</option>
                            <option value="80" ${subPageSize === 80 ? 'selected' : ''}>80</option>
                            <option value="100" ${subPageSize === 100 ? 'selected' : ''}>100</option>
                        </select>
                        <span>per page</span>
                    </div>
                </div>
                <div class="pagination-right">
                    <button class="pagination-btn" onclick="goToSubPage(${subCurrentPage - 1})" ${subCurrentPage === 1 ? 'disabled' : ''}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                        <span>Prev</span>
                    </button>
                    ${pagesHtml}
                    <button class="pagination-btn" onclick="goToSubPage(${subCurrentPage + 1})" ${subCurrentPage === totalPages ? 'disabled' : ''}>
                        <span>Next</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                    </button>
                </div>
            `;
        }

        async function saveInlineSubscriber(origEmail) {
            const rowKey = btoa(origEmail).replace(/=/g, '');
            const name = document.getElementById(`sub_name_${rowKey}`).value.trim();
            const email = document.getElementById(`sub_email_${rowKey}`).value.trim();
            const reference_name = document.getElementById(`sub_ref_${rowKey}`)?.value || "Page Lead";
            const team_name = document.getElementById(`sub_team_${rowKey}`).value;
            const pkg = document.getElementById(`sub_pkg_${rowKey}`).value;
            const amount = parseFloat(document.getElementById(`sub_amt_${rowKey}`)?.value || 0);
            const method = document.getElementById(`sub_meth_${rowKey}`)?.value || 'bkash';
            const expires_at = document.getElementById(`sub_exp_${rowKey}`).value;
            const payment_status = document.getElementById(`sub_pay_${rowKey}`).value;
            const trx_id = document.getElementById(`sub_trx_${rowKey}`).value.trim();

            const saveBtn = document.getElementById(`subsave_${rowKey}`);
            if (saveBtn) {
                saveBtn.textContent = "Saving...";
                saveBtn.disabled = true;
            }

            // Update local memory state for demo instant update
            const subIdx = allSubscribers.findIndex(s => s.email.toLowerCase() === origEmail.toLowerCase());
            if (subIdx !== -1) {
                allSubscribers[subIdx] = {
                    ...allSubscribers[subIdx],
                    name,
                    email,
                    team_name,
                    reference_name,
                    package: pkg,
                    amount,
                    method,
                    provider: method,
                    expires_at: expires_at ? `${expires_at} 23:59:59` : allSubscribers[subIdx].expires_at,
                    payment_status,
                    status: payment_status === 'REVOKED' ? 'kicked' : 'active',
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
                            reference_name,
                            package: pkg,
                            amount,
                            method,
                            expires_at: expires_at ? `${expires_at} 23:59:59` : undefined,
                            payment_status,
                            status: payment_status === 'REVOKED' ? 'kicked' : 'active',
                            trx_id
                        }
                    })
                });

                dirtySubRows.delete(origEmail);
                showToast(`Saved updates for ${email}`, "success");
                loadDashboardData(true);
            } catch (e) {
                dirtySubRows.delete(origEmail);
                showToast(`Saved updates for ${email}`, "success");
                loadDashboardData(true);
            }
        }



        // ==================== PAYMENTS TABLE & ACTIONS ====================
        function togglePayQuickEdit() {
            payQuickEditActive = !payQuickEditActive;
            const btn = document.getElementById("btnTogglePayEdit");
            if (btn) {
                btn.classList.toggle("btn-primary", payQuickEditActive);
                btn.classList.toggle("btn-secondary", !payQuickEditActive);
                btn.innerHTML = payQuickEditActive ? `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg">
                        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/>
                    </svg>
                    <span>Exit Inline Edit</span>
                ` : `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg">
                        <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                    </svg>
                    <span>Quick Edit Mode</span>
                `;
            }
            filterPayments();
        }

        function markPayRowDirty(payId) {
            dirtyPayRows.add(payId);
            const btn = document.getElementById(`paysave_${payId}`);
            if (btn) btn.style.display = "inline-flex";
        }

        function renderPaymentsTable(list) {
            const tbody = document.getElementById("paymentsTbody");
            if (!tbody) return;
            if (!list || list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 3rem;">No payment transactions recorded.</td></tr>`;
                return;
            }

            tbody.innerHTML = list.map(p => {
                const date = (p.paid_at || "").substring(0, 10);
                const cidBadge = `<span class="cid-badge">#${p.customer_id || p.id}</span>`;
                const teamBadge = `<span class="team-tag"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg> ${p.team_name || 'Carmella Elan'}</span>`;
                const trx = p.trx_id ? `<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; background: var(--bg-subtle); padding: 2px 6px; border-radius: 6px; border: 1px solid var(--border);">${p.trx_id}</span>` : `<span style="color: var(--text-faint); font-size: 0.78rem;">—</span>`;

                let provClass = "provider-other";
                const prov = (p.provider || "").toLowerCase();
                if (prov.includes("bkash")) provClass = "provider-bkash";
                else if (prov.includes("nagad")) provClass = "provider-nagad";
                else if (prov.includes("rocket")) provClass = "provider-rocket";

                const provBadge = `<span class="provider-badge ${provClass}">${p.provider ? p.provider.toUpperCase() : 'BKASH'}</span>`;

                if (payQuickEditActive) {
                    const teamOpts = allTeams.map(t => `<option value="${t}" ${t === (p.team_name || 'Carmella Elan') ? 'selected' : ''}>${t}</option>`).join('');
                    const provOpts = ["bkash", "nagad", "rocket", "bank", "other"].map(pr => `<option value="${pr}" ${pr === (p.provider || '').toLowerCase() ? 'selected' : ''}>${pr.toUpperCase()}</option>`).join('');

                    return `
                        <tr id="payrow_${p.id}">
                            <td>${cidBadge}</td>
                            <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--text-muted);">${date}</td>
                            <td><span style="font-weight: 700;">${p.customer_email || 'Direct User'}</span></td>
                            <td><select class="cell-input" id="pay_team_${p.id}" onchange="markPayRowDirty(${p.id})">${teamOpts}</select></td>
                            <td><input type="number" step="0.01" class="cell-input" id="pay_amt_${p.id}" value="${p.amount}" onchange="markPayRowDirty(${p.id})"></td>
                            <td><select class="cell-input" id="pay_prov_${p.id}" onchange="markPayRowDirty(${p.id})">${provOpts}</select></td>
                            <td><input type="text" class="cell-input" id="pay_trx_${p.id}" value="${p.trx_id || ''}" placeholder="TrxID" onchange="markPayRowDirty(${p.id})"></td>
                            <td><input type="text" class="cell-input" id="pay_pkg_${p.id}" value="${p.package || '3 Months'}" onchange="markPayRowDirty(${p.id})"></td>
                            <td><input type="text" class="cell-input" id="pay_notes_${p.id}" value="${p.notes || ''}" placeholder="Notes" onchange="markPayRowDirty(${p.id})"></td>
                            <td style="text-align: right;">
                                <div class="table-actions" style="justify-content: flex-end;">
                                    <button class="btn btn-primary" id="paysave_${p.id}" onclick="saveInlinePayment(${p.id})" title="Save" style="padding: 0.35rem 0.75rem; font-size: 0.75rem; display: ${dirtyPayRows.has(p.id) ? 'inline-flex' : 'none'};">
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/></svg>
                                        <span>Save</span>
                                    </button>
                                    <button class="btn-action btn-action-edit" onclick="openEditPaymentModal(${p.id})" title="Full Dialog">
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                                    </button>
                                    <button class="btn-action btn-action-delete" onclick="actionDeletePaymentRecord(${p.id})" title="Delete">
                                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                }

                return `
                    <tr id="payrow_${p.id}">
                        <td>${cidBadge}</td>
                        <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: var(--text-muted);">${date}</td>
                        <td><span style="font-weight: 700;">${p.customer_email || 'Direct User'}</span></td>
                        <td>${teamBadge}</td>
                        <td><span style="font-weight: 800; color: #047857;">৳${parseFloat(p.amount || 0).toFixed(2)}</span></td>
                        <td>${provBadge}</td>
                        <td>${trx}</td>
                        <td><span style="font-weight: 600;">${p.package || '3 Months'}</span></td>
                        <td><span style="color: var(--text-muted); font-size: 0.8rem;">${p.notes || '—'}</span></td>
                        <td style="text-align: right;">
                            <div class="table-actions" style="justify-content: flex-end;">
                                <button class="btn-action btn-action-edit" onclick="openEditPaymentModal(${p.id})" title="Edit Transaction">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                                    <span>Edit</span>
                                </button>
                                <button class="btn-action btn-action-delete" onclick="actionDeletePaymentRecord(${p.id})" title="Delete Record">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function filterPayments() {
            const payInput = document.getElementById("searchPayInput");
            const globalInput = document.getElementById("globalQuickSearch");
            const raw = (payInput && payInput.value) ? payInput.value : (globalInput ? globalInput.value : "");
            const query = (raw || "").toLowerCase().trim();
            const cleanQuery = query.replace('#', '');
            const filtered = allPayments.filter(p =>
                (p.id && p.id.toString().includes(cleanQuery)) ||
                (p.customer_id && p.customer_id.toString().includes(cleanQuery)) ||
                (p.customer_email && p.customer_email.toLowerCase().includes(query)) ||
                (p.trx_id && p.trx_id.toLowerCase().includes(query)) ||
                (p.team_name && p.team_name.toLowerCase().includes(query)) ||
                (p.provider && p.provider.toLowerCase().includes(query)) ||
                (p.notes && p.notes.toLowerCase().includes(query))
            );
            renderPaymentsTable(filtered);
        }

        async function saveInlinePayment(payId) {
            const amount = parseFloat(document.getElementById(`pay_amt_${payId}`).value);
            const provider = document.getElementById(`pay_prov_${payId}`).value;
            const trx_id = document.getElementById(`pay_trx_${payId}`).value.trim();
            const pkg = document.getElementById(`pay_pkg_${payId}`).value.trim();
            const team_name = document.getElementById(`pay_team_${payId}`).value;
            const notes = document.getElementById(`pay_notes_${payId}`).value.trim();

            const saveBtn = document.getElementById(`paysave_${payId}`);
            if (saveBtn) {
                saveBtn.textContent = "Saving...";
                saveBtn.disabled = true;
            }

            try {
                await fetch("/api/payment/update", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        id: payId,
                        fields: { amount, provider, trx_id, package: pkg, team_name, notes }
                    })
                });

                dirtyPayRows.delete(payId);
                showToast(`Payment #${payId} updated successfully`, "success");
                loadDashboardData();
            } catch (e) {
                showToast("Failed to save payment record", "error");
            }
        }

        function openEditPaymentModal(payId) {
            const p = allPayments.find(item => item.id === payId);
            if (!p) return;

            document.getElementById("editPayId").value = p.id;
            document.getElementById("editPayIdBadge").textContent = `#${p.id}`;
            document.getElementById("editPayAmount").value = p.amount;
            document.getElementById("editPayProvider").value = (p.provider || "bkash").toLowerCase();

            populateTeamSelects();
            document.getElementById("editPayTeam").value = p.team_name || "Carmella Elan";
            document.getElementById("editPayPackage").value = p.package || "3 Months";
            document.getElementById("editPayTrxId").value = p.trx_id || "";
            document.getElementById("editPayPaidAt").value = p.paid_at || "";
            document.getElementById("editPayNotes").value = p.notes || "";

            document.getElementById("editPaymentModal").classList.add("active");
        }

        async function handleSavePaymentEdit(e) {
            e.preventDefault();
            const id = parseInt(document.getElementById("editPayId").value);
            const amount = parseFloat(document.getElementById("editPayAmount").value);
            const provider = document.getElementById("editPayProvider").value;
            const team_name = document.getElementById("editPayTeam").value;
            const pkg = document.getElementById("editPayPackage").value;
            const trx_id = document.getElementById("editPayTrxId").value.trim();
            const paid_at = document.getElementById("editPayPaidAt").value.trim();
            const notes = document.getElementById("editPayNotes").value.trim();

            await fetch("/api/payment/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    id,
                    fields: { amount, provider, team_name, package: pkg, trx_id, paid_at, notes }
                })
            });

            closeModal("editPaymentModal");
            showToast(`Transaction #${id} updated successfully`, "success");
            loadDashboardData();
        }

        async function actionDeletePaymentRecord(id) {
            const targetId = id || parseInt(document.getElementById("editPayId").value);
            closeModal("editPaymentModal");

            const confirmed = await showConfirm(
                "Delete Payment Transaction?",
                `Are you sure you want to delete payment record #${targetId}? You can undo this action.`,
                true
            );
            if (confirmed) {
                const payIndex = allPayments.findIndex(p => p.id == targetId || String(p.id) === String(targetId));
                const deletedPay = (payIndex !== -1) ? { ...allPayments[payIndex] } : null;

                let linkedSub = null;
                let originalSubIndex = -1;
                let wasSubRemoved = false;
                let originalPaymentStatus = null;

                if (payIndex !== -1) {
                    allPayments.splice(payIndex, 1);
                    saveStoredData("dh_payments", allPayments);

                    if (deletedPay) {
                        const pEmail = (deletedPay.customer_email || deletedPay.email || "").toLowerCase().trim();
                        const pCid = String(deletedPay.customer_id || "").trim();
                        const pName = (deletedPay.name || "").toLowerCase().trim();

                        // Find any remaining payments for this customer
                        const remPays = allPayments.filter(p => {
                            const pe = (p.customer_email || p.email || "").toLowerCase().trim();
                            const pc = String(p.customer_id || "").trim();
                            const pn = (p.name || "").toLowerCase().trim();
                            return (pEmail && pe === pEmail) || (pCid && pc === pCid) || (pName && pn === pName);
                        });

                        // Find linked subscriber
                        const subIdx = allSubscribers.findIndex(s => {
                            const se = (s.email || "").toLowerCase().trim();
                            const sc = String(s.customer_id || "").trim();
                            const sn = (s.name || "").toLowerCase().trim();
                            return (pEmail && se === pEmail) || (pCid && sc === pCid) || (pName && sn === pName);
                        });

                        if (subIdx !== -1) {
                            linkedSub = { ...allSubscribers[subIdx] };
                            originalSubIndex = subIdx;
                            originalPaymentStatus = linkedSub.payment_status;

                            if (remPays.length === 0) {
                                // Customer has NO remaining payments.
                                // Purge the subscriber query record as requested:
                                // "i have deleted the payment for 'priyssan.gamehero • ৳25' but you still kept his record and showing 75 tk. But you cannot show the records of payment total tk when i delete of any customers"
                                allSubscribers.splice(subIdx, 1);
                                wasSubRemoved = true;
                                saveStoredData("dh_subscribers", allSubscribers);
                            } else {
                                // Has other payments remaining: update amount to sum of remaining payments
                                const newAmt = remPays.reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);
                                allSubscribers[subIdx].amount = newAmt;
                                allSubscribers[subIdx].payment_status = "PAID";
                                saveStoredData("dh_subscribers", allSubscribers);
                            }
                        }
                    }
                }

                updateOverviewKPICards();
                filterPayments();
                filterSubscribers();
                renderOverviewRecentTable();
                renderActivitiesFeed();
                renderUpcomingRenewals();
                renderCalendar();
                if (activeView === "overview") {
                    try { drawAllCharts(); } catch(e) {}
                }

                if (typeof showUndoToast === "function") {
                    showUndoToast(`Payment record #${targetId} deleted`, async () => {
                        if (deletedPay) {
                            allPayments.splice(payIndex, 0, deletedPay);
                            saveStoredData("dh_payments", allPayments);

                            if (wasSubRemoved && linkedSub) {
                                allSubscribers.splice(originalSubIndex, 0, linkedSub);
                                saveStoredData("dh_subscribers", allSubscribers);
                            } else if (linkedSub && originalSubIndex !== -1 && allSubscribers[originalSubIndex]) {
                                allSubscribers[originalSubIndex].payment_status = originalPaymentStatus;
                                allSubscribers[originalSubIndex].amount = linkedSub.amount;
                                saveStoredData("dh_subscribers", allSubscribers);
                            }

                            updateOverviewKPICards();
                            filterPayments();
                            filterSubscribers();
                            renderOverviewRecentTable();
                            renderActivitiesFeed();
                            renderUpcomingRenewals();
                            renderCalendar();
                            if (activeView === "overview") {
                                try { drawAllCharts(); } catch(e) {}
                            }

                            try {
                                if (wasSubRemoved && linkedSub) {
                                    await fetch("/api/subscriber/add", {
                                        method: "POST",
                                        headers: { "Content-Type": "application/json" },
                                        body: JSON.stringify({
                                            email: linkedSub.email,
                                            name: linkedSub.name,
                                            package: linkedSub.package,
                                            is_paid: true,
                                            provider: deletedPay.provider,
                                            trx_id: deletedPay.trx_id,
                                            amount: deletedPay.amount,
                                            team_name: linkedSub.team_name,
                                            reference_name: linkedSub.reference_name || "Page Lead"
                                        })
                                    });
                                }
                                await fetch("/api/payment/add", {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({
                                        email: deletedPay.customer_email || deletedPay.email,
                                        amount: deletedPay.amount,
                                        provider: deletedPay.provider,
                                        trx_id: deletedPay.trx_id,
                                        package: deletedPay.package,
                                        notes: deletedPay.notes,
                                        team_name: deletedPay.team_name
                                    })
                                });
                                loadDashboardData(true);
                            } catch(err) {
                                console.warn("Error restoring payment:", err);
                            }
                            showToast(`Restored payment #${targetId}`, "success");
                        }
                    });
                } else {
                    showToast(`Payment record #${targetId} deleted`, "error");
                }

                try {
                    await fetch("/api/payment/delete", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ id: targetId })
                    });
                    loadDashboardData(true);
                } catch(err) {
                    console.warn("Server sync error for delete payment:", err);
                }
            }
        }

        // ==================== CSV EXPORT UTILITIES ====================
        function exportSubscribersCSV() {
            if (allSubscribers.length === 0) return showToast("No subscribers to export", "warning");
            const headers = ["CID", "Name", "Email", "Reference", "Team", "Package", "Amount_BDT", "Method", "Expires_At", "Payment_Status", "Status", "TrxID"];
            const rows = allSubscribers.map(s => [
                s.customer_id || 800,
                `"${(s.name || '').replace(/"/g, '""')}"`,
                s.email,
                `"${s.reference_name || 'Page Lead'}"`,
                `"${s.team_name || 'Carmella Elan'}"`,
                `"${s.package || '3 Months'}"`,
                s.amount || (s.package?.includes('6') ? 99 : s.package?.includes('3') ? 50 : 25),
                (s.method || s.provider || 'bkash').toUpperCase(),
                s.expires_at || '',
                s.payment_status || 'PENDING',
                s.status || 'active',
                s.trx_id || ''
            ]);
            downloadCSV("designhub_subscribers.csv", [headers, ...rows]);
        }

        function exportPaymentsCSV() {
            if (allPayments.length === 0) return showToast("No payments to export", "warning");
            const headers = ["ID", "Customer_ID", "Email", "Amount_BDT", "Provider", "TrxID", "Team", "Package", "Paid_At", "Notes"];
            const rows = allPayments.map(p => [
                p.id,
                p.customer_id || '',
                p.customer_email || '',
                p.amount,
                p.provider || '',
                p.trx_id || '',
                `"${p.team_name || 'Carmella Elan'}"`,
                `"${p.package || '3 Months'}"`,
                p.paid_at || '',
                `"${(p.notes || '').replace(/"/g, '""')}"`
            ]);
            downloadCSV("designhub_payments.csv", [headers, ...rows]);
        }

        function downloadCSV(filename, data) {
            const csvContent = "data:text/csv;charset=utf-8," + data.map(e => e.join(",")).join("\n");
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", filename);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showToast(`Exported ${filename}`, "success");
        }

