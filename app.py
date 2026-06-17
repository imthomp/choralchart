"""Flask routes for ChoralChart."""

import base64
import json
import os
import secrets

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from db import get_db, init_db
from parsing import parse_name_line, parse_csv, parse_xlsx
from seating_algorithm import (
    Singer,
    generate_seating_chart,
    calculate_dimensions_with_user_input,
    generate_random_roster,
    calculate_min_width,
    calculate_min_width_grid,
    find_single_wide_parts,
    calculate_stagger_offsets,
    encode_chart,
    decode_chart,
)

app = Flask(__name__)
app.secret_key = 'dev-secret-key'

init_db()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/configure', methods=['POST'])
def configure_post():
    """Handle manual entry and random roster, generate chart, open editor."""
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

        return render_template('edit.html', **generate_chart_from_form(singers=singers))

    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))


@app.route('/upload', methods=['POST'])
def upload():
    """Handle CSV/Excel upload and open editor directly."""
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
        singers = parse_xlsx(file.read()) if filename.endswith('.xlsx') \
            else parse_csv(file.read().decode('utf-8'))

        if not singers:
            flash('No valid singers found in file')
            return redirect(url_for('index'))

        return render_template('edit.html', **generate_chart_from_form(singers=singers))

    except Exception as e:
        flash(f'Error processing file: {str(e)}')
        return redirect(url_for('index'))


@app.route('/sample/<name>')
def load_sample(name):
    """Load a built-in sample roster and open the editor."""
    allowed = {'satb_choir', 'mens_chorus', 'womens_chorus'}
    if name not in allowed:
        flash('Sample not found')
        return redirect(url_for('index'))

    path = os.path.join(app.static_folder, 'samples', f'{name}.csv')
    with open(path, encoding='utf-8') as f:
        singers = parse_csv(f.read())

    if not singers:
        flash('Sample roster is empty')
        return redirect(url_for('index'))

    part_order = list(dict.fromkeys(s.voice_part for s in singers))
    rows, seats_per_row = calculate_dimensions_with_user_input(
        len(singers), len(part_order), 'side-by-side', None, None
    )
    seats_per_row = max(seats_per_row, calculate_min_width(singers, part_order, rows))
    chart = generate_seating_chart(singers, rows, seats_per_row, part_order, 'side-by-side')

    return render_template('edit.html',
        editable=True,
        chart=chart,
        chart_data=encode_chart(chart),
        num_singers=len(singers),
        part_order=part_order,
        layout='side-by-side',
        rows=rows,
        seats_per_row=seats_per_row,
        flipped=False,
        staggered=True,
        curved=False,
        aisle_after=None,
        singers_data=base64.b64encode(
            json.dumps([{'name': s.name, 'voice_part': s.voice_part, 'height': s.height}
                        for s in singers]).encode()
        ).decode(),
        stagger_offsets=calculate_stagger_offsets(chart),
        single_wide_parts=find_single_wide_parts(chart, part_order),
        part_grid_str='',
        mixed=False,
        chart_title='',
    )


@app.route('/edit', methods=['POST'])
def edit():
    """Open the editor (regenerating or restoring an existing chart)."""
    try:
        return render_template('edit.html', **get_chart_data_from_form())
    except ValueError as e:
        flash(str(e))
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error loading editor: {str(e)}')
        return redirect(url_for('index'))


@app.route('/load', methods=['POST'])
def load():
    """Restore a previously saved .choralchart file."""
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
        mixed = data.get('mixed') == 'true'
        aisle_str = data.get('aisle_after', '')
        aisle_after = int(aisle_str) if aisle_str else None

        return render_template('edit.html',
            editable=True,
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
            aisle_after=aisle_after,
            mixed=mixed,
            singers_data=data.get('singers_data', ''),
            stagger_offsets=calculate_stagger_offsets(chart),
            single_wide_parts=[] if mixed else find_single_wide_parts(chart, part_order),
            part_grid_str=data.get('part_grid', ''),
            chart_title=data.get('chart_title', ''),
        )
    except Exception as e:
        flash(f'Error loading chart: {str(e)}')
        return redirect(url_for('index'))


