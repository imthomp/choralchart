"""
Seating algorithm for choir chart generation.
Places singers in straight rows based on voice part and height.
"""

import math
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Singer:
    name: str
    voice_part: str
    height: Optional[float] = None  # in inches, None if unknown

    @property
    def height_display(self) -> str:
        """Return height formatted as feet'inches", or empty string if unknown."""
        if self.height is None:
            return ""
        feet = int(self.height // 12)
        remaining_inches = self.height % 12
        # Check if we have a half inch
        if remaining_inches % 1 == 0.5:
            return f"{feet}'{int(remaining_inches)}.5\""
        elif remaining_inches % 1 == 0:
            return f"{feet}'{int(remaining_inches)}\""
        else:
            # For other decimals, show one decimal place
            return f"{feet}'{remaining_inches:.1f}\""


@dataclass
class Seat:
    row: int
    position: int
    singer: Optional[Singer] = None


def generate_seating_chart(
    singers: List[Singer],
    rows: int,
    seats_per_row: int,
    part_order: List[str],
    layout: str = "side-by-side",
    row_sizes: Optional[List[int]] = None,
    part_grid: Optional[List[List[str]]] = None,
    mixed: bool = False,
) -> List[List[Seat]]:
    """
    Generate a seating chart for straight rows.

    Args:
        singers: List of Singer objects
        rows: Number of rows
        seats_per_row: Number of seats per row (max width)
        part_order: List of voice parts in left-to-right order
        layout: "side-by-side" (parts next to each other) or "stacked" (parts behind each other)
        row_sizes: Optional list of seats per row (back to front), overrides seats_per_row

    Returns:
        2D list of Seat objects (row 0 = back, row -1 = front)
    """
    # Group singers by voice part
    groups = {}
    for part in part_order:
        groups[part] = []

    for singer in singers:
        part = singer.voice_part
        if part in groups:
            groups[part].append(singer)

    # Sort each group by height (tallest first for back rows).
    # Singers with no height are placed in the middle of the group.
    for part in groups:
        known = sorted(
            [s for s in groups[part] if s.height is not None],
            key=lambda s: s.height, reverse=True
        )
        unknown = [s for s in groups[part] if s.height is None]
        mid = len(known) // 2
        groups[part] = known[:mid] + unknown + known[mid:]

    # Initialize empty chart with variable row sizes
    chart = []
    for r in range(rows):
        row_width = row_sizes[r] if row_sizes else seats_per_row
        row = []
        for p in range(row_width):
            row.append(Seat(row=r, position=p, singer=None))
        chart.append(row)

    if layout == "grid" and part_grid:
        _place_grid(chart, groups, part_grid, rows, seats_per_row)
    elif layout == "side-by-side":
        _place_side_by_side_variable(chart, groups, part_order, row_sizes) if row_sizes else _place_side_by_side(chart, groups, part_order, rows, seats_per_row)
    else:  # stacked
        _place_stacked(chart, groups, part_order, rows, seats_per_row)

    if mixed:
        _mix_chart(chart)

    return chart


def _place_side_by_side(
    chart: List[List[Seat]],
    groups: dict,
    part_order: List[str],
    rows: int,
    seats_per_row: int
) -> None:
    """
    Place voice parts side by side (left to right) in columns.
    Each part gets a column width based on ceil(singers/rows).
    Parts are placed adjacently with no gaps.
    """
    num_parts = len(part_order)
    if num_parts == 0:
        return

    total_singers = sum(len(groups[part]) for part in part_order)
    if total_singers == 0:
        return

    # Calculate column width needed for each part (ceil of singers/rows)
    part_widths = []
    for part in part_order:
        count = len(groups[part])
        width = math.ceil(count / rows) if count > 0 else 0
        part_widths.append(width)

    # Total width needed
    total_width = sum(part_widths)

    # Center offset for the whole chart
    chart_offset = (seats_per_row - total_width) // 2

    # Place each part in its column
    current_pos = chart_offset
    for i, part in enumerate(part_order):
        part_width = part_widths[i]
        if part_width > 0:
            _place_section(chart, groups[part],
                           start_row=0, end_row=rows,
                           start_pos=current_pos, end_pos=current_pos + part_width)
            current_pos += part_width


def _place_side_by_side_variable(
    chart: List[List[Seat]],
    groups: dict,
    part_order: List[str],
    row_sizes: List[int]
) -> None:
    """
    Place voice parts side by side with variable row widths.
    Each part gets a strict column section - no mixing between parts.
    """
    num_parts = len(part_order)
    rows = len(row_sizes)
    if num_parts == 0 or rows == 0:
        return

    total_singers = sum(len(groups[part]) for part in part_order)
    if total_singers == 0:
        return

    # Calculate the proportion each part should take
    part_proportions = []
    for part in part_order:
        count = len(groups[part])
        proportion = count / total_singers if total_singers > 0 else 0
        part_proportions.append(proportion)

    # Create queues for each voice part (tallest first)
    queues = {part: list(groups[part]) for part in part_order}

    # For each row, divide it into sections for each part
    for row_idx in range(rows):
        row_width = row_sizes[row_idx]

        # Calculate how many seats each part gets in this row
        part_seats = []
        remaining_width = row_width
        for i, part in enumerate(part_order):
            if i == len(part_order) - 1:
                # Last part gets remaining width
                seats = remaining_width
            else:
                seats = round(row_width * part_proportions[i])
                seats = min(seats, remaining_width)
            part_seats.append(seats)
            remaining_width -= seats

        # Calculate starting position for each part (centered as a group)
        total_used = sum(part_seats)
        start_offset = (row_width - total_used) // 2

        # Place each part's singers in their section
        current_pos = start_offset
        for i, part in enumerate(part_order):
            section_width = part_seats[i]
            if section_width <= 0:
                continue

            # How many singers to place from this part in this row?
            # Distribute evenly across rows based on remaining singers
            remaining_rows = rows - row_idx
            remaining_singers = len(queues[part])
            if remaining_rows > 0 and remaining_singers > 0:
                # Place ceil(remaining/remaining_rows) but capped by section width
                to_place = min(section_width, math.ceil(remaining_singers / remaining_rows))

                # Center within the section
                section_offset = (section_width - to_place) // 2

                for j in range(to_place):
                    if queues[part]:
                        pos = current_pos + section_offset + j
                        if pos < len(chart[row_idx]):
                            chart[row_idx][pos].singer = queues[part].pop(0)

            current_pos += section_width


def _mix_chart(chart: List[List[Seat]]) -> None:
    """
    Rearrange singers so no two neighbors share a voice part — horizontally
    (adjacent seats in the same row) or vertically (same column in adjacent rows).

    Greedy left-to-right placement: pick the most-available part that doesn't
    conflict with the left neighbor or the seat directly above.  When both
    constraints can't be satisfied simultaneously the vertical one is relaxed,
    then the horizontal one, so dominant parts are pushed toward row edges.
    Height-based back-to-front ordering is preserved within each part.
    """
    from collections import defaultdict

    prev_row_parts: dict[int, str] = {}

    for row in chart:
        filled = [(s.position, s.singer) for s in row if s.singer]
        if len(filled) <= 1:
            prev_row_parts = {pos: singer.voice_part for pos, singer in filled}
            continue

        positions = [pos for pos, _ in sorted(filled)]

        part_groups: dict[str, list] = defaultdict(list)
        for _, singer in filled:
            part_groups[singer.voice_part].append(singer)

        # Clear current occupants
        for pos, _ in filled:
            row[pos].singer = None

        pool: dict[str, list] = {part: singers[:] for part, singers in part_groups.items()}

        new_parts: list[str] = []
        for pos in positions:
            forbidden_left = new_parts[-1] if new_parts else None
            forbidden_above = prev_row_parts.get(pos)

            # Candidates sorted by count descending
            candidates = sorted(
                [(part, ss) for part, ss in pool.items() if ss],
                key=lambda x: -len(x[1])
            )

            chosen = None
            # Prefer satisfying both constraints
            for part, _ in candidates:
                if part != forbidden_left and part != forbidden_above:
                    chosen = part
                    break
            # Relax vertical
            if chosen is None:
                for part, _ in candidates:
                    if part != forbidden_left:
                        chosen = part
                        break
            # Relax both (dominant-part fallback)
            if chosen is None and candidates:
                chosen = candidates[0][0]

            singer = pool[chosen].pop(0)
            new_parts.append(chosen)
            row[pos].singer = singer

        prev_row_parts = dict(zip(positions, new_parts))


def _place_grid(
    chart: List[List[Seat]],
    groups: dict,
    part_grid: List[List[str]],
    rows: int,
    seats_per_row: int
) -> None:
    """
    Place voice parts in a 2D grid layout.

    part_grid is ordered back-to-front (index 0 = back rows).
    Parts within each grid row are placed side-by-side.
    Row bands are sized proportionally to their singer counts.

    Example: [['Alto', 'Bass'], ['Soprano', 'Tenor']]
      → Alto and Bass share the back rows, Soprano and Tenor the front rows.
    """
    num_groups = len(part_grid)
    if num_groups == 0:
        return

    group_counts = [
        sum(len(groups.get(p, [])) for p in group)
        for group in part_grid
    ]
    total_singers = sum(group_counts)
    if total_singers == 0:
        return

    # Allocate chart rows proportionally; every group gets at least 1 row.
    row_allocs = []
    remaining = rows
    for i, count in enumerate(group_counts):
        if i == num_groups - 1:
            alloc = remaining
        else:
            proportion = count / total_singers
            alloc = max(1, round(rows * proportion))
            alloc = min(alloc, remaining - (num_groups - i - 1))
        row_allocs.append(alloc)
        remaining -= alloc

    current_row = 0
    for group_idx, group_parts in enumerate(part_grid):
        group_rows = row_allocs[group_idx]
        end_row = current_row + group_rows

        active_parts = [p for p in group_parts if groups.get(p)]
        if active_parts:
            part_widths = [
                math.ceil(len(groups[p]) / group_rows)
                for p in active_parts
            ]
            total_width = sum(part_widths)
            col_offset = (seats_per_row - total_width) // 2

            pos = col_offset
            for part, width in zip(active_parts, part_widths):
                if width > 0:
                    _place_section(chart, groups[part],
                                   start_row=current_row, end_row=end_row,
                                   start_pos=pos, end_pos=pos + width)
                    pos += width

        current_row = end_row


def _place_stacked(
    chart: List[List[Seat]],
    groups: dict,
    part_order: List[str],
    rows: int,
    seats_per_row: int
) -> None:
    """
    Place voice parts stacked (back to front).
    Parts are arranged in horizontal bands from back to front.
    """
    num_parts = len(part_order)
    if num_parts == 0:
        return

    # Divide rows among parts
    rows_per_part = rows // num_parts
    extra_rows = rows % num_parts

    current_row = 0
    for i, part in enumerate(part_order):
        # Give extra rows to back parts
        part_rows = rows_per_part + (1 if i < extra_rows else 0)
        end_row = current_row + part_rows

        _place_section(chart, groups[part],
                       start_row=current_row, end_row=end_row,
                       start_pos=0, end_pos=seats_per_row)
        current_row = end_row


def _place_section(chart: List[List[Seat]], singers: List[Singer],
                   start_row: int, end_row: int,
                   start_pos: int, end_pos: int) -> None:
    """
    Place a group of singers in a rectangular section of the chart.
    Fills from back row to front, centered within each row.
    """
    section_width = end_pos - start_pos
    num_rows = end_row - start_row
    total_singers = len(singers)

    if total_singers == 0 or section_width == 0 or num_rows == 0:
        return

    singer_idx = 0
    for row in range(start_row, end_row):
        # Calculate how many singers go in this row
        remaining = total_singers - singer_idx
        if remaining <= 0:
            break

        # Fill full rows, last row gets remainder
        rows_left = end_row - row
        if rows_left > 1:
            # Not the last row - try to fill evenly
            singers_this_row = min(section_width, math.ceil(remaining / rows_left))
        else:
            # Last row - place all remaining
            singers_this_row = min(section_width, remaining)

        # Calculate centering offset
        offset = (section_width - singers_this_row) // 2

        # Place singers centered in this row
        for i in range(singers_this_row):
            if singer_idx < total_singers:
                pos = start_pos + offset + i
                chart[row][pos].singer = singers[singer_idx]
                singer_idx += 1


def calculate_min_width(singers: List[Singer], part_order: List[str], rows: int) -> int:
    """
    Calculate the minimum seats_per_row needed for side-by-side layout.

    This accounts for per-part column widths which can exceed ceil(total/rows)
    due to cumulative rounding.
    """
    # Count singers per part
    part_counts = {part: 0 for part in part_order}
    for singer in singers:
        if singer.voice_part in part_counts:
            part_counts[singer.voice_part] += 1

    # Calculate width needed for each part
    total_width = 0
    for part in part_order:
        count = part_counts[part]
        width = math.ceil(count / rows) if count > 0 else 0
        total_width += width

    return total_width


def calculate_min_width_grid(
    singers: List[Singer],
    part_grid: List[List[str]],
    rows: int
) -> int:
    """
    Calculate the minimum seats_per_row needed for a grid layout.

    Uses the same row-allocation logic as _place_grid so the result is exact.
    """
    part_counts: dict[str, int] = {}
    for singer in singers:
        part_counts[singer.voice_part] = part_counts.get(singer.voice_part, 0) + 1

    total_singers = sum(part_counts.values())
    num_groups = len(part_grid)
    if total_singers == 0 or num_groups == 0:
        return 1

    group_singer_counts = [
        sum(part_counts.get(p, 0) for p in group) for group in part_grid
    ]

    # Mirror the row-allocation from _place_grid
    row_allocs: list[int] = []
    remaining = rows
    for i, count in enumerate(group_singer_counts):
        if i == num_groups - 1:
            alloc = remaining
        else:
            proportion = count / total_singers
            alloc = max(1, round(rows * proportion))
            alloc = min(alloc, remaining - (num_groups - i - 1))
        row_allocs.append(alloc)
        remaining -= alloc

    max_width = 0
    for group, group_rows in zip(part_grid, row_allocs):
        group_width = sum(
            math.ceil(part_counts.get(p, 0) / group_rows)
            for p in group if part_counts.get(p, 0) > 0
        )
        max_width = max(max_width, group_width)

    return max_width


def calculate_chart_dimensions(num_singers: int, num_parts: int, layout: str) -> tuple[int, int]:
    """
    Calculate reasonable row and seat counts for a given number of singers.

    Args:
        num_singers: Total number of singers
        num_parts: Number of voice parts
        layout: "side-by-side" or "stacked"

    Returns:
        Tuple of (rows, seats_per_row)
    """
    # Aim for roughly 10-15 singers per row
    target_per_row = 12
    rows = max(2, math.ceil(num_singers / target_per_row))

    if layout == "stacked":
        # Make rows divisible by num_parts for clean splits
        while rows % num_parts != 0:
            rows += 1

    seats_per_row = math.ceil(num_singers / rows)

    if layout == "side-by-side":
        # Make seats divisible by num_parts for clean splits
        while seats_per_row % num_parts != 0:
            seats_per_row += 1

    return rows, seats_per_row


def get_unique_parts(singers: List[Singer]) -> List[str]:
    """Extract unique voice parts from singers, preserving first-seen order."""
    seen = set()
    parts = []
    for singer in singers:
        if singer.voice_part not in seen:
            seen.add(singer.voice_part)
            parts.append(singer.voice_part)
    return parts


def calculate_dimensions_with_user_input(
    num_singers: int,
    num_parts: int,
    layout: str,
    user_rows: Optional[int] = None,
    user_max_per_row: Optional[int] = None
) -> tuple[int, int]:
    """
    Calculate chart dimensions, respecting user input where provided.

    Args:
        num_singers: Total number of singers
        num_parts: Number of voice parts
        layout: "side-by-side" or "stacked"
        user_rows: User-specified number of rows (optional)
        user_max_per_row: User-specified max per row (optional, blank = auto)

    Returns:
        Tuple of (rows, seats_per_row)
    """
    if user_rows and user_max_per_row:
        # User specified both - use as-is
        return user_rows, user_max_per_row

    if user_rows and not user_max_per_row:
        # User specified rows only - calculate seats per row
        seats_per_row = math.ceil(num_singers / user_rows)
        if layout == "side-by-side":
            while seats_per_row % num_parts != 0:
                seats_per_row += 1
        return user_rows, seats_per_row

    if user_max_per_row and not user_rows:
        # User specified max per row only - calculate rows
        rows = math.ceil(num_singers / user_max_per_row)
        if layout == "stacked":
            while rows % num_parts != 0:
                rows += 1
        return rows, user_max_per_row

    # Neither specified - auto calculate
    return calculate_chart_dimensions(num_singers, num_parts, layout)


def generate_random_roster(
    num_singers: int,
    parts: List[str],
    height_range: tuple[float, float] = (60, 78),
    distribution: Optional[List[int]] = None,
    seed: Optional[int] = None
) -> List[Singer]:
    """
    Generate a random roster of singers for testing.

    Args:
        num_singers: Number of singers to generate
        parts: List of voice parts to distribute among
        height_range: (min_height, max_height) in inches
        distribution: Optional list of counts per part (must sum to num_singers)
                     If None, distributes evenly with round-robin
        seed: Optional random seed for reproducibility

    Returns:
        List of Singer objects
    """
    import random

    if seed is not None:
        random.seed(seed)

    # First names by gender
    female_names = [
        "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan",
        "Jessica", "Sarah", "Karen", "Emma", "Ava", "Sophia", "Isabella", "Mia",
        "Charlotte", "Amelia", "Harper", "Evelyn", "Abigail", "Emily", "Ella",
        "Madison", "Scarlett", "Victoria", "Grace", "Chloe", "Lily", "Hannah",
        "Natalie", "Zoe", "Leah", "Hazel", "Violet", "Aurora", "Savannah",
        "Audrey", "Bella", "Claire", "Lucy", "Anna", "Caroline",
        # Diverse additions
        "Maria", "Sofia", "Fatima", "Aisha", "Yuki", "Mei", "Priya", "Amara",
        "Zara", "Layla", "Nadia", "Rosa", "Valentina", "Camila", "Aaliyah",
        "Keiko", "Sasha", "Ingrid", "Chiara", "Lena", "Yasmin", "Nour",
        "Xiomara", "Adaeze", "Taraji", "Esperanza", "Miriam", "Hana", "Ines",
        "Celestine", "Amina", "Rania", "Yolanda", "Bianca", "Svetlana"
    ]

    male_names = [
        "James", "John", "Robert", "Michael", "William", "David", "Richard",
        "Joseph", "Thomas", "Charles", "Oliver", "Elijah", "Lucas", "Mason",
        "Logan", "Alexander", "Ethan", "Jacob", "Liam", "Noah", "Aiden",
        "Benjamin", "Henry", "Sebastian", "Jack", "Daniel", "Matthew", "Owen",
        "Ryan", "Nathan", "Connor", "Andrew", "Isaac", "Joshua", "Dylan",
        "Luke", "Gabriel", "Anthony", "Christian", "Jonathan", "Samuel", "Eric",
        # Diverse additions
        "Carlos", "Mateo", "Diego", "Jamal", "Andre", "Kwame", "Rafael",
        "Hiroshi", "Wei", "Arjun", "Ibrahim", "Omar", "Luca", "Nikolai",
        "Tomas", "Ezra", "Kofi", "Malik", "Santiago", "Jin", "Ravi", "Ahmed",
        "Emeka", "Soren", "Dmitri", "Tariq", "Yusuf", "Pascal", "Desmond",
        "Oluwaseun", "Alejandro", "Takeshi", "Vikram", "Bastian", "Seamus"
    ]

    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
        "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
        "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
        "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
        # Diverse additions
        "Kim", "Chen", "Park", "Patel", "Singh", "Kumar", "Ali", "Khan",
        "Hassan", "Okafor", "Mensah", "Diallo", "Rosario", "Santos", "Reyes",
        "Romero", "Nakamura", "Tanaka", "Yamamoto", "Ivanov", "Johansson",
        "Mueller", "Bianchi", "Dubois", "Osei", "Achebe", "Kowalski",
        "Petrov", "Andersen", "Fernandez", "Adeyemi", "Wakahisa", "Abubakar"
    ]

    def get_gender(part: str):
        """Return 'female', 'male', or None (random) based on voice part."""
        part_lower = part.lower()
        if any(p in part_lower for p in ['soprano', 'alto', 'mezzo']):
            return 'female'
        if any(p in part_lower for p in ['tenor', 'baritone', 'bass', 'bari']):
            return 'male'
        return None  # Unknown part — pick randomly

    def get_name(part: str) -> str:
        gender = get_gender(part)
        if gender == 'female':
            first = random.choice(female_names)
        elif gender == 'male':
            first = random.choice(male_names)
        else:
            first = random.choice(random.choice([female_names, male_names]))
        return f"{first} {random.choice(last_names)}"

    singers = []
    min_h, max_h = height_range

    if distribution:
        # Use specified distribution
        for part_idx, count in enumerate(distribution):
            part = parts[part_idx % len(parts)]
            for _ in range(count):
                name = get_name(part)
                base_height = random.uniform(min_h, max_h)
                height = round(base_height * 2) / 2
                singers.append(Singer(name=name, voice_part=part, height=height))
    else:
        # Even distribution with ±5 variation per part
        base = num_singers // len(parts)
        extra = num_singers % len(parts)
        counts = [base + (1 if i < extra else 0) for i in range(len(parts))]
        for i in range(len(counts)):
            counts[i] = max(1, counts[i] + random.randint(-5, 5))
        # Adjust total back to num_singers
        diff = num_singers - sum(counts)
        while diff != 0:
            i = random.randrange(len(counts))
            if diff > 0:
                counts[i] += 1
                diff -= 1
            elif diff < 0 and counts[i] > 1:
                counts[i] -= 1
                diff += 1

        for part, count in zip(parts, counts):
            for _ in range(count):
                name = get_name(part)
                base_height = random.uniform(min_h, max_h)
                height = round(base_height * 2) / 2
                singers.append(Singer(name=name, voice_part=part, height=height))

    return singers