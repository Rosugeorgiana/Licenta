import pandas as pd
import sqlite3

# Conectare la baza de date SQLite
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
    data = pd.read_excel(file_path)
    data.dropna(how='all', inplace=True)
    data.columns = data.columns.str.strip()
    data = data.dropna(subset=['Specializare'])

    def create_dict(row):
        return {
            'specialization': row['Specializare'],
            'year': row['An'],
            'type': row['Nr. total'],
            'grupe': row['Grupe'],
            'subgrupe': row['Subgrupe']
        }

    formation_entries = [create_dict(row) for _, row in data.iterrows()]
    return formation_entries

# Funcție pentru parsarea fișierului Recap.xlsx
def parse_acoperite(file_path):
    df = pd.read_excel(file_path)
    df = df.dropna(subset=['Denumirea disciplinei']).reset_index(drop=True)
    
    sem1_curs_col = df.columns[11]
    sem2_curs_col = df.columns[17]
    sem1_sem_col = df.columns[12]
    sem2_sem_col = df.columns[18]
    sem1_lab_col = df.columns[13]
    sem2_lab_col = df.columns[19]

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

# Funcție pentru inserarea datelor în tabelul Specializare
def insert_into_specializare(entries):
    for entry in entries:
        cur.execute('''
            INSERT INTO Specializare (nume, an, tip, numarGrupe, numarSubgrupe)
            VALUES (?, ?, ?, ?, ?)
        ''', (entry['specialization'], entry['year'], entry['type'], entry['grupe'], entry['subgrupe']))
    conn.commit()

# Funcție pentru inserarea datelor în tabelul Sala
def insert_into_sala(entries):
    for entry in entries:
        cur.execute('''
            INSERT INTO Sala (nume, capacitate)
            VALUES (?, ?)
        ''', (entry['nume'], entry['capacitate']))
    conn.commit()

# Funcție pentru inserarea datelor în tabelul Profesor
def insert_into_profesor(entries):
    for entry in entries:
        cur.execute('''
            INSERT INTO Profesor (nume, pozitie)
            VALUES (?, ?)
        ''', (entry['name'], entry['position']))
    conn.commit()

# Funcție pentru inserarea datelor în tabelul Subgrupa
def insert_into_subgrupa(entries):
    for entry in entries:
        cur.execute('SELECT specNumber FROM Specializare WHERE nume = ?', (entry['specialization'],))
        specializare_id = cur.fetchone()[0]
        cur.execute('SELECT grupaNumber FROM Grupa WHERE specNumber = ?', (specializare_id,))
        grupaNumbers = cur.fetchall()
        subgrupe_per_grupa = entry['subgrupe'] // entry['grupe']
        remainder = entry['subgrupe'] % entry['grupe']
        subgrupa_counter = 1
        for idx, grupaNumber in enumerate(grupaNumbers):
            subgrupe_in_this_grupa = subgrupe_per_grupa + (1 if idx < remainder else 0)
            for _ in range(subgrupe_in_this_grupa):
                subgrupa_name = f'subgrupa{subgrupa_counter}'
                cur.execute('''
                    INSERT INTO Subgrupa (grupaNumber, nume)
                    VALUES (?, ?)
                ''', (grupaNumber[0], subgrupa_name))
                subgrupa_counter += 1
    conn.commit()

# Parsăm și inserăm datele în baza de date
formation_entries = parse_formation(file_paths[2])
acoperite_entries = parse_acoperite(file_paths[3])
state_entries = parse_state(file_paths[4])
sali_entries = parse_sali(file_paths[5])

insert_into_sala(sali_entries)
insert_into_profesor(state_entries)
insert_into_subgrupa(formation_entries)

# ÎnchnumarSubgrupeem conexiunea la baza de date
conn.close()