@app.route('/share', methods=['POST'])
def share():
    """Save chart state and return a shareable URL (creates or updates)."""
    chart_id = request.form.get('share_id', '').strip() or secrets.token_urlsafe(6)

    with get_db() as db:
        db.execute('''
            INSERT INTO charts
                (id, chart_data, part_order, part_grid, layout, singers_data,
                 num_singers, staggered, flipped, mixed, title, aisle_after, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
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
                aisle_after=excluded.aisle_after,
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
            request.form.get('aisle_after', ''),
        ))

    return jsonify({'id': chart_id, 'url': url_for('view_chart', chart_id=chart_id, _external=True)})


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
    aisle_str = row['aisle_after'] or ''
    aisle_after = int(aisle_str) if aisle_str else None

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
        aisle_after=aisle_after,
        singers_data=row['singers_data'] or '',
        stagger_offsets=calculate_stagger_offsets(chart),
        single_wide_parts=[],
        part_grid_str=row['part_grid'] or '',
        chart_title=row['title'] or '',
    )


# ---------------------------------------------------------------------------
# Form helpers
# ---------------------------------------------------------------------------

def generate_chart_from_form(singers=None) -> dict:
    """Parse form data and generate a seating chart.

    If `singers` is provided (pre-parsed Singer list), skip decoding singers_data.
    """
    if singers is None:
        singers_json = request.form.get('singers_data', '')
        singers_data = json.loads(base64.b64decode(singers_json).decode())
        singers = [Singer(**s) for s in singers_data]

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
        seen: dict = {}
        for s in singers:
            seen[s.voice_part] = None
        part_order = list(seen.keys())

    mixed = request.form.get('mixed') == 'true'

    row_sizes_str = request.form.get('row_sizes', '').strip()
    if row_sizes_str:
        row_sizes = [int(s.strip()) for s in row_sizes_str.split(',') if s.strip()]
        rows = len(row_sizes)
        seats_per_row = max(row_sizes)
        chart = generate_seating_chart(singers, rows, seats_per_row, part_order, layout,
                                       row_sizes, mixed=mixed)
    else:
        rows_str = request.form.get('rows', '').strip()
        max_per_row_str = request.form.get('max_per_row', '').strip()
        user_rows = int(rows_str) if rows_str else None
        user_max_per_row = int(max_per_row_str) if max_per_row_str else None

        rows, seats_per_row = calculate_dimensions_with_user_input(
            len(singers), len(part_order), layout, user_rows, user_max_per_row
        )

        if layout == 'side-by-side':
            seats_per_row = max(seats_per_row, calculate_min_width(singers, part_order, rows))
        elif layout == 'grid' and part_grid:
            seats_per_row = max(seats_per_row, calculate_min_width_grid(singers, part_grid, rows))

        chart = generate_seating_chart(singers, rows, seats_per_row, part_order, layout,
                                       part_grid=part_grid, mixed=mixed)

    aisle_str = request.form.get('aisle_after', '').strip()
    aisle_after = int(aisle_str) if aisle_str else None

    singers_data_encoded = request.form.get('singers_data', '') or base64.b64encode(
        json.dumps([{'name': s.name, 'voice_part': s.voice_part, 'height': s.height}
                    for s in singers]).encode()
    ).decode()

    return {
        'editable': True,
        'chart': chart,
        'chart_data': encode_chart(chart),
        'num_singers': len(singers),
        'part_order': part_order,
        'layout': layout,
        'rows': rows,
        'seats_per_row': seats_per_row,
        'flipped': request.form.get('flipped') == 'true',
        'staggered': request.form.get('staggered') == 'true',
        'curved': request.form.get('curved') == 'true',
        'aisle_after': aisle_after,
        'singers_data': singers_data_encoded,
        'stagger_offsets': calculate_stagger_offsets(chart),
        'single_wide_parts': [] if mixed else find_single_wide_parts(chart, part_order),
        'part_grid_str': part_grid_str,
        'mixed': mixed,
    }


def get_chart_data_from_form() -> dict:
    """Restore chart from encoded form data, or regenerate if none present."""
    chart_json = request.form.get('chart_data', '')
    if not chart_json:
        return generate_chart_from_form()

    chart = decode_chart(chart_json)
    part_order = [p.strip() for p in request.form.get('part_order', '').split(',') if p.strip()]
    mixed = request.form.get('mixed') == 'true'
    aisle_str = request.form.get('aisle_after', '').strip()

    return {
        'editable': True,
        'chart': chart,
        'chart_data': chart_json,
        'num_singers': int(request.form.get('num_singers', 0)),
        'part_order': part_order,
        'layout': request.form.get('layout', 'side-by-side'),
        'rows': len(chart),
        'seats_per_row': len(chart[0]) if chart else 0,
        'flipped': request.form.get('flipped') == 'true',
        'staggered': request.form.get('staggered') == 'true',
        'curved': request.form.get('curved') == 'true',
        'aisle_after': int(aisle_str) if aisle_str else None,
        'singers_data': request.form.get('singers_data', ''),
        'stagger_offsets': calculate_stagger_offsets(chart),
        'single_wide_parts': [] if mixed else find_single_wide_parts(chart, part_order),
        'part_grid_str': request.form.get('part_grid', ''),
        'mixed': mixed,
    }


if __name__ == '__main__':
    app.run(debug=True)
