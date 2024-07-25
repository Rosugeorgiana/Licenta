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

# Funcție pentru parsarea fișierului State_2021.xlsx
def parse_state(file_path):
    excel_data = pd.read_excel(file_path, sheet_name=None)  # Citim toate foile
    state_entries = []

    if "Anii de studiu Seria / nr. gr." in excel_data:
        df_state = excel_data["Anii de studiu Seria / nr. gr."]
        df_state_clean = df_state.dropna(subset=['Denumirea postului', 'Numele şi prenumele'])  # Eliminăm rândurile fără denumirea postului și nume
        
        for _, row in df_state_clean.iterrows():
            if row['Numele şi prenumele'].strip().lower() != 'vacant':
                tip = 'curs'
                if 'gr' in row['Anii de studiu Seria / nr. gr.'].lower():
                    tip = 'seminar'
                if 'sgr' in row['Anii de studiu Seria / nr. gr.'].lower():
                    tip = 'laborator'
                
                teacher_entry = {
                    'name': row['Numele şi prenumele'],
                    'position': row['Denumirea postului'],
                    'discipline': row['Disciplina'] if 'Disciplina' in row else None,
                    'specialization': row['Specializarea'] if 'Specializarea' in row else None,
                    'tip': tip
                }
                state_entries.append(teacher_entry)
    return state_entries

# Funcție pentru parsarea fișierelor AcoperireSem1 și AcoperireSem2
def parse_acoperire(file_path):
    df = pd.read_excel(file_path)
    df = df.dropna(subset=['Disciplina']).reset_index(drop=True)
    
    acoperire_entries = []

    for _, row in df.iterrows():
        acoperire_entry = {
            'discipline': row['Disciplina'],
            'professor': row['Cadru didactic'],
            'specialization': row['Specializarea'] if 'Specializarea' in row else None
        }
        acoperire_entries.append(acoperire_entry)
    
    return acoperire_entries

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

# Funcție pentru inserarea datelor în tabelul Grupa
def insert_into_grupa(entries):
    for entry in entries:
        cur.execute('SELECT specNumber FROM Specializare WHERE nume = ?', (entry['specialization'],))
        specializare_id = cur.fetchone()[0]
        for i in range(entry['grupe']):
            grupa_name = f'grupa{i + 1}'
            cur.execute('''
                INSERT INTO Grupa (specNumber, nume)
                VALUES (?, ?)
            ''', (specializare_id, grupa_name))
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

# Funcție pentru inserarea datelor în tabelul Event
def insert_into_event():
    # Construim mapări pentru cursuri și profesori
    cur.execute('SELECT cursID, nume FROM Curs')
    cursuri = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute('SELECT profesorID, nume FROM Profesor')
    profesori = {row[1]: row[0] for row in cur.fetchall()}

    # Parsăm fișierele AcoperireSem1 și AcoperireSem2
    for file_path in [file_paths[0], file_paths[1]]:
        df = pd.read_excel(file_path)
        df = df.dropna(subset=['Disciplina']).reset_index(drop=True)
        
        for _, row in df.iterrows():
            curs_id = cursuri.get(row['Disciplina'])
            profesor_id = profesori.get(row['Cadru didactic'])
            tip = 'laborator' if row['Seminar'] == 0 else 'curs'

            if curs_id and profesor_id:
                cur.execute('''
                    INSERT INTO Event (cursID, profesorID, tip)
                    VALUES (?, ?, ?)
                ''', (curs_id, profesor_id, tip))

    # Parsăm fișierul State_2021.xlsx
    state_entries = parse_state(file_paths[4])

    for entry in state_entries:
        curs_id = cursuri.get(entry['discipline'])
        profesor_id = profesori.get(entry['name'])

        if curs_id and profesor_id:
            cur.execute('''
                INSERT INTO Event (cursID, profesorID, tip)
                VALUES (?, ?, ?)
            ''', (curs_id, profesor_id, entry['tip']))

    conn.commit()

# Funcție pentru inserarea datelor în tabelul eventParticipant
def insert_into_event_participant():
    # Construim mapări pentru cursuri și profesori
    cur.execute('SELECT cursID, nume FROM Curs')
    cursuri = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute('SELECT profesorID, nume FROM Profesor')
    profesori = {row[1]: row[0] for row in cur.fetchall()}

    # Construim mapări pentru eventID pe baza cursID și profesorID
    cur.execute('SELECT eventID, cursID, profesorID FROM Event')
    events = cur.fetchall()
    event_map = {(row[1], row[2]): row[0] for row in events}

    # Construim mapări pentru specializări
    cur.execute('SELECT specNumber, nume FROM Specializare')
    specializari = {row[1]: row[0] for row in cur.fetchall()}

    # Construim mapări pentru grupe și subgrupe
    cur.execute('SELECT grupaNumber, specNumber FROM Grupa')
    grupe = cur.fetchall()

    cur.execute('SELECT subgrupaNumber, grupaNumber FROM Subgrupa')
    subgrupe = cur.fetchall()

    def get_grupe_and_subgrupe(spec_id):
        grupe_ids = [grupa[0] for grupa in grupe if grupa[1] == spec_id]
        subgrupe_ids = [subgrupa[0] for subgrupa in subgrupe if subgrupa[1] in grupe_ids]
        return subgrupe_ids

    # Parsăm fișierele AcoperireSem1 și AcoperireSem2
    for file_path in [file_paths[0], file_paths[1]]:
        df = pd.read_excel(file_path)
        df = df.dropna(subset=['Disciplina']).reset_index(drop=True)
        
        for _, row in df.iterrows():
            curs_id = cursuri.get(row['Disciplina'])
            profesor_id = profesori.get(row['Cadru didactic'])
            spec_id = specializari.get(row['Specializarea'])

            if curs_id and profesor_id and spec_id:
                event_id = event_map.get((curs_id, profesor_id))
                subgrupe_ids = get_grupe_and_subgrupe(spec_id)
                for subgrupa_id in subgrupe_ids:
                    cur.execute('''
                        INSERT INTO eventParticipant (eventID, subgrupaNumar)
                        VALUES (?, ?)
                    ''', (event_id, subgrupa_id))

    # Parsăm fișierul State_2021.xlsx
    state_entries = parse_state(file_paths[4])

    for entry in state_entries:
        curs_id = cursuri.get(entry['discipline'])
        profesor_id = profesori.get(entry['name'])
        spec_id = specializari.get(entry['specialization'])

        if curs_id and profesor_id and spec_id:
            event_id = event_map.get((curs_id, profesor_id))
            subgrupe_ids = get_grupe_and_subgrupe(spec_id)
            for subgrupa_id in subgrupe_ids:
                cur.execute('''
                    INSERT INTO eventParticipant (eventID, subgrupaNumar)
                    VALUES (?, ?)
                ''', (event_id, subgrupa_id))

    conn.commit()

# Parsăm și inserăm datele în baza de date
formation_entries = parse_formation(file_paths[2])
state_entries = parse_state(file_paths[4])
acoperire_entries = parse_acoperire(file_paths[0]) + parse_acoperire(file_paths[1])
sali_entries = parse_sali(file_paths[5])

insert_into_specializare(formation_entries)
insert_into_grupa(formation_entries)
insert_into_sala(sali_entries)
insert_into_profesor(state_entries)
insert_into_subgrupa(formation_entries)
insert_into_event()
insert_into_event_participant()

# Închidem conexiunea la baza de date
conn.close()
