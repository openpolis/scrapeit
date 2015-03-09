# -*- coding: utf-8 -*-
"""
Calcolo del codice fiscale italiano a partire dai dati anagrafici.
Vedi http://it.wikipedia.org/wiki/Codice_fiscale per ulteriori informazioni.
Vedi http://it.wikipedia.org/wiki/Omocodia per limitazioni all'uso di questo
codice.

Questo modulo gestisce le query al database dei codici istat dei comuni
d'Italia, necessari per le routine di calcolo (codicefiscale.py) e alcune
query accessorie utili per la gui (gui.py).
"""

import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'codici.db')

class DBQueryError(Exception): pass
class DBNoDataError(Exception): pass

class Connessione(object):
    def __init__(self, db_path=DB):
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()
        try: # verifico che il db ci sia davvero...
            self.cur.execute('select 0 from province;')
        except sqlite3.OperationalError:
            raise DBQueryError('errore a inizializzare il database.')

    def chiudi(self):
        self.con.close()

    def codici_geografici(self, stato, provincia, comune):
        if stato == 'ITALIA':
            sql = 'SELECT codice FROM comuni WHERE comune=? AND provincia=?;'
            params = (comune.upper(), provincia.upper())
        else:
            sql = 'SELECT codice FROM stati WHERE stato=?;'
            params = (stato.upper(),)
        try:
            self.cur.execute(sql, params)
        except sqlite3.OperationalError:
            raise DBQueryError('errore nella query al database')
        try:
            return self.cur.fetchall()[0][0]
        except IndexError:
            raise DBNoDataError('nessun codice corrisponde ai valori immessi')

    # ==========================================================================
    # query aggiunte che servono alla gui
    # ==========================================================================

    def lista_stati(self):
        try:
            self.cur.execute('SELECT stato FROM stati ORDER BY stato;')
        except sqlite3.OperationalError:
            raise DBQueryError('errore nella query al database')
        return [i[0] for i in self.cur.fetchall()]

    def lista_province(self):
        try:
            self.cur.execute('SELECT sigla FROM province ORDER BY sigla;')
        except sqlite3.OperationalError:
            raise DBQueryError('errore nella query al database')
        return [i[0] for i in self.cur.fetchall()]

    def lista_comuni(self, provincia):
        sql = 'SELECT comune FROM comuni WHERE provincia=? ORDER BY comune;'
        try:
            self.cur.execute(sql, (provincia,))
        except sqlite3.OperationalError:
            raise DBQueryError('errore nella query al database')
        return [i[0] for i in self.cur.fetchall()]


