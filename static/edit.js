/* ChoralChart edit page — all interactivity lives here.
   Reads initial state from window.CHART_CONFIG (set inline by edit.html). */

if (CHART_CONFIG.editable) {
    // Flip toggle
    document.getElementById('flip-toggle').addEventListener('change', function() {
        const wrapper = document.querySelector('.chart-wrapper');
        const hiddenFlipped = document.querySelector('input[name="flipped"]');
        const goFlipped = this.checked;
        wrapper.style.transition = 'transform 0.17s ease-in';
        wrapper.style.transform = 'scaleY(0)';
        setTimeout(() => {
            if (goFlipped) { wrapper.classList.add('flipped'); hiddenFlipped.value = 'true'; }
            else           { wrapper.classList.remove('flipped'); hiddenFlipped.value = 'false'; }
            wrapper.style.transition = 'transform 0.17s ease-out';
            wrapper.style.transform = 'scaleY(1)';
            setTimeout(() => { wrapper.style.transition = ''; wrapper.style.transform = ''; }, 170);
        }, 170);
    });

    function updateStaggerOffsets() {
        const rows = document.querySelectorAll('.chart-row');
        let prevParity = null;
        let currentOffset = false;

        rows.forEach((row, i) => {
            const singerCount = row.querySelectorAll('.seat:not(.empty)').length;
            const currentParity = singerCount % 2;

            if (i === 0) {
                currentOffset = false;
            } else if (currentParity === prevParity) {
                currentOffset = !currentOffset;
            }

            if (currentOffset) {
                row.classList.add('stagger-offset');
            } else {
                row.classList.remove('stagger-offset');
            }

            prevParity = currentParity;
        });
    }

    // Stagger toggle
    document.getElementById('stagger-toggle').addEventListener('change', function() {
        const container = document.querySelector('.chart-container');
        const hiddenStaggered = document.querySelector('input[name="staggered"]');
        if (this.checked) {
            container.classList.add('staggered');
            hiddenStaggered.value = 'true';
        } else {
            container.classList.remove('staggered');
            hiddenStaggered.value = 'false';
        }
        checkHeightWarnings();
    });

    // Height toggle
    document.getElementById('height-toggle').addEventListener('change', function() {
        const container = document.querySelector('.chart-container');
        if (this.checked) {
            container.classList.remove('hide-heights');
        } else {
            container.classList.add('hide-heights');
        }
    });

    // Empty chairs toggle
    document.getElementById('empty-chairs-toggle').addEventListener('change', function() {
        const seats = document.querySelectorAll('.seat.empty');
        if (this.checked) {
            seats.forEach(s => s.classList.add('ec-show'));
            requestAnimationFrame(() => requestAnimationFrame(() => {
                seats.forEach(s => s.classList.add('ec-visible'));
            }));
        } else {
            seats.forEach(s => s.classList.remove('ec-visible'));
            setTimeout(() => {
                seats.forEach(s => s.classList.remove('ec-show'));
            }, 320);
        }
    });

    // Seat number mode (left / right / both edges)
    function updateSeatNumbers() {
        const mode = document.getElementById('seat-num-mode').value;
        document.querySelectorAll('.chart-row').forEach(row => {
            const seats = Array.from(row.querySelectorAll('.seat:not(.empty)'));
            const n = seats.length;
            seats.forEach((seat, i) => {
                const fromLeft = i + 1;
                const fromRight = n - i;
                let label = '';
                if (mode === 'left') label = String(fromLeft);
                else if (mode === 'right') label = String(fromRight);
                else label = fromLeft <= fromRight
                    ? String(fromLeft)
                    : (fromLeft === fromRight ? String(fromLeft) : String(fromRight));
                const numEl = seat.querySelector('.seat-number');
                if (numEl) numEl.textContent = label;
            });
        });
    }
    document.getElementById('seat-num-mode').addEventListener('change', updateSeatNumbers);

    // --- Undo / Redo ---
    const undoStack = [];
    let undoIdx = -1;

    function pushHistory() {
        undoStack.splice(undoIdx + 1);
        undoStack.push(document.getElementById('chart_data').value);
        undoIdx = undoStack.length - 1;
        updateUndoRedoButtons();
    }

    function updateUndoRedoButtons() {
        document.getElementById('btn-undo').disabled = undoIdx <= 0;
        document.getElementById('btn-redo').disabled = undoIdx >= undoStack.length - 1;
    }

    function applyChartState(encoded) {
        const data = JSON.parse(atob(encoded));
        document.querySelectorAll('.chart-row').forEach((rowEl, rowIdx) => {
            const rowData = data[rowIdx];
            if (!rowData) return;
            rowEl.querySelectorAll('.seat').forEach((seatEl, posIdx) => {
                const seatData = rowData[posIdx];
                if (seatData !== undefined) updateSeatDisplay(seatEl, seatData.singer);
            });
        });
        document.getElementById('chart_data').value = encoded;
        updateStaggerOffsets();
        checkHeightWarnings();
    }

    function undo() {
        if (undoIdx <= 0) return;
        undoIdx--;
        applyChartState(undoStack[undoIdx]);
        updateUndoRedoButtons();
    }

    function redo() {
        if (undoIdx >= undoStack.length - 1) return;
        undoIdx++;
        applyChartState(undoStack[undoIdx]);
        updateUndoRedoButtons();
    }

    // Expose for inline onclick handlers
    window.undo = undo;
    window.redo = redo;

    // Seat interaction (pointer events — works on mouse and touch)
    const partOrder = CHART_CONFIG.partOrder;
    let selectedSeat = null;
    let dragState = null;
    let lastTapInfo = { el: null, time: 0 };

    function getPartIndex(voicePart) {
        const idx = partOrder.indexOf(voicePart);
        return idx >= 0 ? idx : 0;
    }

    function updateSeatDisplay(seatEl, singerData) {
        const seatNum = parseInt(seatEl.dataset.pos) + 1;

        if (singerData) {
            const partIdx = getPartIndex(singerData.voice_part);
            seatEl.className = `seat part-${partIdx} draggable`;
            seatEl.dataset.singer = JSON.stringify(singerData);

            let heightStr = '';
            if (singerData.height != null) {
                const feet = Math.floor(singerData.height / 12);
                const inches = singerData.height % 12;
                heightStr = inches % 1 === 0.5
                    ? `${feet}'${Math.floor(inches)}.5"`
                    : `${feet}'${Math.floor(inches)}"`;
            }

            seatEl.innerHTML = `
                <span class="seat-number">${seatNum}</span>
                <span class="singer-name">${singerData.name}</span>
                <span class="singer-info"><span class="singer-part">${singerData.voice_part}</span>${heightStr ? `<span class="singer-height"> | ${heightStr}</span>` : ''}</span>
            `;
        } else {
            seatEl.className = 'seat empty';
            seatEl.dataset.singer = 'null';
            seatEl.innerHTML = `<span class="seat-number">${seatNum}</span>`;
        }
    }

    function swapSeats(seat1, seat2) {
        const singer1 = seat1.dataset.singer !== 'null' ? JSON.parse(seat1.dataset.singer) : null;
        const singer2 = seat2.dataset.singer !== 'null' ? JSON.parse(seat2.dataset.singer) : null;

        updateSeatDisplay(seat1, singer2);
        updateSeatDisplay(seat2, singer1);

        [seat1, seat2].forEach(s => {
            s.classList.add('swapping');
            s.addEventListener('animationend', () => s.classList.remove('swapping'), { once: true });
        });

        updateChartData();
        pushHistory();
        updateStaggerOffsets();
        checkHeightWarnings();
    }

    function shiftSeats(sourceEl, targetEl) {
        const sourceRow = sourceEl.closest('.chart-row');
        const targetRow = targetEl.closest('.chart-row');

        if (sourceRow !== targetRow) {
            swapSeats(sourceEl, targetEl);
            return;
        }

        const seats = Array.from(sourceRow.querySelectorAll('.seat'));
        const srcIdx = seats.indexOf(sourceEl);
        const dstIdx = seats.indexOf(targetEl);
        if (srcIdx === dstIdx) return;

        const singers = seats.map(s => s.dataset.singer !== 'null' ? JSON.parse(s.dataset.singer) : null);
        const [moved] = singers.splice(srcIdx, 1);
        singers.splice(dstIdx, 0, moved);
        seats.forEach((s, i) => updateSeatDisplay(s, singers[i]));

        const lo = Math.min(srcIdx, dstIdx);
        const hi = Math.max(srcIdx, dstIdx);
        seats.slice(lo, hi + 1).forEach(s => {
            s.classList.add('swapping');
            s.addEventListener('animationend', () => s.classList.remove('swapping'), { once: true });
        });

        updateChartData();
        pushHistory();
        updateStaggerOffsets();
        checkHeightWarnings();
    }

    function updateChartData() {
        const rows = document.querySelectorAll('.chart-row');
        const chartData = [];

        rows.forEach((rowEl, rowIdx) => {
            const seats = rowEl.querySelectorAll('.seat');
            const rowData = [];

            seats.forEach((seatEl, posIdx) => {
                const singerStr = seatEl.dataset.singer;
                const singer = singerStr !== 'null' ? JSON.parse(singerStr) : null;
                rowData.push({ row: rowIdx, position: posIdx, singer: singer });
            });

            chartData.push(rowData);
        });

        const encoded = btoa(JSON.stringify(chartData));
        document.getElementById('chart_data').value = encoded;
    }

    // Pointer-event drag and drop (works on mouse and touch/iPad)
    const DRAG_THRESHOLD = 6; // px of movement before drag starts

    document.addEventListener('pointerdown', e => {
        const seat = e.target.closest('#chart .seat');
        if (!seat) return;

        if (!seat.classList.contains('draggable')) {
            const now = Date.now();
            if (selectedSeat) {
                // Complete a pending selection swap
                swapSeats(selectedSeat, seat);
                selectedSeat.classList.remove('selected');
                selectedSeat = null;
                lastTapInfo = { el: null, time: 0 };
            } else if (lastTapInfo.el === seat && now - lastTapInfo.time < 350) {
                // Double-tap on empty seat: create a new singer here
                openCreateModal(seat);
                lastTapInfo = { el: null, time: 0 };
            } else {
                lastTapInfo = { el: seat, time: now };
            }
            return;
        }

        e.preventDefault(); // only on draggable seats (prevents text selection, keeps touch-scroll on empty seats)
        const rect = seat.getBoundingClientRect();
        dragState = {
            sourceEl: seat,
            cloneEl: null,
            startX: e.clientX,
            startY: e.clientY,
            offsetX: e.clientX - rect.left,
            offsetY: e.clientY - rect.top,
            currentTarget: null,
            moved: false,
            pointerId: e.pointerId,
        };
    });

    document.addEventListener('pointermove', e => {
        if (!dragState || e.pointerId !== dragState.pointerId) return;
        e.preventDefault();

        const dx = e.clientX - dragState.startX;
        const dy = e.clientY - dragState.startY;

        if (!dragState.moved) {
            if (Math.sqrt(dx * dx + dy * dy) < DRAG_THRESHOLD) return;
            if (dragState.sourceEl.dataset.singer === 'null') { dragState = null; return; }

            // Cancel any pending selection when drag starts
            if (selectedSeat) { selectedSeat.classList.remove('selected'); selectedSeat = null; }

            // Build floating clone
            const src = dragState.sourceEl;
            const rect = src.getBoundingClientRect();
            const clone = src.cloneNode(true);
            clone.style.cssText = [
                'position:fixed', 'z-index:9999', 'pointer-events:none',
                `width:${rect.width}px`, `height:${rect.height}px`,
                `left:${e.clientX - dragState.offsetX}px`,
                `top:${e.clientY - dragState.offsetY}px`,
                'opacity:0.9', 'box-shadow:0 8px 28px rgba(0,0,0,0.22)',
                'transform:scale(1.06)', 'border-radius:8px', 'transition:none',
            ].join(';');
            document.body.appendChild(clone);
            dragState.cloneEl = clone;
            src.classList.add('dragging');
            dragState.moved = true;
        }

        // Move clone
        dragState.cloneEl.style.left = (e.clientX - dragState.offsetX) + 'px';
        dragState.cloneEl.style.top  = (e.clientY - dragState.offsetY) + 'px';

        // Find seat under cursor (hide clone so it doesn't block hit-test)
        dragState.cloneEl.style.visibility = 'hidden';
        const el = document.elementFromPoint(e.clientX, e.clientY);
        dragState.cloneEl.style.visibility = '';

        const over = el ? el.closest('#chart .seat') : null;
        if (dragState.currentTarget !== over) {
            if (dragState.currentTarget) dragState.currentTarget.classList.remove('drag-over');
            if (over && over !== dragState.sourceEl) {
                over.classList.add('drag-over');
                dragState.currentTarget = over;
            } else {
                dragState.currentTarget = null;
            }
        }
    });

    function finishDrag(e) {
        if (!dragState || e.pointerId !== dragState.pointerId) return;
        const { sourceEl, cloneEl, currentTarget, moved } = dragState;

        if (cloneEl) document.body.removeChild(cloneEl);
        sourceEl.classList.remove('dragging');
        if (currentTarget) currentTarget.classList.remove('drag-over');

        if (moved) {
            if (currentTarget) shiftSeats(sourceEl, currentTarget);
        } else {
            // Tap — check for double-tap (opens modal) or single tap (select/swap)
            const now = Date.now();
            const isSinger = sourceEl.dataset.singer !== 'null';
            if (isSinger && lastTapInfo.el === sourceEl && now - lastTapInfo.time < 350) {
                // Double-tap: open modal
                if (selectedSeat) { selectedSeat.classList.remove('selected'); selectedSeat = null; }
                openModal(sourceEl, JSON.parse(sourceEl.dataset.singer));
                lastTapInfo = { el: null, time: 0 };
            } else {
                lastTapInfo = { el: sourceEl, time: now };
                if (selectedSeat === null) {
                    if (isSinger) { selectedSeat = sourceEl; selectedSeat.classList.add('selected'); }
                } else if (selectedSeat === sourceEl) {
                    selectedSeat.classList.remove('selected');
                    selectedSeat = null;
                } else {
                    swapSeats(selectedSeat, sourceEl);
                    selectedSeat.classList.remove('selected');
                    selectedSeat = null;
                }
            }
        }
        dragState = null;
    }

    document.addEventListener('pointerup', finishDrag);
    document.addEventListener('pointercancel', e => {
        if (!dragState || e.pointerId !== dragState.pointerId) return;
        const { sourceEl, cloneEl, currentTarget } = dragState;
        if (cloneEl) document.body.removeChild(cloneEl);
        sourceEl.classList.remove('dragging');
        if (currentTarget) currentTarget.classList.remove('drag-over');
        dragState = null;
    });

    // Modal functionality
    let editingSeat = null;
    let editingIsNew = false;

    function parseHeightInput(str) {
        str = (str || '').trim();
        if (!str) return null;
        const m = str.match(/^(\d+)'\s*(\d+(?:\.\d+)?)"?$/);
        if (m) return parseFloat(m[1]) * 12 + parseFloat(m[2]);
        const n = parseFloat(str);
        return isNaN(n) || n <= 0 ? null : n;
    }

    function heightToInputStr(h) {
        if (h == null) return '';
        const ft = Math.floor(h / 12);
        const inc = h % 12;
        return inc % 1 === 0.5 ? `${ft}'${Math.floor(inc)}.5"` : `${ft}'${Math.floor(inc)}"`;
    }

    function openModal(seatEl, singer) {
        editingSeat = seatEl;
        editingIsNew = false;
        document.getElementById('modal-title').textContent = 'Edit Singer';
        document.getElementById('modal-remove-btn').style.display = '';
        document.getElementById('modal-name').value = singer.name;
        document.getElementById('modal-height').value = heightToInputStr(singer.height);
        document.getElementById('modal-part').value = singer.voice_part;
        document.getElementById('edit-modal').classList.add('active');
        setTimeout(() => document.getElementById('modal-name').select(), 10);
    }

    function openCreateModal(seatEl) {
        editingSeat = seatEl;
        editingIsNew = true;
        document.getElementById('modal-title').textContent = 'Add Singer';
        document.getElementById('modal-remove-btn').style.display = 'none';
        document.getElementById('modal-name').value = '';
        document.getElementById('modal-height').value = '';
        document.getElementById('modal-part').value = CHART_CONFIG.partOrder[0] || '';
        document.getElementById('edit-modal').classList.add('active');
        setTimeout(() => document.getElementById('modal-name').focus(), 10);
    }

    function closeModal() {
        editingSeat = null;
        editingIsNew = false;
        document.getElementById('edit-modal').classList.remove('active');
    }

    function savePart() {
        if (!editingSeat) return;
        const newName = document.getElementById('modal-name').value.trim();
        if (!newName) { document.getElementById('modal-name').focus(); return; }
        const singer = editingIsNew
            ? { name: newName, voice_part: document.getElementById('modal-part').value, height: null }
            : JSON.parse(editingSeat.dataset.singer);
        singer.name = newName;
        singer.height = parseHeightInput(document.getElementById('modal-height').value);
        singer.voice_part = document.getElementById('modal-part').value;
        updateSeatDisplay(editingSeat, singer);
        updateChartData();
        pushHistory();
        checkHeightWarnings();
        closeModal();
    }

    // Expose modal functions for onclick attributes
    window.closeModal = closeModal;
    window.savePart = savePart;
    window.openCreateModal = openCreateModal;

    document.getElementById('edit-modal').addEventListener('click', (e) => {
        if (e.target.id === 'edit-modal') closeModal();
    });
    document.getElementById('edit-modal').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); savePart(); }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        } else if (e.key === 'z' && (e.ctrlKey || e.metaKey) && !e.shiftKey) {
            e.preventDefault();
            undo();
        } else if ((e.key === 'y' && (e.ctrlKey || e.metaKey)) ||
                   (e.key === 'z' && (e.ctrlKey || e.metaKey) && e.shiftKey)) {
            e.preventDefault();
            redo();
        }
    });

    // --- Height warnings ---
    function checkHeightWarnings() {
        document.querySelectorAll('.seat.height-warn, .seat.height-warn-back')
            .forEach(el => el.classList.remove('height-warn', 'height-warn-back'));

        const isStaggered = document.querySelector('.chart-container').classList.contains('staggered');
        const rows = Array.from(document.querySelectorAll('.chart-row'));

        for (let i = 0; i < rows.length - 1; i++) {
            const backRow = rows[i];
            const frontRow = rows[i + 1];

            // Compute the visual x-offset of front[p] relative to back[p] (in px).
            // This accounts for both CSS centering (rows with different singer counts are
            // centered independently, creating a natural half-stride offset when the count
            // difference is odd) and the explicit stagger-offset translateX.
            //
            // offset = 64*(n_b - n_f) + (p_b - p_f)*128 + (stagger_f - stagger_b)
            //   where p_b/p_f = first filled data-pos in each row (algorithm centering offset)
            //   and stagger_f/stagger_b = 64 if that row has translateX applied, else 0
            const n_b = backRow.querySelectorAll('.seat:not(.empty)').length;
            const n_f = frontRow.querySelectorAll('.seat:not(.empty)').length;
            const firstBackEl  = backRow.querySelector('.seat:not(.empty)');
            const firstFrontEl = frontRow.querySelector('.seat:not(.empty)');
            const p_b = firstBackEl  ? parseInt(firstBackEl.dataset.pos)  : 0;
            const p_f = firstFrontEl ? parseInt(firstFrontEl.dataset.pos) : 0;
            const stagger_b = (isStaggered && backRow.classList.contains('stagger-offset'))  ? 64 : 0;
            const stagger_f = (isStaggered && frontRow.classList.contains('stagger-offset')) ? 64 : 0;
            const offset = 64 * (n_b - n_f) + (p_b - p_f) * 128 + (stagger_f - stagger_b);

            // Find back data-pos values within ±64px (half-stride) of each front seat.
            // q_lo_d and q_hi_d are the delta from front data-pos to back data-pos.
            const q_lo_d = Math.ceil((offset - 64) / 128);
            const q_hi_d = Math.floor((offset + 64) / 128);

            const backHeights = {};
            const backSeatEls = {};
            backRow.querySelectorAll('.seat:not(.empty)').forEach(seat => {
                const singer = JSON.parse(seat.dataset.singer);
                if (singer && singer.height !== null) {
                    const p = parseInt(seat.dataset.pos);
                    backHeights[p] = singer.height;
                    backSeatEls[p] = seat;
                }
            });

            frontRow.querySelectorAll('.seat:not(.empty)').forEach(seat => {
                const singer = JSON.parse(seat.dataset.singer);
                if (!singer || singer.height === null) return;
                const pos = parseInt(seat.dataset.pos);
                let warned = false;
                for (let dq = q_lo_d; dq <= q_hi_d; dq++) {
                    const bh = backHeights[pos + dq];
                    if (bh !== undefined && singer.height > bh) {
                        warned = true;
                        backSeatEls[pos + dq].classList.add('height-warn-back');
                    }
                }
                if (warned) seat.classList.add('height-warn');
            });
        }

        const anyWarn = document.querySelector('.seat.height-warn') !== null;
        document.getElementById('height-warn-banner').style.display = anyWarn ? '' : 'none';
    }

    // --- Singer removal ---
    function removeSinger() {
        if (!editingSeat) return;
        const singer = JSON.parse(editingSeat.dataset.singer);
        if (!singer) return;

        if (!confirm(`Remove ${singer.name} from the chart?`)) return;

        closeModal();

        const part = singer.voice_part;
        const partSeats = Array.from(document.querySelectorAll('.seat:not(.empty)'))
            .filter(s => {
                const d = JSON.parse(s.dataset.singer);
                return d && d.voice_part === part;
            })
            .sort((a, b) => {
                const dr = parseInt(a.dataset.row) - parseInt(b.dataset.row);
                return dr !== 0 ? dr : parseInt(a.dataset.pos) - parseInt(b.dataset.pos);
            });

        const remaining = partSeats
            .map(s => JSON.parse(s.dataset.singer))
            .filter(s => s.name !== singer.name);

        partSeats.forEach(s => updateSeatDisplay(s, null));
        remaining.forEach((s, i) => updateSeatDisplay(partSeats[i], s));

        updateChartData();
        pushHistory();
        updateStaggerOffsets();
        checkHeightWarnings();
    }

    window.removeSinger = removeSinger;

    // --- JSON save/load ---
    function saveChart() {
        const data = {
            version: 1,
            chart_data:   document.getElementById('chart_data').value,
            part_order:   document.querySelector('input[name="part_order"]').value,
            part_grid:    document.querySelector('input[name="part_grid"]').value,
            layout:       document.querySelector('input[name="layout"]').value,
            singers_data: document.querySelector('input[name="singers_data"]').value,
            num_singers:  document.querySelector('input[name="num_singers"]').value,
            staggered:    document.querySelector('input[name="staggered"]').value,
            flipped:      document.querySelector('input[name="flipped"]').value,
            mixed:        document.querySelector('input[name="mixed"]').value,
            aisle_after:  document.querySelector('input[name="aisle_after"]').value,
            chart_title:  document.getElementById('chart-title').value,
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'seating-chart.choralchart';
        a.click();
        URL.revokeObjectURL(url);
    }

    window.saveChart = saveChart;

    // --- Share / living document ---
    async function shareChart() {
        const formData = new FormData();
        formData.append('chart_data',   document.getElementById('chart_data').value);
        formData.append('part_order',   document.querySelector('input[name="part_order"]').value);
        formData.append('part_grid',    document.querySelector('input[name="part_grid"]').value);
        formData.append('layout',       document.querySelector('input[name="layout"]').value);
        formData.append('singers_data', document.querySelector('input[name="singers_data"]').value);
        formData.append('num_singers',  document.querySelector('input[name="num_singers"]').value);
        formData.append('staggered',    document.querySelector('input[name="staggered"]').value);
        formData.append('flipped',      document.querySelector('input[name="flipped"]').value);
        formData.append('mixed',        document.querySelector('input[name="mixed"]').value);
        formData.append('aisle_after',  document.querySelector('input[name="aisle_after"]').value);
        formData.append('chart_title',  document.getElementById('chart-title').value);
        const existingId = document.getElementById('share_id').value;
        if (existingId) formData.append('share_id', existingId);

        const resp = await fetch(CHART_CONFIG.shareUrl, { method: 'POST', body: formData });
        const data = await resp.json();
        document.getElementById('share_id').value = data.id;
        document.getElementById('share-url').href = data.url;
        document.getElementById('share-url').textContent = data.url;
        document.getElementById('share-banner').style.display = 'flex';
    }

    window.shareChart = shareChart;

    function copyShareUrl() {
        const url = document.getElementById('share-url').href;
        navigator.clipboard.writeText(url).then(() => {
            const btn = event.target;
            btn.textContent = 'Copied!';
            setTimeout(() => btn.textContent = 'Copy', 1500);
        });
    }

    window.copyShareUrl = copyShareUrl;

    function reshuffleChart() {
        const isMixed = document.querySelector('input[name="mixed"]').value === 'true';
        const seats = Array.from(document.querySelectorAll('.seat:not(.empty)'));

        function shuffle(arr) {
            for (let i = arr.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [arr[i], arr[j]] = [arr[j], arr[i]];
            }
        }

        if (isMixed) {
            const singers = seats.map(s => JSON.parse(s.dataset.singer));
            shuffle(singers);
            seats.forEach((seat, i) => updateSeatDisplay(seat, singers[i]));
        } else {
            const partGroups = {};
            seats.forEach(s => {
                const singer = JSON.parse(s.dataset.singer);
                const p = singer.voice_part;
                if (!partGroups[p]) partGroups[p] = { seats: [], singers: [] };
                partGroups[p].seats.push(s);
                partGroups[p].singers.push(singer);
            });
            Object.values(partGroups).forEach(({ seats: ps, singers: sg }) => {
                shuffle(sg);
                ps.forEach((seat, i) => updateSeatDisplay(seat, sg[i]));
            });
        }

        updateChartData();
        pushHistory();
        updateStaggerOffsets();
        checkHeightWarnings();
    }

    window.reshuffleChart = reshuffleChart;

    // --- Voice part arrangement panel ---
    function toggleArrangementPanel() {
        const body = document.getElementById('arr-panel-body');
        const indicator = document.getElementById('arr-toggle-indicator');
        const open = body.style.display !== 'none';
        body.style.display = open ? 'none' : '';
        indicator.textContent = open ? '▶ Show' : '▼ Hide';
    }

    window.toggleArrangementPanel = toggleArrangementPanel;

    const arrGrid = document.getElementById('arr-part-grid');
    let arrDraggedItem = null;

    function arrMakeItem(part) {
        const item = document.createElement('div');
        item.className = 'part-item';
        item.draggable = true;
        item.dataset.part = part;
        item.innerHTML = `<span class="drag-handle">&#9776;</span><span class="part-name">${part}</span>`;
        arrBindItem(item);
        return item;
    }

    function arrBindItem(item) {
        item.addEventListener('dragstart', e => {
            arrDraggedItem = item;
            item.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        });
        item.addEventListener('dragend', () => {
            item.classList.remove('dragging');
            arrGrid.querySelectorAll('.drag-over-item, .drag-target')
                .forEach(el => el.classList.remove('drag-over-item', 'drag-target'));
            arrDraggedItem = null;
        });
        item.addEventListener('dragover', e => {
            e.preventDefault();
            if (arrDraggedItem && arrDraggedItem !== item) item.classList.add('drag-over-item');
        });
        item.addEventListener('dragleave', () => item.classList.remove('drag-over-item'));
        item.addEventListener('drop', e => {
            e.preventDefault();
            e.stopPropagation();
            item.classList.remove('drag-over-item');
            if (!arrDraggedItem || arrDraggedItem === item) return;
            const siblings = Array.from(item.parentNode.querySelectorAll('.part-item'));
            const di = siblings.indexOf(arrDraggedItem);
            const ti = siblings.indexOf(item);
            item.parentNode.insertBefore(arrDraggedItem, di < ti ? item.nextSibling : item);
        });
    }

    function arrBindGroup(group) {
        const partsEl = group.querySelector('.grid-group-parts');
        partsEl.addEventListener('dragover', e => {
            e.preventDefault();
            if (arrDraggedItem && arrDraggedItem.parentNode !== partsEl)
                group.classList.add('drag-target');
        });
        partsEl.addEventListener('dragleave', e => {
            if (!partsEl.contains(e.relatedTarget)) group.classList.remove('drag-target');
        });
        partsEl.addEventListener('drop', e => {
            e.preventDefault();
            group.classList.remove('drag-target');
            if (arrDraggedItem && arrDraggedItem.parentNode !== partsEl)
                partsEl.appendChild(arrDraggedItem);
        });
    }

    function arrRefreshLabels() {
        const groups = Array.from(arrGrid.querySelectorAll('.grid-group'));
        groups.forEach((group, idx) => {
            const header = group.querySelector('.grid-group-header');
            const label = group.querySelector('.grid-group-label');
            let removeBtn = group.querySelector('.btn-remove-group');
            if (groups.length === 1) {
                label.textContent = 'All rows';
                if (removeBtn) removeBtn.remove();
            } else {
                if (!removeBtn) {
                    removeBtn = document.createElement('button');
                    removeBtn.type = 'button';
                    removeBtn.className = 'btn-remove-group';
                    removeBtn.textContent = 'Remove';
                    removeBtn.addEventListener('click', () => arrRemoveGroup(removeBtn));
                    header.appendChild(removeBtn);
                }
                label.textContent = idx === 0 ? 'Back rows' : idx === groups.length - 1 ? 'Front rows' : 'Middle rows';
            }
        });
    }

    function arrAddGroup() {
        const group = document.createElement('div');
        group.className = 'grid-group';
        group.innerHTML = `<div class="grid-group-header"><span class="grid-group-label"></span></div><div class="grid-group-parts"></div>`;
        arrGrid.appendChild(group);
        arrBindGroup(group);
        arrRefreshLabels();
    }

    window.arrAddGroup = arrAddGroup;

    function arrRemoveGroup(btn) {
        const group = btn.closest('.grid-group');
        const allGroups = Array.from(arrGrid.querySelectorAll('.grid-group'));
        const idx = allGroups.indexOf(group);
        const dest = allGroups[idx > 0 ? idx - 1 : 1];
        group.querySelectorAll('.part-item').forEach(item => dest.querySelector('.grid-group-parts').appendChild(item));
        group.remove();
        arrRefreshLabels();
    }

    // Initialize grid from current part_grid and part_order
    (function initArrGrid() {
        const gridStr = CHART_CONFIG.partGridStr;
        const order = CHART_CONFIG.partOrder;
        const groups = gridStr ? gridStr.split(';').map(g => g.split(',').filter(Boolean)) : [order];
        groups.forEach((groupParts, gi) => {
            let group;
            if (gi === 0) {
                group = document.createElement('div');
                group.className = 'grid-group';
                group.innerHTML = `<div class="grid-group-header"><span class="grid-group-label"></span></div><div class="grid-group-parts"></div>`;
                arrGrid.appendChild(group);
            } else {
                const g = document.createElement('div');
                g.className = 'grid-group';
                g.innerHTML = `<div class="grid-group-header"><span class="grid-group-label"></span></div><div class="grid-group-parts"></div>`;
                arrGrid.appendChild(g);
                group = g;
            }
            const partsEl = group.querySelector('.grid-group-parts');
            groupParts.forEach(part => partsEl.appendChild(arrMakeItem(part)));
            arrBindGroup(group);
        });
        arrRefreshLabels();
    })();

    // Mode picker
    document.querySelectorAll('input[name="arr_mode"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const isMixed = this.value === 'mixed';
            document.getElementById('arr-grid-ui').style.display = isMixed ? 'none' : '';
            document.getElementById('arr-mixed-ui').style.display = isMixed ? '' : 'none';
            document.getElementById('arr-mode-group-label').classList.toggle('active', !isMixed);
            document.getElementById('arr-mode-mixed-label').classList.toggle('active', isMixed);
        });
    });

    function applyArrangement() {
        const isMixed = document.querySelector('input[name="arr_mode"]:checked').value === 'mixed';
        let newPartGrid = '';
        let newPartOrder = '';
        let newLayout = document.querySelector('input[name="layout"]').value;
        if (!isMixed) {
            const groupRows = Array.from(arrGrid.querySelectorAll('.grid-group')).map(g =>
                Array.from(g.querySelectorAll('.part-item')).map(i => i.dataset.part).join(',')
            ).filter(Boolean);
            newPartGrid = groupRows.length > 1 ? groupRows.join(';') : '';
            newLayout = groupRows.length > 1 ? 'grid' : 'side-by-side';
            newPartOrder = groupRows.map(r => r.split(',')).flat().join(',');
        } else {
            newPartOrder = CHART_CONFIG.partOrder.join(',');
            newLayout = 'side-by-side';
        }
        const form = document.createElement('form');
        form.method = 'post';
        form.action = CHART_CONFIG.editUrl;
        const fields = {
            singers_data: document.querySelector('input[name="singers_data"]').value,
            part_order:   newPartOrder,
            part_grid:    newPartGrid,
            layout:       newLayout,
            num_singers:  document.querySelector('input[name="num_singers"]').value,
            rows:         document.querySelector('input[name="rows"]')?.value || '',
            max_per_row:  document.querySelector('input[name="max_per_row"]')?.value || '',
            staggered:    document.querySelector('input[name="staggered"]').value,
            flipped:      document.querySelector('input[name="flipped"]').value,
            mixed:        isMixed ? 'true' : 'false',
            aisle_after:  document.querySelector('input[name="aisle_after"]').value,
            chart_title:  document.getElementById('chart-title')?.value || '',
        };
        for (const [k, v] of Object.entries(fields)) {
            const inp = document.createElement('input');
            inp.type = 'hidden'; inp.name = k; inp.value = v;
            form.appendChild(inp);
        }
        document.body.appendChild(form);
        form.submit();
    }

    window.applyArrangement = applyArrangement;

    // Seed initial undo state and run height check on page load
    pushHistory();
    checkHeightWarnings();
}

