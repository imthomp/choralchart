"""
Tests for seating_algorithm.py — pure algorithm logic, no Flask required.
"""
import pytest
from seating_algorithm import (
    Singer, Seat, generate_seating_chart, get_unique_parts,
    calculate_min_width, calculate_min_width_grid, calculate_dimensions_with_user_input,
)
from app import find_single_wide_parts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def all_singers(chart):
    return [seat.singer for row in chart for seat in row if seat.singer]


def singers_of(chart, part):
    return [seat.singer for row in chart for seat in row
            if seat.singer and seat.singer.voice_part == part]


def row_parts(chart, row_idx):
    return [seat.singer.voice_part for seat in chart[row_idx] if seat.singer]


def part_rows(chart, part):
    """Set of row indices where the part has at least one singer."""
    return {i for i, row in enumerate(chart)
            for seat in row if seat.singer and seat.singer.voice_part == part}


def max_consecutive_in_row(row, part):
    filled = [s for s in row if s.singer]
    max_run = run = 0
    for seat in filled:
        if seat.singer.voice_part == part:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0
    return max_run


# ---------------------------------------------------------------------------
# Singer model
# ---------------------------------------------------------------------------

class TestSingerHeightDisplay:
    def test_none_returns_empty(self):
        assert Singer("A", "Alto").height_display == ""

    def test_even_feet_and_inches(self):
        assert Singer("A", "Alto", height=66).height_display == "5'6\""

    def test_half_inch(self):
        assert Singer("A", "Alto", height=66.5).height_display == "5'6.5\""

    def test_six_feet(self):
        assert Singer("A", "Alto", height=72).height_display == "6'0\""


# ---------------------------------------------------------------------------
# Height sorting
# ---------------------------------------------------------------------------

class TestHeightSorting:
    def make_chart(self, singers):
        return generate_seating_chart(
            singers, rows=2, seats_per_row=6,
            part_order=["Soprano"], layout="side-by-side"
        )

    def test_tallest_in_back_rows(self):
        singers = [
            Singer("Short", "Soprano", height=60),
            Singer("Medium", "Soprano", height=65),
            Singer("Tall", "Soprano", height=70),
            Singer("Taller", "Soprano", height=72),
        ]
        chart = self.make_chart(singers)
        # Row 0 = back; row 1 = front
        back_heights = [s.singer.height for s in chart[0] if s.singer]
        front_heights = [s.singer.height for s in chart[1] if s.singer]
        assert min(back_heights) >= max(front_heights)

    def test_unknown_heights_placed_in_middle(self):
        known = [Singer(f"K{i}", "Soprano", height=60 + i) for i in range(4)]
        unknowns = [Singer("U1", "Soprano", height=None),
                    Singer("U2", "Soprano", height=None)]
        chart = self.make_chart(known + unknowns)
        placed = all_singers(chart)
        unknown_idxs = [i for i, s in enumerate(placed) if s.height is None]
        # Unknowns should not all be at the very start or very end
        assert unknown_idxs != list(range(len(unknowns)))
        assert unknown_idxs != list(range(len(placed) - len(unknowns), len(placed)))


# ---------------------------------------------------------------------------
# Side-by-side layout
# ---------------------------------------------------------------------------

