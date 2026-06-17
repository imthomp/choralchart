"""
Flask application for choir seating chart generation.
"""

import csv
import io
import json
import base64
import sqlite3
import secrets
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import openpyxl

from seating_algorithm import (
    Singer, generate_seating_chart, get_unique_parts,
    calculate_dimensions_with_user_input, generate_random_roster,
    calculate_min_width, calculate_min_width_grid
)

app = Flask(__name__)
app.secret_key = 'dev-secret-key'  # For flash messages

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'charts.db'))


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS charts (
                id TEXT PRIMARY KEY,
                chart_data TEXT NOT NULL,
                part_order TEXT NOT NULL,
                part_grid TEXT,
                layout TEXT,
                singers_data TEXT,
                num_singers INTEGER,
                staggered TEXT,
                flipped TEXT,
                mixed TEXT,
                title TEXT,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        ''')


init_db()


@app.route('/', methods=['GET'])
def index():
    """Display the upload form."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Handle CSV upload and show configuration page."""
    if 'file' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))

    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
        flash('Please upload a CSV or Excel (.xlsx) file')
        return redirect(url_for('index'))

    try:
        if filename.endswith('.xlsx'):
            singers = parse_xlsx(file.read())
        else:
            content = file.read().decode('utf-8')
            singers = parse_csv(content)

        if not singers:
            flash('No valid singers found in file')
            return redirect(url_for('index'))

        return show_configure_page(singers)

    except Exception as e:
        flash(f'Error processing file: {str(e)}')
        return redirect(url_for('index'))


@app.route('/configure', methods=['POST'])
def configure_post():
    """Handle both manual entry and random roster, then show configuration page."""
    try:
        entry_type = request.form.get('entry_type', 'manual')

        if entry_type == 'random':
            num_singers_str = request.form.get('num_singers', '').strip()
            num_singers = int(num_singers_str) if num_singers_str else 40
            parts_str = request.form.get('parts', '').strip() or 'Soprano,Alto,Tenor,Bass'
            parts = [p.strip() for p in parts_str.split(',') if p.strip()]

            if num_singers < 1 or num_singers > 500:
                flash('Number of singers must be between 1 and 500')
                return redirect(url_for('index'))

            if not parts:
                flash('Please specify at least one voice part')
                return redirect(url_for('index'))

            singers = generate_random_roster(num_singers, parts)

        else:
            part_names = request.form.getlist('part_name')
            part_name_lists = request.form.getlist('part_names_list')

            singers = []
            for part, names_block in zip(part_names, part_name_lists):
                part = part.strip()
                if not part:
                    continue
                for line in names_block.splitlines():
                    line = line.strip()
                    if line:
                        name, height = parse_name_line(line)
                        if name:
                            singers.append(Singer(name=name, voice_part=part, height=height))

            if not singers:
                flash('Please add at least one singer name')
                return redirect(url_for('index'))

        chart_data = generate_chart_from_form(singers=singers)
        return render_template('edit.html', **chart_data)

    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))


def show_configure_page(singers: list[Singer]):
    """Show the configuration page for a list of singers."""
    parts = get_unique_parts(singers)
    singers_data = [
        {'name': s.name, 'voice_part': s.voice_part, 'height': s.height}
        for s in singers
    ]
    singers_json = base64.b64encode(json.dumps(singers_data).encode()).decode()

    return render_template('configure.html',
                           parts=parts,
                           num_singers=len(singers),
                           singers_data=singers_json,
                           singers=singers)


@app.route('/preview', methods=['POST'])
def preview():
    return redirect(url_for('index'))


@app.route('/edit', methods=['POST'])
def edit():
    """Show editable seating chart with drag/drop."""
    try:
        chart_data = get_chart_data_from_form()
        return render_template('edit.html', **chart_data)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error loading editor: {str(e)}')
        return redirect(url_for('index'))


@app.route('/load', methods=['POST'])
def load():
    """Restore a previously saved .choralchart JSON file."""
    file = request.files.get('file')
    if not file or file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))

    try:
        data = json.loads(file.read().decode('utf-8'))

        if 'chart_data' not in data or 'part_order' not in data:
            flash('Invalid chart file — missing required fields')
            return redirect(url_for('index'))

        chart = decode_chart(data['chart_data'])
        part_order = [p.strip() for p in data['part_order'].split(',') if p.strip()]
        stagger_offsets = calculate_stagger_offsets(chart)

        return render_template('edit.html',
            chart=chart,
            chart_data=data['chart_data'],
            num_singers=int(data.get('num_singers', 0)),
            part_order=part_order,
            layout=data.get('layout', 'side-by-side'),
            rows=len(chart),
            seats_per_row=len(chart[0]) if chart else 0,
            flipped=data.get('flipped') == 'true',
            staggered=data.get('staggered') == 'true',
            curved=False,
            aisle_after=None,
            singers_data=data.get('singers_data', ''),
            stagger_offsets=stagger_offsets,
            single_wide_parts=[],
            part_grid_str=data.get('part_grid', ''),
        )
    except Exception as e:
        flash(f'Error loading chart: {str(e)}')
        return redirect(url_for('index'))


def generate_chart_from_form(singers=None) -> dict:
    """Parse form data and generate a new seating chart.

    If `singers` is provided (already-parsed list of Singer objects), skip
    decoding singers_data from the form.  This lets configure_post pass
    pre-parsed singers directly without re-encoding them.
    """
    if singers is None:
        singers_json = request.form.get('singers_data', '')
        singers_data = json.loads(base64.b64decode(singers_json).decode())
        singers = [Singer(**s) for s in singers_data]

    # Parse part_grid (2D grid layout) or fall back to flat part_order.
    part_grid_str = request.form.get('part_grid', '').strip()
    part_grid = None
    if part_grid_str:
        part_grid = [
            [p.strip() for p in row.split(',') if p.strip()]
            for row in part_grid_str.split(';')
            if any(p.strip() for p in row.split(','))
        ]
        part_order = [p for group in part_grid for p in group]
        layout = 'grid'
    else:
        layout = request.form.get('layout', 'side-by-side')
        part_order_str = request.form.get('part_order', '')
        part_order = [p.strip() for p in part_order_str.split(',') if p.strip()]

    if not part_order:
        seen = {}
        for s in singers:
            seen[s.voice_part] = None
        part_order = list(seen.keys())

    mixed = request.form.get('mixed') == 'true'

    # Check for variable row sizes first
    row_sizes_str = request.form.get('row_sizes', '').strip()
    if row_sizes_str:
        # Parse variable row sizes (back to front)
        row_sizes = [int(s.strip()) for s in row_sizes_str.split(',') if s.strip()]
        rows = len(row_sizes)
        seats_per_row = max(row_sizes)  # For chart allocation
        chart = generate_seating_chart(singers, rows, seats_per_row, part_order, layout, row_sizes,
                                       mixed=mixed)
    else:
        # Get optional row/seat configuration
        rows_str = request.form.get('rows', '').strip()
        max_per_row_str = request.form.get('max_per_row', '').strip()

        user_rows = int(rows_str) if rows_str else None
        user_max_per_row = int(max_per_row_str) if max_per_row_str else None

        rows, seats_per_row = calculate_dimensions_with_user_input(
            len(singers), len(part_order), layout, user_rows, user_max_per_row
        )

        # Ensure seats_per_row is large enough — cumulative rounding on per-part
        # column widths can exceed the auto-calculated value.
        if layout == 'side-by-side':
            min_width = calculate_min_width(singers, part_order, rows)
            seats_per_row = max(seats_per_row, min_width)
        elif layout == 'grid' and part_grid:
            min_width = calculate_min_width_grid(singers, part_grid, rows)
            seats_per_row = max(seats_per_row, min_width)

        chart = generate_seating_chart(singers, rows, seats_per_row, part_order, layout,
                                       part_grid=part_grid, mixed=mixed)

    # Get display options
    flipped = request.form.get('flipped') == 'true'
    staggered = request.form.get('staggered') == 'true'
    curved = request.form.get('curved') == 'true'

    # Get aisle position
    aisle_str = request.form.get('aisle_after', '').strip()
    aisle_after = int(aisle_str) if aisle_str else None

    # Prepare data for templates
    chart_json = encode_chart(chart)
    stagger_offsets = calculate_stagger_offsets(chart)

    return {
        'chart': chart,
        'chart_data': chart_json,
        'num_singers': len(singers),
        'part_order': part_order,
        'layout': layout,
        'rows': rows,
        'seats_per_row': seats_per_row,
        'flipped': flipped,
        'staggered': staggered,
        'curved': curved,
        'aisle_after': aisle_after,
        'singers_data': request.form.get('singers_data', '') or base64.b64encode(
            json.dumps([{'name': s.name, 'voice_part': s.voice_part, 'height': s.height}
                        for s in singers]).encode()).decode(),
        'stagger_offsets': stagger_offsets,
        'single_wide_parts': [] if mixed else find_single_wide_parts(chart, part_order),
        'part_grid_str': part_grid_str,
        'mixed': mixed,
    }


def get_chart_data_from_form() -> dict:
    """Get chart data from form (either from chart_data or regenerate)."""
    chart_json = request.form.get('chart_data', '')

    if chart_json:
        # Decode existing chart
        chart = decode_chart(chart_json)
    else:
        # Regenerate chart
        return generate_chart_from_form()

    part_order_str = request.form.get('part_order', '')
    part_order = [p.strip() for p in part_order_str.split(',') if p.strip()]
    flipped = request.form.get('flipped') == 'true'
    staggered = request.form.get('staggered') == 'true'
    curved = request.form.get('curved') == 'true'
    aisle_str = request.form.get('aisle_after', '').strip()
    aisle_after = int(aisle_str) if aisle_str else None

    stagger_offsets = calculate_stagger_offsets(chart)

    return {
        'chart': chart,
        'chart_data': chart_json,
        'num_singers': int(request.form.get('num_singers', 0)),
        'part_order': part_order,
        'layout': request.form.get('layout', 'side-by-side'),
        'rows': len(chart),
        'seats_per_row': len(chart[0]) if chart else 0,
        'curved': curved,
        'aisle_after': aisle_after,
        'flipped': flipped,
        'staggered': staggered,
        'singers_data': request.form.get('singers_data', ''),
        'stagger_offsets': stagger_offsets,
        'mixed': request.form.get('mixed') == 'true',
        'single_wide_parts': [] if request.form.get('mixed') == 'true' else find_single_wide_parts(chart, part_order),
        'part_grid_str': request.form.get('part_grid', ''),
    }


def find_single_wide_parts(chart: list, part_order: list) -> list[str]:
    """Return parts that are only one seat wide in every row where they appear."""
    if not chart or not part_order:
        return []

    part_set = set(part_order)
    max_width = {part: 0 for part in part_order}

    for row in chart:
        filled = [seat for seat in row if seat.singer and seat.singer.voice_part in part_set]
        i = 0
        while i < len(filled):
            part = filled[i].singer.voice_part
            run = 1
            while i + run < len(filled) and filled[i + run].singer.voice_part == part:
                run += 1
            if run > max_width[part]:
                max_width[part] = run
            i += run

    return [part for part in part_order if max_width[part] == 1]


def calculate_stagger_offsets(chart) -> list[bool]:
    """
    Calculate which rows need stagger offset for proper brick pattern.

    The offset depends on singer count parity:
    - Same parity as previous row: centering aligns them, need manual offset
    - Different parity: centering naturally offsets by ~half a seat
    """
    if not chart:
        return []

    offsets = [False]  # First row has no offset

    for i in range(1, len(chart)):
        current_count = sum(1 for seat in chart[i] if seat.singer)
        prev_count = sum(1 for seat in chart[i-1] if seat.singer)

        same_parity = (current_count % 2) == (prev_count % 2)

        if same_parity:
            # Centering aligns them - need opposite offset from previous row
            offsets.append(not offsets[i-1])
        else:
            # Centering already staggers them - keep same offset as previous row
            offsets.append(offsets[i-1])

    return offsets


def encode_chart(chart) -> str:
    """Encode a chart to JSON string for form storage."""
    data = []
    for row in chart:
        row_data = []
        for seat in row:
            if seat.singer:
                row_data.append({
                    'row': seat.row,
                    'position': seat.position,
                    'singer': {
                        'name': seat.singer.name,
                        'voice_part': seat.singer.voice_part,
                        'height': seat.singer.height
                    }
                })
            else:
                row_data.append({
                    'row': seat.row,
                    'position': seat.position,
                    'singer': None
                })
        data.append(row_data)
    return base64.b64encode(json.dumps(data).encode()).decode()


def decode_chart(chart_json: str):
    """Decode a chart from JSON string."""
    from seating_algorithm import Seat
    data = json.loads(base64.b64decode(chart_json).decode())
    chart = []
    for row_data in data:
        row = []
        for seat_data in row_data:
            singer = None
            if seat_data.get('singer'):
                singer = Singer(**seat_data['singer'])
            row.append(Seat(
                row=seat_data['row'],
                position=seat_data['position'],
                singer=singer
            ))
        chart.append(row)
    return chart


def parse_name_line(line: str) -> tuple:
    """
    Parse a line that is either just a name, or 'Name, height'.
    Height formats: 66, 66", 5'6, 5'6"
    Returns (name, height_or_None).
    """
    idx = line.rfind(',')
    if idx != -1:
        name_part = line[:idx].strip()
        height_part = line[idx + 1:].strip()
        if height_part and name_part:
            try:
                return name_part, _parse_height(height_part)
            except ValueError:
                pass
    return line.strip(), None


def _parse_height(s: str) -> float:
    """Parse height from strings like '66', '66"', '5\'6"', '5\'6'."""
    s = s.strip().rstrip('"').strip()
    if "'" in s:
        parts = s.split("'", 1)
        feet = int(parts[0].strip())
        inches_str = parts[1].strip().rstrip('"').strip()
        inches = float(inches_str) if inches_str else 0.0
        return feet * 12 + inches
    return float(s)


def parse_xlsx(data: bytes) -> list[Singer]:
    """
    Parse an Excel (.xlsx) file into Singer objects.
    Expects columns: name, voice_part, height (header row, any order).
    Height is optional — rows without it are still accepted.
    """
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    ws = wb.active

    singers = []
    headers = None
    for row in ws.iter_rows(values_only=True):
        # Skip fully empty rows
        if all(cell is None for cell in row):
            continue
        if headers is None:
            headers = [str(c).strip().lower() if c is not None else '' for c in row]
            continue

        row_dict = dict(zip(headers, row))
        name = str(row_dict.get('name', '') or '').strip()
        voice_part = str(row_dict.get('voice_part', '') or '').strip()
        height_raw = row_dict.get('height')

        if not name or not voice_part:
            continue

        height = None
        if height_raw is not None:
            try:
                height = float(height_raw)
            except (ValueError, TypeError):
                pass

        singers.append(Singer(name=name, voice_part=voice_part, height=height))

    wb.close()
    return singers


def parse_csv(content: str) -> list[Singer]:
    """
    Parse CSV content into Singer objects.
    Accepts any voice_part values and supports decimal heights.
    """
    singers = []
    reader = csv.DictReader(io.StringIO(content))

    for row in reader:
        try:
            name = row.get('name', '').strip()
            voice_part = row.get('voice_part', '').strip()
            height_str = row.get('height', '').strip()

            if not name or not voice_part or not height_str:
                continue

            height = float(height_str)
            singers.append(Singer(name=name, voice_part=voice_part, height=height))

        except (ValueError, KeyError):
            continue

    return singers


@app.route('/share', methods=['POST'])
def share():
    """Save a chart and return a shareable ID (or update an existing one)."""
    chart_id = request.form.get('share_id', '').strip()
    if not chart_id:
        chart_id = secrets.token_urlsafe(6)

    with get_db() as db:
        db.execute('''
            INSERT INTO charts
                (id, chart_data, part_order, part_grid, layout, singers_data,
                 num_singers, staggered, flipped, mixed, title, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                chart_data=excluded.chart_data,
                part_order=excluded.part_order,
                part_grid=excluded.part_grid,
                layout=excluded.layout,
                singers_data=excluded.singers_data,
                num_singers=excluded.num_singers,
                staggered=excluded.staggered,
                flipped=excluded.flipped,
                mixed=excluded.mixed,
                title=excluded.title,
                updated_at=datetime('now')
        ''', (
            chart_id,
            request.form.get('chart_data', ''),
            request.form.get('part_order', ''),
            request.form.get('part_grid', ''),
            request.form.get('layout', 'side-by-side'),
            request.form.get('singers_data', ''),
            int(request.form.get('num_singers', 0)),
            request.form.get('staggered', 'false'),
            request.form.get('flipped', 'false'),
            request.form.get('mixed', 'false'),
            request.form.get('chart_title', ''),
        ))

    share_url = url_for('view_chart', chart_id=chart_id, _external=True)
    return jsonify({'id': chart_id, 'url': share_url})


@app.route('/chart/<chart_id>')
def view_chart(chart_id):
    """Public read-only view of a shared chart."""
    with get_db() as db:
        row = db.execute('SELECT * FROM charts WHERE id = ?', (chart_id,)).fetchone()

    if not row:
        flash('Chart not found — it may have expired or the link is incorrect.')
        return redirect(url_for('index'))

    chart = decode_chart(row['chart_data'])
    part_order = [p.strip() for p in row['part_order'].split(',') if p.strip()]
    stagger_offsets = calculate_stagger_offsets(chart)

    return render_template('edit.html',
        editable=False,
        chart=chart,
        chart_data=row['chart_data'],
        num_singers=row['num_singers'],
        part_order=part_order,
        layout=row['layout'] or 'side-by-side',
        rows=len(chart),
        seats_per_row=len(chart[0]) if chart else 0,
        flipped=row['flipped'] == 'true',
        staggered=row['staggered'] == 'true',
        mixed=row['mixed'] == 'true',
        aisle_after=None,
        singers_data=row['singers_data'] or '',
        stagger_offsets=stagger_offsets,
        single_wide_parts=[],
        part_grid_str=row['part_grid'] or '',
        chart_title=row['title'] or '',
    )


if __name__ == '__main__':
    app.run(debug=True)