// Export chart as PNG image (available in both editable and read-only views)
function exportImage() {
    const panel = document.querySelector('.chart-panel');
    const titleEl = document.getElementById('chart-title');
    const titleVal = titleEl ? titleEl.value.trim() : '';
    const fullW = panel.scrollWidth;
    const titleHeight = titleVal ? 56 : 0; // extra px for title header

    html2canvas(panel, {
        scale: 2,
        backgroundColor: '#ffffff',
        useCORS: true,
        width: fullW,
        height: panel.scrollHeight + titleHeight,
        windowWidth: fullW + 200,
        scrollX: 0,
        scrollY: 0,
        onclone: (clonedDoc) => {
            const p = clonedDoc.querySelector('.chart-panel');
            p.style.overflow = 'visible';
            p.style.width = fullW + 'px';
            p.style.minWidth = 'unset';

            // Remove height warning highlights from the exported image
            clonedDoc.querySelectorAll('.height-warn, .height-warn-back')
                .forEach(el => el.classList.remove('height-warn', 'height-warn-back'));

            // Inject title above the chart
            if (titleVal) {
                const h = clonedDoc.createElement('div');
                h.style.cssText = 'font-size:1.2rem;font-weight:700;text-align:center;padding-bottom:0.75rem;color:#111827;font-family:system-ui,sans-serif;';
                h.textContent = titleVal;
                p.insertBefore(h, p.firstChild);
            }

            const wrapper = p.querySelector('.chart-wrapper');
            if (wrapper) {
                wrapper.style.width = 'max-content';
                wrapper.style.minWidth = 'unset';
                wrapper.style.margin = '0';
            }
            const container = p.querySelector('.chart-container');
            if (container) {
                container.style.overflow = 'visible';
                container.style.width = 'max-content';
                container.style.minWidth = 'unset';
            }
        }
    }).then(canvas => {
        const link = document.createElement('a');
        const safeName = titleVal
            ? titleVal.replace(/[^a-z0-9]+/gi, '-').toLowerCase().replace(/^-|-$/g, '')
            : 'seating-chart';
        link.download = safeName + '.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
    });
}

window.exportImage = exportImage;
