
from output_class import Output

class Output_TXT(Output):
    def __init__(self):
        pass
    def output_curs(self, acoperite_entries):
        print('-------------------------MATERII----------------------------:')
        for entry in acoperite_entries:
            print(entry['name'])
    def output_specializare(self, formation_entries):
        print('-------------------------SPECIALIZARI----------------------------:')
        for entry in formation_entries:
            print(entry['specialization'], entry['year'])
    def output_grupa(self, formation_entries):
        pass
    def output_sala(self, sali_entries):
        print('-------------------------SALI----------------------------:')
        for entry in sali_entries:
            print(entry['nume'],'capacitate',entry['capacitate'])
        pass
    def output_profesor(self, state_entries):
        print('-------------------------PROFESORI----------------------------:')
        for entry in state_entries:
            print(entry['position'],entry['name'],entry['firstname'])
        pass
    def output_subgrupa(self, formation_entries):
        pass
    def output_event(self, acoperire_events):
        pass
    def output_event_participant(self, acoperire_events):
        pass
