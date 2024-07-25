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

# Funcție pentru inserarea datelor în tabelul Specializare
def insert_into_specializare(entries):
    for entry in entries:
        cur.execute('''
            INSERT INTO Specializare (nume, an, tip, numarGrupe, numarSubgrupe)
            VALUES (?, ?, ?, ?, ?)
        ''', (entry['specialization'], entry['year'], entry['type'], entry['grupe'], entry['subgrupe']))
    conn.commit()

# Funcție pentru inserarea datelor în tabelul Curs
def insert_into_curs(entries):
    for entry in entries:
        cur.execute('''
            INSERT INTO Curs (nume, seminar, cursOre, labOre)
            VALUES (?, ?, ?, ?)
        ''', (entry['name'], entry['seminar'], entry['totalOreCurs'], entry['totalOreSeminar']))
    conn.commit()

# Funcție pentru inserarea datelor în tabelul Grupa
def insert_into_grupa(entries):
    for entry in entries:
        cur.execute('SELECT specNumber FROM Specializare WHERE nume = ?', (entry['specialization'],))
        specNumber = cur.fetchone()[0]
        for i in range(entry['grupe']):
            grupa_name = f'grupa{i + 1}'
            cur.execute('''
                INSERT INTO Grupa (specNumber, nume)
                VALUES (?, ?)
            ''', (specNumber, grupa_name))
    conn.commit()

# Parsăm și inserăm datele în baza de date
formation_entries = parse_formation(file_paths[2])
acoperite_entries = parse_acoperite(file_paths[3])

insert_into_specializare(formation_entries)
insert_into_curs(acoperite_entries)
insert_into_grupa(formation_entries)

# Închidem conexiunea la baza de date
conn.close()
