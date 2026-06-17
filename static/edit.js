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
        document.querySelectorAll('.row-label').forEach(lbl => {
            lbl.style.transition = 'opacity 0.18s ease';
            lbl.style.opacity = '0.3';
            setTimeout(() => { lbl.style.opacity = '1'; }, 180);
        });
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

    // Drag and drop
    const partOrder = CHART_CONFIG.partOrder;
    let selectedSeat = null;

    function getPartIndex(voicePart) {
        const idx = partOrder.indexOf(voicePart);
        return idx >= 0 ? idx : 0;
    }

    function updateSeatDisplay(seatEl, singerData) {
        const seatNum = parseInt(seatEl.dataset.pos) + 1;

        if (singerData) {
            const partIdx = getPartIndex(singerData.voice_part);
            seatEl.className = `seat part-${partIdx} draggable`;
            seatEl.draggable = true;
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
            seatEl.draggable = false;
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

    // Drag and drop events
    document.querySelectorAll('.seat').forEach(seat => {
        seat.addEventListener('dragstart', (e) => {
            e.target.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        });

        seat.addEventListener('dragend', (e) => {
            e.target.classList.remove('dragging');
            document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
        });

        seat.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            e.currentTarget.classList.add('drag-over');
        });

        seat.addEventListener('dragleave', (e) => {
            e.currentTarget.classList.remove('drag-over');
        });

        seat.addEventListener('drop', (e) => {
            e.preventDefault();
            e.currentTarget.classList.remove('drag-over');
            const dragging = document.querySelector('.dragging');
            if (dragging && dragging !== e.currentTarget) {
                swapSeats(dragging, e.currentTarget);
            }
        });

        seat.addEventListener('click', (e) => {
            if (selectedSeat === null) {
                selectedSeat = e.currentTarget;
                selectedSeat.classList.add('selected');
            } else if (selectedSeat === e.currentTarget) {
                selectedSeat.classList.remove('selected');
                selectedSeat = null;
            } else {
                swapSeats(selectedSeat, e.currentTarget);
                selectedSeat.classList.remove('selected');
                selectedSeat = null;
            }
        });

        seat.addEventListener('dblclick', (e) => {
            e.preventDefault();
            const seatEl = e.currentTarget;
            if (seatEl.dataset.singer === 'null') return;
            if (selectedSeat) {
                selectedSeat.classList.remove('selected');
                selectedSeat = null;
            }
            const singer = JSON.parse(seatEl.dataset.singer);
            openModal(seatEl, singer);
        });
    });

    // Modal functionality
    let editingSeat = null;

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
        document.getElementById('modal-name').value = singer.name;
        document.getElementById('modal-height').value = heightToInputStr(singer.height);
        document.getElementById('modal-part').value = singer.voice_part;
        document.getElementById('edit-modal').classList.add('active');
        setTimeout(() => document.getElementById('modal-name').select(), 10);
    }

    function closeModal() {
        editingSeat = null;
        document.getElementById('edit-modal').classList.remove('active');
    }

    function savePart() {
        if (!editingSeat) return;
        const singer = JSON.parse(editingSeat.dataset.singer);
        const newName = document.getElementById('modal-name').value.trim();
        if (!newName) { document.getElementById('modal-name').focus(); return; }
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
        document.querySelectorAll('.seat.height-warn').forEach(el => el.classList.remove('height-warn'));

        const isStaggered = document.querySelector('.chart-container').classList.contains('staggered');
        const rows = Array.from(document.querySelectorAll('.chart-row'));
        for (let i = 0; i < rows.length - 1; i++) {
            const backRow = rows[i];
            const frontRow = rows[i + 1];
            const backIsOffset = backRow.classList.contains('stagger-offset');
            const frontIsOffset = frontRow.classList.contains('stagger-offset');

            const backHeights = {};
            backRow.querySelectorAll('.seat:not(.empty)').forEach(seat => {
                const singer = JSON.parse(seat.dataset.singer);
                if (singer && singer.height !== null) {
                    backHeights[parseInt(seat.dataset.pos)] = singer.height;
                }
            });

            frontRow.querySelectorAll('.seat:not(.empty)').forEach(seat => {
                const singer = JSON.parse(seat.dataset.singer);
                if (!singer || singer.height === null) return;
                const pos = parseInt(seat.dataset.pos);
                let posesToCheck;
                if (isStaggered) {
                    if (frontIsOffset && !backIsOffset) {
                        posesToCheck = [pos, pos + 1];
                    } else if (!frontIsOffset && backIsOffset) {
                        posesToCheck = [pos - 1, pos];
                    } else {
                        posesToCheck = [pos];
                    }
                } else {
                    posesToCheck = [pos];
                }
                const warned = posesToCheck.some(p => {
                    const bh = backHeights[p];
                    return bh !== undefined && singer.height > bh;
                });
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
            staggered:    document.querySelector('input[name="staggered"]').value,
            flipped:      document.querySelector('input[name="flipped"]').value,
            mixed:        isMixed ? 'true' : 'false',
            aisle_after:  document.querySelector('input[name="aisle_after"]').value,
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
    const fullW = panel.scrollWidth;
    const fullH = panel.scrollHeight;

    html2canvas(panel, {
        scale: 2,
        backgroundColor: '#ffffff',
        useCORS: true,
        width: fullW,
        height: fullH,
        windowWidth: fullW + 200,
        scrollX: 0,
        scrollY: 0,
        onclone: (clonedDoc) => {
            const p = clonedDoc.querySelector('.chart-panel');
            p.style.overflow = 'visible';
            p.style.width = fullW + 'px';
            p.style.height = fullH + 'px';
            p.style.minWidth = 'unset';
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
        link.download = 'seating-chart.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
    });
}

window.exportImage = exportImage;
