import sqlite3
from output_class import Output

class Output_DB(Output):
    def __init__(self):
        # Conectare la baza de date SQLite
        self.conn = sqlite3.connect('orar.db') 
        self.cur = self.conn.cursor()

# Funcție pentru inserarea datelor în tabelul Curs
    def output_curs(self, acoperite_entries):
        for entry in acoperite_entries:
            self.cur.execute('''
                INSERT INTO Curs (nume, seminar, cursOre, labOre)
                VALUES (?, ?, ?, ?)
            ''', (entry['name'], entry['seminar'], entry['totalOreCurs'], entry['totalOreSeminar']))
        self.conn.commit()

# Funcție pentru inserarea datelor în tabelul Specializare
    def output_specializare(self, formation_entries):
        for entry in formation_entries:
            self.cur.execute('''
                INSERT INTO Specializare (nume, an, tip, numarGrupe, numarSubgrupe)
                VALUES (?, ?, ?, ?, ?)
            ''', (entry['specialization'], entry['year'], entry['type'], entry['grupe'], entry['subgrupe']))
        self.conn.commit()

# Funcție pentru inserarea datelor în tabelul Grupa
    def output_grupa(self, formation_entries):
        for entry in formation_entries:
            self.cur.execute('SELECT specNumber FROM Specializare WHERE nume = ?', (entry['specialization'],))
            specializare_id = self.cur.fetchone()[0]
            for i in range(entry['grupe']):
                grupa_name = f'grupa{i + 1}'
                self.cur.execute('''
                    INSERT INTO Grupa (specNumber, nume)
                    VALUES (?, ?)
                ''', (specializare_id, grupa_name))
        self.conn.commit()

# Funcție pentru inserarea datelor în tabelul Sala
    def output_sala(self, sali_entries):
        for entry in sali_entries:
            self.cur.execute('''
                INSERT INTO Sala (nume, capacitate)
                VALUES (?, ?)
            ''', (entry['nume'], entry['capacitate']))
        self.conn.commit()

# Funcție pentru inserarea datelor în tabelul Profesor
    def output_profesor(self, state_entries):
        for entry in state_entries:
            self.cur.execute('''
                INSERT INTO Profesor (nume, pozitie)
                VALUES (?, ?)
            ''', (entry['name'], entry['position']))
        self.conn.commit()
            
# Funcție pentru inserarea datelor în tabelul Subgrupa
    def output_subgrupa(self, formation_entries):
        for entry in formation_entries:
            self.cur.execute('SELECT specNumber FROM Specializare WHERE nume = ?', (entry['specialization'],))
            specializare_id = self.cur.fetchone()[0]
            self.cur.execute('SELECT grupaNumber FROM Grupa WHERE specNumber = ?', (specializare_id,))
            grupaNumbers = self.cur.fetchall()
            subgrupe_per_grupa = entry['subgrupe'] // entry['grupe']
            remainder = entry['subgrupe'] % entry['grupe']
            subgrupa_counter = 1
            for idx, grupaNumber in enumerate(grupaNumbers):
                subgrupe_in_this_grupa = subgrupe_per_grupa + (1 if idx < remainder else 0)
                for _ in range(subgrupe_in_this_grupa):
                    subgrupa_name = f'subgrupa{subgrupa_counter}'
                    self.cur.execute('''
                        INSERT INTO Subgrupa (grupaNumber, nume)
                        VALUES (?, ?)
                    ''', (grupaNumber[0], subgrupa_name))
                    subgrupa_counter += 1
        self.conn.commit()

# Funcție pentru inserarea datelor în tabelul Event
    def output_event(self, acoperire_events):
        # Construim mapări pentru cursuri și profesori
        self.cur.execute('SELECT cursID, nume FROM Curs')
        cursuri = {row[1]: row[0] for row in self.cur.fetchall()}

        self.cur.execute('SELECT profesorID, nume FROM Profesor')
        profesori = {row[1]: row[0] for row in self.cur.fetchall()}
        # Parsăm fișierele AcoperireSem1 și AcoperireSem2
        for row in acoperire_events:
            curs_id = cursuri.get(row['Disciplina'])
            profesor_id = profesori.get(row['Cadru didactic'])
            tip = 'laborator' if row['Sem'] == 0 else 'curs'

            if curs_id and profesor_id:
                self.cur.execute('''
                    INSERT INTO Event (cursID, profesorID, tip)
                    VALUES (?, ?, ?)
                ''', (curs_id, profesor_id, tip))
        self.conn.commit()

    def output_event_participant(self, acoperire_events):
        # Construim mapări pentru cursuri și profesori
        self.cur.execute('SELECT cursID, nume FROM Curs')
        cursuri = {row[1]: row[0] for row in self.cur.fetchall()}

        self.cur.execute('SELECT profesorID, nume FROM Profesor')
        profesori = {row[1]: row[0] for row in self.cur.fetchall()}

        # Construim mapări pentru eventID pe baza cursID și profesorID
        self.cur.execute('SELECT eventID, cursID, profesorID FROM Event')
        events = self.cur.fetchall()
        event_map = {(row[1], row[2]): row[0] for row in events}

        # Construim mapări pentru specializări
        self.cur.execute('SELECT specNumber, nume FROM Specializare')
        specializari = {row[1]: row[0] for row in self.cur.fetchall()}

        # Construim mapări pentru grupe și subgrupe
        self.cur.execute('SELECT grupaNumber, specNumber FROM Grupa')
        grupe = self.cur.fetchall()

        self.cur.execute('SELECT subgrupaNumber, grupaNumber FROM Subgrupa')
        subgrupe = self.cur.fetchall()

        def get_grupe_and_subgrupe(spec_id):
            grupe_ids = [grupa[0] for grupa in grupe if grupa[1] == spec_id]
            subgrupe_ids = [subgrupa[0] for subgrupa in subgrupe if subgrupa[1] in grupe_ids]
            return subgrupe_ids

            
        for row in acoperire_events:
            curs_id = cursuri.get(row['Disciplina'])
            profesor_id = profesori.get(row['Cadru didactic'])
            spec_id = specializari.get(row['Specializarea'])

            if curs_id and profesor_id and spec_id:
                event_id = event_map.get((curs_id, profesor_id))
                subgrupe_ids = get_grupe_and_subgrupe(spec_id)
                for subgrupa_id in subgrupe_ids:
                    self.cur.execute('''
                        INSERT INTO eventParticipant (eventID, subgrupaNumar)
                        VALUES (?, ?)
                    ''', (event_id, subgrupa_id))
        self.conn.commit()

# Închidem conexiunea la baza de date
    def __del__(self):
        self.conn.close()
