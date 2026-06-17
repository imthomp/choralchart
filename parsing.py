"""Roster parsing — CSV, Excel, and inline name/height formats."""

import csv
import io

import openpyxl

from seating_algorithm import Singer


def parse_name_line(line: str) -> tuple:
    """Parse 'Name' or 'Name, height' into (name, height_or_None).

    Accepted height formats: 66  66"  5'6  5'6"
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
    """Parse a height string into total inches."""
    s = s.strip().rstrip('"').strip()
    if "'" in s:
        parts = s.split("'", 1)
        feet = int(parts[0].strip())
        inches_str = parts[1].strip().rstrip('"').strip()
        inches = float(inches_str) if inches_str else 0.0
        return feet * 12 + inches
    return float(s)


def parse_csv(content: str) -> list[Singer]:
    """Parse CSV text into Singer objects.

    Expects header row with at least 'name' and 'voice_part' columns.
    'height' column is optional.
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
            singers.append(Singer(name=name, voice_part=voice_part, height=float(height_str)))
        except (ValueError, KeyError):
            continue
    return singers


def parse_xlsx(data: bytes) -> list[Singer]:
    """Parse an Excel (.xlsx) file into Singer objects.

    Expects columns: name, voice_part, height (header row, any order).
    Height is optional — rows without it are still accepted.
    """
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    ws = wb.active
    singers = []
    headers = None
    for row in ws.iter_rows(values_only=True):
        if all(cell is None for cell in row):
            continue
        if headers is None:
            headers = [str(c).strip().lower() if c is not None else '' for c in row]
            continue
        row_dict = dict(zip(headers, row))
        name = str(row_dict.get('name', '') or '').strip()
        voice_part = str(row_dict.get('voice_part', '') or '').strip()
        if not name or not voice_part:
            continue
        height = None
        height_raw = row_dict.get('height')
        if height_raw is not None:
            try:
                height = float(height_raw)
            except (ValueError, TypeError):
                pass
        singers.append(Singer(name=name, voice_part=voice_part, height=height))
    wb.close()
    return singers
