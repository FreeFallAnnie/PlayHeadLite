import csv

def load_XMarks(csv_path):
    palette = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            palette[int(row['ID'])] = {
                'prompt': row['Prompt'],
                'color': row['Color'].upper()
            }
    return palette

def get_Sparkle(palette, husky_id):
    return palette.get(husky_id, {'prompt': "Describe this.", 'color': "BLUE"}).values()
