"""
Generate sample CSV rosters with various configurations.
Run from the repo root: python tests/generate_sample_rosters.py
Output goes to static/samples/.
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from seating_algorithm import generate_random_roster

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'samples')


def save_roster(singers, filename):
    path = os.path.join(OUT_DIR, filename)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'voice_part', 'height'])
        writer.writeheader()
        for s in singers:
            writer.writerow({'name': s.name, 'voice_part': s.voice_part, 'height': s.height})
    print(f"Created {filename} with {len(singers)} singers")


if __name__ == '__main__':
    singers = generate_random_roster(50, ['Soprano', 'Alto', 'Tenor', 'Bass'], distribution=[15, 18, 8, 9])
    save_roster(singers, 'test_unequal_50.csv')

    singers = generate_random_roster(25, ['Soprano', 'Alto', 'Tenor', 'Bass'], distribution=[10, 8, 4, 3])
    save_roster(singers, 'test_unequal_25.csv')

    singers = generate_random_roster(120, ['Soprano 1', 'Soprano 2', 'Alto 1', 'Alto 2', 'Tenor', 'Bass'], distribution=[25, 22, 28, 20, 12, 13])
    save_roster(singers, 'test_split_parts_120.csv')

    singers = generate_random_roster(47, ['Soprano', 'Alto', 'Tenor', 'Bass'], distribution=[14, 16, 9, 8])
    save_roster(singers, 'test_prime_47.csv')

    singers = generate_random_roster(18, ['High', 'Middle', 'Low'], distribution=[7, 6, 5])
    save_roster(singers, 'test_3parts_18.csv')

    singers = generate_random_roster(210, ['Soprano 1', 'Soprano 2', 'Alto 1', 'Alto 2', 'Tenor 1', 'Tenor 2', 'Bass 1', 'Bass 2'], distribution=[30, 28, 32, 26, 22, 20, 28, 24])
    save_roster(singers, 'test_large_210.csv')

    singers = generate_random_roster(201, ['Tenor 1', 'Tenor 2', 'Baritone', 'Bass'], distribution=[35, 45, 55, 66])
    save_roster(singers, 'test_mens_chorus.csv')

    print("\nAll sample rosters generated!")
