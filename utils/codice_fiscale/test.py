# -*- coding: utf-8 -*-
"""
Calcolo del codice fiscale italiano a partire dai dati anagrafici. 
Questo modulo contiene i test per codicefiscale.py.
"""
import unittest
from datetime import date
from codicefiscale import (codice_cognome, codice_nome, codice_nascita, 
                           codice_geografia, codice_controllo, codice_fiscale,
                           InvalidDataError)
import db

class CognomeTest(unittest.TestCase):
    def test_normale(self):
        self.assertEqual(codice_cognome(u'Rossi'), 'RSS')
        
    def test_corto(self):
        self.assertEqual(codice_cognome(u'Bo'), 'BOX')
    
    def test_corto_inversione(self):
        self.assertEqual(codice_cognome(u'Al'), 'LAX')
        
    def test_due_consonanti(self):
        self.assertEqual(codice_cognome(u'aresio'), 'RSA')
        
    def test_una_consonante(self):
        self.assertEqual(codice_cognome(u'aesio'), 'SAE')
        
    def test_doppio(self):
        self.assertEqual(codice_cognome(u'Di Nanni'), 'DNN')
        
    def test_apostrofo(self):
        self.assertEqual(codice_cognome(u"D'Andrea"), 'DND')
    
    def test_caratteri_accentati(self):
        self.assertEqual(codice_cognome(u'Noè'), 'NOE')
    

class NomeTest(unittest.TestCase):
    def test_normale(self): # la prima, terza e quarta consonante!
        self.assertEqual(codice_nome(u'Giovanni'), 'GNN')

    def test_meno_di_quattro_consonanti(self):
        self.assertEqual(codice_nome(u'Andrea'), 'NDR')


class NascitaTest(unittest.TestCase):
    def test_gennaio_maschio(self):
        self.assertEqual(codice_nascita(date(1950, 1, 15), 'm'), '50A15')
        
    def test_dicembre_femmina(self):
        self.assertEqual(codice_nascita(date(1950, 12, 5), 'f'), '50T45')


class GeografiaTest(unittest.TestCase):
    def setUp(self):
        self.con = db.Connessione()
        self.db = self.con.codici_geografici
    
    def test_italia(self):
        self.assertEqual(
            codice_geografia('ITALIA', 'BA', 'MOLFETTA', self.db), 'F284')
    
    def test_italia_inesistente(self):
        with self.assertRaises(db.DBNoDataError): 
            codice_geografia('ITALIA', 'BA', '???', self.db)
    
    def test_estero(self):
        self.assertEqual(
            codice_geografia('ALBANIA', '?', '?', self.db), 'Z100')
    
    def test_estero_inesistente(self):
        with self.assertRaises(db.DBNoDataError): 
            codice_geografia('?', '?', '?', self.db)
                          
    def tearDown(self):
        self.con.chiudi()
        
                          
class ControlloTest(unittest.TestCase):
    def test_normale(self): # alcuni codici veri da testare...
        for cod in ('GRPLCR71R24L912N', 'MRARSS34P12A662Z', 'GNNBOX78S63I754Q',
                    'DLAHUX86C50F952H', 'RSMBLL12P65E472F', 'DDDRMO56B12E625V'):
            cc = codice_controllo(cod[:-1])
            self.assertEqual(cc, cod[-1], 
                    'errore in %s: atteso %s, trovato %s' % (cod, cod[-1], cc))
            
    def test_caratteri_non_ammessi(self):
        with self.assertRaises(InvalidDataError): 
            codice_controllo(';-)')

class FiscaleTest(unittest.TestCase): 
    pass

cognome_suite = unittest.TestLoader().loadTestsFromTestCase(CognomeTest)
nome_suite = unittest.TestLoader().loadTestsFromTestCase(NomeTest)
nascita_suite = unittest.TestLoader().loadTestsFromTestCase(NascitaTest)
geografia_suite = unittest.TestLoader().loadTestsFromTestCase(GeografiaTest)
controllo_suite = unittest.TestLoader().loadTestsFromTestCase(ControlloTest)
fiscale_suite = unittest.TestLoader().loadTestsFromTestCase(FiscaleTest)

all_tests = unittest.TestSuite([cognome_suite, nome_suite, nascita_suite, 
                                geografia_suite, controllo_suite, fiscale_suite])

if __name__ == '__main__':
    unittest.TextTestRunner().run(all_tests)

    raw_input()
    