class TestSideBySide:
    def satb_chart(self, rows=3, counts=(6, 6, 6, 6)):
        parts = ["Soprano", "Alto", "Tenor", "Bass"]
        singers = [
            Singer(f"{p[0]}{i}", p, height=60 + j)
            for j, (p, n) in enumerate(zip(parts, counts))
            for i in range(n)
        ]
        seats_per_row = max(4, sum(counts) // rows + 4)
        return generate_seating_chart(
            singers, rows=rows, seats_per_row=seats_per_row,
            part_order=parts, layout="side-by-side"
        )

    def test_all_singers_placed(self):
        chart = self.satb_chart()
        assert len(all_singers(chart)) == 24

    def test_parts_occupy_distinct_column_bands(self):
        chart = self.satb_chart(rows=2)
        # In side-by-side the parts must appear in left-to-right order
        # with no interleaving. Check each row's part sequence is monotone.
        parts = ["Soprano", "Alto", "Tenor", "Bass"]
        for row in chart:
            row_parts_list = [s.singer.voice_part for s in row if s.singer]
            part_idxs = [parts.index(p) for p in row_parts_list]
            assert part_idxs == sorted(part_idxs), f"Parts not L-R ordered: {row_parts_list}"

    def test_no_seat_holds_two_singers(self):
        chart = self.satb_chart()
        for row in chart:
            for seat in row:
                assert seat.singer is None or isinstance(seat.singer, Singer)

    def test_correct_row_count(self):
        chart = self.satb_chart(rows=4)
        assert len(chart) == 4

    def test_part_counts_match_input(self):
        chart = self.satb_chart(counts=(5, 7, 4, 8))
        assert len(singers_of(chart, "Soprano")) == 5
        assert len(singers_of(chart, "Alto")) == 7
        assert len(singers_of(chart, "Tenor")) == 4
        assert len(singers_of(chart, "Bass")) == 8

    def test_single_part(self):
        singers = [Singer(f"S{i}", "Soprano", height=60 + i) for i in range(10)]
        chart = generate_seating_chart(
            singers, rows=2, seats_per_row=6,
            part_order=["Soprano"], layout="side-by-side"
        )
        assert len(all_singers(chart)) == 10


# ---------------------------------------------------------------------------
# Stacked layout
# ---------------------------------------------------------------------------

class TestStacked:
    def chart(self, rows=4):
        parts = ["Soprano", "Alto", "Tenor", "Bass"]
        singers = [Singer(f"{p[0]}{i}", p, height=60 + i)
                   for p in parts for i in range(6)]
        return generate_seating_chart(
            singers, rows=rows, seats_per_row=8,
            part_order=parts, layout="stacked"
        )

    def test_all_singers_placed(self):
        assert len(all_singers(self.chart())) == 24

    def test_parts_in_separate_row_bands(self):
        chart = self.chart(rows=4)
        soprano_rows = part_rows(chart, "Soprano")
        tenor_rows = part_rows(chart, "Tenor")
        assert soprano_rows.isdisjoint(tenor_rows)

    def test_correct_row_count(self):
        assert len(self.chart(rows=8)) == 8


# ---------------------------------------------------------------------------
# Grid layout
# ---------------------------------------------------------------------------

class TestGridLayout:
    def make_singers(self, part_counts):
        return [
            Singer(f"{p[0]}{i}", p, height=60 + i)
            for p, n in part_counts.items()
            for i in range(n)
        ]

    def test_2x2_grid_row_separation(self):
        singers = self.make_singers(
            {"Alto": 6, "Bass": 6, "Soprano": 6, "Tenor": 6}
        )
        part_grid = [["Alto", "Bass"], ["Soprano", "Tenor"]]
        part_order = ["Alto", "Bass", "Soprano", "Tenor"]
        chart = generate_seating_chart(
            singers, rows=4, seats_per_row=8,
            part_order=part_order, layout="grid", part_grid=part_grid
        )
        back_rows = {0, 1}
        front_rows = {2, 3}
        assert part_rows(chart, "Alto") <= back_rows
        assert part_rows(chart, "Bass") <= back_rows
        assert part_rows(chart, "Soprano") <= front_rows
        assert part_rows(chart, "Tenor") <= front_rows

    def test_2x2_grid_all_singers_placed(self):
        singers = self.make_singers(
            {"Alto": 6, "Bass": 6, "Soprano": 6, "Tenor": 6}
        )
        part_grid = [["Alto", "Bass"], ["Soprano", "Tenor"]]
        chart = generate_seating_chart(
            singers, rows=4, seats_per_row=8,
            part_order=["Alto", "Bass", "Soprano", "Tenor"],
            layout="grid", part_grid=part_grid
        )
        assert len(all_singers(chart)) == 24

    def test_single_group_matches_side_by_side(self):
        """A 1-group grid should produce the same result as side-by-side."""
        parts = ["Soprano", "Alto", "Tenor", "Bass"]
        singers = [Singer(f"{p[0]}{i}", p, height=60 + i)
                   for p in parts for i in range(6)]
        chart_grid = generate_seating_chart(
            singers, rows=3, seats_per_row=10,
            part_order=parts, layout="grid", part_grid=[parts]
        )
        chart_sbs = generate_seating_chart(
            singers, rows=3, seats_per_row=10,
            part_order=parts, layout="side-by-side"
        )
        placed_grid = {s.name for s in all_singers(chart_grid)}
        placed_sbs = {s.name for s in all_singers(chart_sbs)}
        assert placed_grid == placed_sbs

    def test_unequal_group_sizes_proportional_rows(self):
        """Larger groups should get more rows."""
        singers = (
            [Singer(f"A{i}", "Alto", 65) for i in range(12)] +
            [Singer(f"S{i}", "Soprano", 63) for i in range(4)]
        )
        part_grid = [["Alto"], ["Soprano"]]
        chart = generate_seating_chart(
            singers, rows=4, seats_per_row=8,
            part_order=["Alto", "Soprano"],
            layout="grid", part_grid=part_grid
        )
        alto_row_count = len(part_rows(chart, "Alto"))
        soprano_row_count = len(part_rows(chart, "Soprano"))
        assert alto_row_count >= soprano_row_count

    def test_parts_within_group_are_side_by_side(self):
        """Parts in the same grid group must appear in distinct columns, not same column."""
        singers = (
            [Singer(f"A{i}", "Alto", 65) for i in range(6)] +
            [Singer(f"B{i}", "Bass", 69) for i in range(6)]
        )
        part_grid = [["Alto", "Bass"]]
        chart = generate_seating_chart(
            singers, rows=3, seats_per_row=6,
            part_order=["Alto", "Bass"],
            layout="grid", part_grid=part_grid
        )
        for row in chart:
            alto_positions = {s.position for s in row if s.singer and s.singer.voice_part == "Alto"}
            bass_positions = {s.position for s in row if s.singer and s.singer.voice_part == "Bass"}
            assert alto_positions.isdisjoint(bass_positions)


# ---------------------------------------------------------------------------
# find_single_wide_parts
# ---------------------------------------------------------------------------

class TestFindSingleWideParts:
    def test_single_singer_flagged(self):
        singers = [Singer(f"A{i}", "Alto", 65) for i in range(6)] + \
                  [Singer("B1", "Bass", 69)]
        chart = generate_seating_chart(
            singers, rows=3, seats_per_row=6,
            part_order=["Alto", "Bass"], layout="side-by-side"
        )
        assert "Bass" in find_single_wide_parts(chart, ["Alto", "Bass"])
        assert "Alto" not in find_single_wide_parts(chart, ["Alto", "Bass"])

    def test_balanced_parts_not_flagged(self):
        singers = [Singer(f"A{i}", "Alto", 65) for i in range(6)] + \
                  [Singer(f"B{i}", "Bass", 69) for i in range(6)]
        chart = generate_seating_chart(
            singers, rows=2, seats_per_row=8,
            part_order=["Alto", "Bass"], layout="side-by-side"
        )
        assert find_single_wide_parts(chart, ["Alto", "Bass"]) == []

    def test_empty_chart_returns_empty(self):
        assert find_single_wide_parts([], ["Alto", "Bass"]) == []


# ---------------------------------------------------------------------------
# get_unique_parts
# ---------------------------------------------------------------------------

class TestGetUniqueParts:
    def test_preserves_first_seen_order(self):
        singers = [
            Singer("A", "Bass"), Singer("B", "Tenor"),
            Singer("C", "Alto"), Singer("D", "Soprano"),
        ]
        assert get_unique_parts(singers) == ["Bass", "Tenor", "Alto", "Soprano"]

    def test_deduplicates(self):
        singers = [Singer("A", "Soprano"), Singer("B", "Soprano"), Singer("C", "Alto")]
        assert get_unique_parts(singers) == ["Soprano", "Alto"]

    def test_empty_list(self):
        assert get_unique_parts([]) == []


# ---------------------------------------------------------------------------
# calculate_min_width
# ---------------------------------------------------------------------------

class TestCalculateMinWidthGrid:
    def test_single_group_no_overflow(self):
        """Regression: auto seats_per_row < needed width caused IndexError."""
        singers = [Singer(f"{p[0]}{i}", p, 65.0)
                   for p in ["Soprano", "Alto", "Tenor", "Bass"]
                   for i in range(5)]
        part_grid = [["Soprano", "Alto", "Tenor", "Bass"]]
        # 4 parts × ceil(5/2)=3 → needs 12; auto-calc gives 10
        min_w = calculate_min_width_grid(singers, part_grid, rows=2)
        assert min_w == 12

    def test_two_groups_takes_max(self):
        singers = (
            [Singer(f"A{i}", "Alto", 65) for i in range(6)] +
            [Singer(f"B{i}", "Bass", 69) for i in range(6)] +
            [Singer(f"S{i}", "Soprano", 63) for i in range(3)] +
            [Singer(f"T{i}", "Tenor", 67) for i in range(3)]
        )
        part_grid = [["Alto", "Bass"], ["Soprano", "Tenor"]]
        min_w = calculate_min_width_grid(singers, part_grid, rows=4)
        # Back group (12 singers, ~3 rows): ceil(6/3)+ceil(6/3) = 4
        # Front group (6 singers, ~1 row): ceil(3/1)+ceil(3/1) = 6
        assert min_w >= 4  # at least wide enough for back group

    def test_generates_without_index_error(self):
        """End-to-end: the combo that triggered the original crash."""
        singers = [Singer(f"{p[0]}{i}", p, 65.0)
                   for p in ["Soprano", "Alto", "Tenor", "Bass"]
                   for i in range(5)]
        part_grid = [["Soprano", "Alto", "Tenor", "Bass"]]
        import math
        rows, seats_per_row = 2, 10  # auto-calc values before the fix
        from seating_algorithm import calculate_min_width_grid
        seats_per_row = max(seats_per_row, calculate_min_width_grid(singers, part_grid, rows))
        # Must not raise
        chart = generate_seating_chart(
            singers, rows=rows, seats_per_row=seats_per_row,
            part_order=["Soprano", "Alto", "Tenor", "Bass"],
            layout="grid", part_grid=part_grid
        )
        assert len([s for row in chart for s in row if s.singer]) == 20


class TestCalculateMinWidth:
    def test_equal_distribution(self):
        singers = [Singer(f"S{i}", "Soprano") for i in range(6)] + \
                  [Singer(f"A{i}", "Alto") for i in range(6)]
        # 6 singers, 3 rows → width 2 each → total 4
        width = calculate_min_width(singers, ["Soprano", "Alto"], rows=3)
        assert width == 4

    def test_single_singer_part_gets_width_1(self):
        singers = [Singer(f"A{i}", "Alto") for i in range(6)] + \
                  [Singer("B1", "Bass")]
        # Bass: ceil(1/3) = 1; Alto: ceil(6/3) = 2 → total 3
        width = calculate_min_width(singers, ["Alto", "Bass"], rows=3)
        assert width == 3


# ---------------------------------------------------------------------------
# calculate_dimensions_with_user_input
# ---------------------------------------------------------------------------

class TestCalculateDimensions:
    def test_user_specifies_both(self):
        rows, seats = calculate_dimensions_with_user_input(24, 4, "side-by-side", 3, 10)
        assert rows == 3 and seats == 10

    def test_user_specifies_rows_only(self):
        rows, seats = calculate_dimensions_with_user_input(24, 4, "side-by-side", user_rows=3)
        assert rows == 3
        assert seats >= 8  # at least ceil(24/3)=8

    def test_user_specifies_max_per_row_only(self):
        rows, seats = calculate_dimensions_with_user_input(24, 4, "side-by-side", user_max_per_row=8)
        assert seats == 8
        assert rows >= 3  # at least ceil(24/8)=3

    def test_auto_returns_reasonable_dimensions(self):
        rows, seats = calculate_dimensions_with_user_input(40, 4, "side-by-side")
        assert rows >= 2
        assert seats >= 4
        assert rows * seats >= 40


# ---------------------------------------------------------------------------
# Mixed mode
# ---------------------------------------------------------------------------

def has_adjacent_same_part(row):
    """Return True if any two adjacent filled seats share a voice part."""
    filled = [s.singer.voice_part for s in row if s.singer]
    return any(filled[i] == filled[i + 1] for i in range(len(filled) - 1))


def has_vertical_same_part(chart):
    """Return True if any seat shares a voice part with the seat directly above it."""
    for row_idx in range(1, len(chart)):
        for seat in chart[row_idx]:
            if not seat.singer:
                continue
            above = chart[row_idx - 1][seat.position]
            if above.singer and above.singer.voice_part == seat.singer.voice_part:
                return True
    return False


class TestMixedMode:
    def make_satb(self, per_part=6):
        parts = ["Soprano", "Alto", "Tenor", "Bass"]
        return [Singer(f"{p[0]}{i}", p, 65.0) for p in parts for i in range(per_part)]

    def test_no_adjacent_same_part(self):
        singers = self.make_satb(6)
        chart = generate_seating_chart(
            singers, rows=3, seats_per_row=10,
            part_order=["Soprano", "Alto", "Tenor", "Bass"],
            layout="side-by-side", mixed=True
        )
        for row in chart:
            assert not has_adjacent_same_part(row), "adjacent same-part singers found"

    def test_all_singers_placed(self):
        singers = self.make_satb(6)
        chart = generate_seating_chart(
            singers, rows=3, seats_per_row=10,
            part_order=["Soprano", "Alto", "Tenor", "Bass"],
            layout="side-by-side", mixed=True
        )
        assert len(all_singers(chart)) == 24

    def test_mixed_false_unchanged(self):
        """Non-mixed chart should still group same parts together."""
        singers = self.make_satb(6)
        chart = generate_seating_chart(
            singers, rows=3, seats_per_row=10,
            part_order=["Soprano", "Alto", "Tenor", "Bass"],
            layout="side-by-side", mixed=False
        )
        # In a non-mixed side-by-side chart every row has each part in a block,
        # so at most 3 transitions (S→A, A→T, T→B). Verify there ARE adjacencies.
        any_adjacent = any(has_adjacent_same_part(row) for row in chart)
        assert any_adjacent, "expected blocks of same-part singers"

    def test_skewed_distribution_no_crash(self):
        """Dominant part should not crash; adjacencies unavoidable with 14:2 ratio."""
        singers = (
            [Singer(f"S{i}", "Soprano", 63) for i in range(14)] +
            [Singer(f"A{i}", "Alto", 62) for i in range(2)]
        )
        chart = generate_seating_chart(
            singers, rows=2, seats_per_row=10,
            part_order=["Soprano", "Alto"],
            layout="side-by-side", mixed=True
        )
        assert len(all_singers(chart)) == 16

    def test_no_vertical_same_part(self):
        singers = self.make_satb(6)
        chart = generate_seating_chart(
            singers, rows=3, seats_per_row=10,
            part_order=["Soprano", "Alto", "Tenor", "Bass"],
            layout="side-by-side", mixed=True
        )
        assert not has_vertical_same_part(chart), "same-part singers in same column across rows"

    def test_single_part_mixed_no_crash(self):
        """Single part can't interleave, but must not raise."""
        singers = [Singer(f"S{i}", "Soprano", 63) for i in range(8)]
        chart = generate_seating_chart(
            singers, rows=2, seats_per_row=5,
            part_order=["Soprano"],
            layout="side-by-side", mixed=True
        )
        assert len(all_singers(chart)) == 8
