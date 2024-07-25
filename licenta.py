import pandas as pd
import sqlite3
conn = sqlite3.connect('orar.db')
cur = conn.cursor()

# Definim calea fișierelor Excel
file_paths = [
    'C:\\Users\\tedy\\Desktop\\AcoperireSem1.xlsx',
    'C:\\Users\\tedy\\Desktop\\AcoperireSem2.xlsx',
    'C:\\Users\\tedy\\Desktop\\Formatii.xlsx',
    'C:\\Users\\tedy\\Desktop\\Recap.xlsx',
    'C:\\Users\\tedy\\Desktop\\State_2021.xlsx',
    'C:\\Users\\tedy\\Desktop\\Sali.xlsx'
]

# Funcție pentru parsarea fișierului Formatii.xlsx
def parse_formation(file_path):
    # Citim datele din fișierul Excel
    data = pd.read_excel(file_path)

    # Eliminăm rândurile complet goale
    data.dropna(how='all', inplace=True)

    # Eliminăm spațiile albe din capetele coloanelor
    data.columns = data.columns.str.strip()

    # Eliminăm rândurile unde 'Specializare' este NaN
    data = data.dropna(subset=['Specializare'])

    # Funcție pentru crearea unui dicționar dintr-un rând
    def create_dict(row):
        return {
            'specialization': row['Specializare'],
            'year': row['An'],
            'type': row['Nr. total'],
            'grupe': row['Grupe'],
            'subgrupe': row['Subgrupe']
        }

    # Creăm dicționare pentru fiecare rând și le stocăm într-o listă
    formation_entries = [create_dict(row) for _, row in data.iterrows()]

    return formation_entries

# Parsăm fișierul de formații și afișăm datele procesate pentru inspecție
formation_entries = parse_formation(file_paths[2])
print("Formation Entries:", formation_entries)

# Funcție pentru parsarea fișierului Recap.xlsx
def parse_acoperite(file_path):
    df = pd.read_excel(file_path)
    df = df.dropna(subset=['Denumirea disciplinei']).reset_index(drop=True)  # Eliminăm rândurile fără denumirea disciplinei

    # Identificăm coloanele relevante
    sem1_curs_col = df.columns[11]
    sem2_curs_col = df.columns[17]
    sem1_sem_col = df.columns[12]
    sem2_sem_col = df.columns[18]
    sem1_lab_col = df.columns[13]
    sem2_lab_col = df.columns[19]

    # Funcție pentru crearea unei intrări de profesor
    def create_teacher_entry(row):
        total_ore_curs = row[sem1_curs_col] if not pd.isna(row[sem1_curs_col]) else (
            row[sem2_curs_col] if not pd.isna(row[sem2_curs_col]) else 0)
        if not pd.isna(row[sem1_sem_col]):
            total_ore_sem = row[sem1_sem_col]
        elif not pd.isna(row[sem2_sem_col]):
            total_ore_sem = row[sem2_sem_col]
        elif not pd.isna(row[sem1_lab_col]):
            total_ore_sem = row[sem1_lab_col]
        elif not pd.isna(row[sem2_lab_col]):
            total_ore_sem = row[sem2_lab_col]
        else:
            total_ore_sem = 0
        return {
            'name': row['Denumirea disciplinei'],
            'seminar': True if row['Unnamed: 25'] == 1 else False,
            'totalOreCurs': total_ore_curs,
            'totalOreSeminar': total_ore_sem,
        }

    return df.apply(create_teacher_entry, axis=1).tolist()

# Funcție pentru parsarea fișierului State_2021.xlsx
def parse_state(file_path):
    excel_data = pd.read_excel(file_path)
    excel_data_clean = excel_data.dropna(subset=['Denumirea postului', 'Numele şi prenumele'])  # Eliminăm rândurile fără denumirea postului și nume

    state_entries = []

    for _, row in excel_data_clean.iterrows():
        if row['Numele şi prenumele'].strip().lower() != 'vacant':
            teacher_entry = {
                'name': row['Numele şi prenumele'],
                'position': row['Denumirea postului'],
                'firstname': row['Numele şi prenumele'].split()[0] if len(row['Numele şi prenumele'].split()) > 1 else '',
                'phone': '0000000000'  # Număr de telefon fictiv
            }
            state_entries.append(teacher_entry)
    
    return state_entries

# Funcție pentru parsarea fișierului Sali.xlsx
def parse_sali(file_path):
    df = pd.read_excel(file_path)
    df.dropna(how='all', inplace=True)  # Eliminăm rândurile complet goale
    df.columns = df.columns.str.strip()  # Eliminăm spațiile albe din capetele coloanelor

    sali_entries = []

    for _, row in df.iterrows():
        room_entry = {
            'nume': row['Sali'],
            'capacitate': row['Capacitate']
        }
        sali_entries.append(room_entry)
    
    return sali_entries

# Parsăm fișierul de formații
formation_entries = parse_formation(file_paths[2])
# Parsăm fișierul de recapitulare
acoperite_entries = parse_acoperite(file_paths[3])
# Parsăm fișierul de state
state_entries = parse_state(file_paths[4])
# Parsăm fișierul de săli
sali_entries = parse_sali(file_paths[5])

# Afișăm datele procesate pentru inspecție
print("Formation Entries:", formation_entries)
print("Acoperite Entries:", acoperite_entries)
print("State Entries:", state_entries)
print("Sali Entries:", sali_entries)
