"""
Tests for app.py — utility functions and Flask routes.
"""
import base64
import json
import pytest
from app import app as flask_app, parse_name_line, _parse_height, parse_csv


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    flask_app.testing = True
    with flask_app.test_client() as c:
        yield c


def _encode_singers(singers_list):
    """Encode a list of singer dicts as the form expects."""
    return base64.b64encode(json.dumps(singers_list).encode()).decode()


SIMPLE_ROSTER = _encode_singers([
    {"name": "Alice", "voice_part": "Soprano", "height": 63},
    {"name": "Bob",   "voice_part": "Alto",    "height": 65},
    {"name": "Carol", "voice_part": "Soprano", "height": 62},
    {"name": "Dave",  "voice_part": "Alto",    "height": 67},
])


# ---------------------------------------------------------------------------
# parse_name_line
# ---------------------------------------------------------------------------

class TestParseNameLine:
    def test_name_only(self):
        name, height = parse_name_line("John Smith")
        assert name == "John Smith"
        assert height is None

    def test_name_with_inches(self):
        name, height = parse_name_line("John Smith, 66")
        assert name == "John Smith"
        assert height == 66.0

    def test_name_with_inches_and_quote(self):
        name, height = parse_name_line('John Smith, 66"')
        assert name == "John Smith"
        assert height == 66.0

    def test_name_with_feet_and_inches(self):
        name, height = parse_name_line("John Smith, 5'6")
        assert name == "John Smith"
        assert height == 66.0

    def test_name_with_feet_inches_and_quotes(self):
        name, height = parse_name_line('John Smith, 5\'6"')
        assert name == "John Smith"
        assert height == 66.0

    def test_name_with_comma_no_height(self):
        # Trailing comma with no numeric part → treated as name only
        name, height = parse_name_line("Smith, Jr.")
        assert height is None

    def test_strips_whitespace(self):
        name, height = parse_name_line("  Alice  ")
        assert name == "Alice"


# ---------------------------------------------------------------------------
# _parse_height
# ---------------------------------------------------------------------------

class TestParseHeight:
    def test_plain_inches(self):
        assert _parse_height("66") == 66.0

    def test_inches_with_quote(self):
        assert _parse_height('66"') == 66.0

    def test_feet_no_inches(self):
        assert _parse_height("5'") == 60.0

    def test_feet_and_inches(self):
        assert _parse_height("5'6") == 66.0

    def test_feet_inches_with_quote(self):
        assert _parse_height("5'6\"") == 66.0

    def test_six_feet(self):
        assert _parse_height("6'0") == 72.0

    def test_decimal_inches(self):
        assert _parse_height("65.5") == 65.5


# ---------------------------------------------------------------------------
# parse_csv
# ---------------------------------------------------------------------------

class TestParseCsv:
    def test_valid_csv(self):
        csv = "name,voice_part,height\nAlice,Soprano,63\nBob,Bass,70\n"
        singers = parse_csv(csv)
        assert len(singers) == 2
        assert singers[0].name == "Alice"
        assert singers[1].voice_part == "Bass"

    def test_skips_missing_fields(self):
        csv = "name,voice_part,height\nAlice,,63\n,Bass,70\n"
        singers = parse_csv(csv)
        assert len(singers) == 0

    def test_empty_csv(self):
        assert parse_csv("name,voice_part,height\n") == []

    def test_decimal_height(self):
        csv = "name,voice_part,height\nAlice,Soprano,63.5\n"
        singers = parse_csv(csv)
        assert singers[0].height == 63.5


# ---------------------------------------------------------------------------
# Flask routes — smoke tests
# ---------------------------------------------------------------------------

class TestRoutes:
    def test_index_loads(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_configure_manual_entry(self, client):
        r = client.post("/configure", data={
            "entry_type": "manual",
            "part_name": ["Soprano", "Alto"],
            "part_names_list": ["Alice\nBob\nCarol", "Dave\nEve"],
        })
        # Redirects to configure page (200) or edit (200)
        assert r.status_code == 200

    def test_configure_random_roster(self, client):
        r = client.post("/configure", data={
            "entry_type": "random",
            "num_singers": "20",
            "parts": "Soprano,Alto,Tenor,Bass",
        })
        assert r.status_code == 200

    def test_configure_random_out_of_range(self, client):
        r = client.post("/configure", data={
            "entry_type": "random",
            "num_singers": "0",
            "parts": "Soprano",
        })
        # Should redirect back to index with flash
        assert r.status_code == 302

    def test_edit_generates_chart(self, client):
        r = client.post("/edit", data={
            "singers_data": SIMPLE_ROSTER,
            "part_grid": "Soprano,Alto",
            "staggered": "true",
        })
        assert r.status_code == 200
        assert b"Edit Chart" in r.data

    def test_edit_with_flat_part_order(self, client):
        r = client.post("/edit", data={
            "singers_data": SIMPLE_ROSTER,
            "layout": "side-by-side",
            "part_order": "Soprano, Alto",
            "staggered": "true",
        })
        assert r.status_code == 200

    def test_edit_with_grid_layout(self, client):
        roster = _encode_singers([
            {"name": "Alice",  "voice_part": "Soprano", "height": 63},
            {"name": "Bob",    "voice_part": "Bass",    "height": 70},
            {"name": "Carol",  "voice_part": "Tenor",   "height": 68},
            {"name": "Dave",   "voice_part": "Alto",    "height": 65},
            {"name": "Eve",    "voice_part": "Soprano", "height": 61},
            {"name": "Frank",  "voice_part": "Bass",    "height": 72},
        ])
        r = client.post("/edit", data={
            "singers_data": roster,
            "part_grid": "Alto,Bass;Soprano,Tenor",
            "staggered": "true",
        })
        assert r.status_code == 200
        assert b"Edit Chart" in r.data

    def test_upload_no_file(self, client):
        r = client.post("/upload")
        assert r.status_code == 302  # redirect back

    def test_upload_bad_extension(self, client):
        from io import BytesIO
        r = client.post("/upload", data={
            "file": (BytesIO(b"content"), "roster.txt")
        }, content_type="multipart/form-data")
        assert r.status_code == 302

    def test_load_valid_choralchart(self, client):
        from io import BytesIO
        # Build a minimal valid .choralchart payload
        chart_payload = client.post("/edit", data={
            "singers_data": SIMPLE_ROSTER,
            "part_grid": "Soprano,Alto",
            "staggered": "true",
        })
        assert chart_payload.status_code == 200

        # Simulate what saveChart() would produce
        save_data = json.dumps({
            "version": 1,
            "chart_data": base64.b64encode(json.dumps([
                [{"row": 0, "position": 0, "singer": {"name": "Alice", "voice_part": "Soprano", "height": 63}},
                 {"row": 0, "position": 1, "singer": None}]
            ]).encode()).decode(),
            "part_order": "Soprano, Alto",
            "part_grid": "Soprano,Alto",
            "layout": "grid",
            "singers_data": SIMPLE_ROSTER,
            "num_singers": "4",
            "staggered": "true",
            "flipped": "false",
        })
        r = client.post("/load", data={
            "file": (BytesIO(save_data.encode()), "chart.choralchart")
        }, content_type="multipart/form-data")
        assert r.status_code == 200
        assert b"Edit Chart" in r.data

    def test_load_invalid_file(self, client):
        from io import BytesIO
        r = client.post("/load", data={
            "file": (BytesIO(b"not json at all"), "chart.choralchart")
        }, content_type="multipart/form-data")
        assert r.status_code == 302  # redirect back with flash

    def test_load_no_file(self, client):
        r = client.post("/load")
        assert r.status_code == 302
