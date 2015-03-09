# -*- coding: utf-8 -*-
"""
Calcolo del codice fiscale italiano a partire dai dati anagrafici.
Vedi http://it.wikipedia.org/wiki/Codice_fiscale per ulteriori informazioni.
Vedi http://it.wikipedia.org/wiki/Omocodia per limitazioni all'uso di questo
codice.

Questo modulo contiene il motore di calcolo.
"""

from datetime import date

class InvalidDataError(Exception): pass

# tavola di conversione per vocali accentate e altri segni strani
# TODO aggiungerne? Ma bisogna essere sicuri che si "traducono" davvero cosi'
segni_normalizzati = dict(zip(
    (ord(i) for i in u"ÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÇ´"),
    (ord(i) for i in u"AAAAAAEEEEIIIIOOOOOUUUUC'")))


# tavole di eliminazione per vocali e consonanti,
# compresi spazio e apostrofo per nomi doppi e 'nobili'
vocali = {ord(i):None for i in u" 'AEIOU"}
consonanti = {ord(i):None for i in u" 'BCDFGHJKLMNPQRSTVWXYZ"}

def codice_cognome(cognome):
    """Le prime tre lettere del codice, relative al cognome.
    @type cognome: unicode"""
    cognome = cognome.upper().translate(segni_normalizzati)
    cons = cognome.translate(vocali)
    vocs = cognome.translate(consonanti)
    return (cons + vocs)[:3].ljust(3, u'X')

def codice_nome(nome):
    """Le seconde tre lettere del codice, relative al nome.
    @type nome: unicode"""
    nome = nome.upper().translate(segni_normalizzati)
    cons = nome.translate(vocali)
    vocs = nome.translate(consonanti)
    try:
        return ''.join((cons[0], cons[2], cons[3]))
    except IndexError:
        return (cons + vocs)[:3].ljust(3, u'X')


mesi = '_ABCDEHLMPRST' # a ogni mese la sua lettera (piu' lo zero che non c'e')

def codice_nascita(data, sesso):
    """Le lettere dalla settima all'undicesima, per la data di nascita.
    @param data: data di nascita
    @type  data: datetime.date
    @param sesso: sesso ('M' o 'm' per maschile; tutto il resto e' interpretato
                         come femminile)
    """
    mod = 0 if sesso in 'Mm' else 40
    g = str(data.day+mod).zfill(2)
    m = mesi[data.month]
    a = str(data.year)[-2:]
    return a + m + g


def codice_geografia(stato, provincia, comune, db):
    """Le lettere dalla dodicesima alla quindicesima, per il luogo di nascita.
    @param db: un callable che restituisce il codice (pescandolo da un db
               o altro storage). La signature del callable deve essere
               db(stato, provincia, comune).
    """
    return db(stato, provincia, comune)


alfabeto = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
# codici di controllo: per le lettere pari (prima posizione) e dispari (seconda)
controllo = {'0':(0, 1),   '1':(1, 0),   '2':(2, 5),   '3':(3, 7),
             '4':(4, 9),   '5':(5, 13),  '6':(6, 15),  '7':(7, 17),
             '8':(8, 19),  '9':(9, 21),
             'A':(0, 1),   'B':(1, 0),   'C':(2, 5),   'D':(3, 7),
             'E':(4, 9),   'F':(5, 13),  'G':(6, 15),  'H':(7, 17),
             'I':(8, 19),  'J':(9, 21),  'K':(10, 2),  'L':(11, 4),
             'M':(12, 18), 'N':(13, 20), 'O':(14, 11), 'P':(15, 3),
             'Q':(16, 6),  'R':(17, 8),  'S':(18, 12), 'T':(19, 14),
             'U':(20, 16), 'V':(21, 10), 'W':(22, 22), 'X':(23, 25),
             'Y':(24, 24), 'Z':(25, 23)}

def codice_controllo(codice):
    """La sedicesima e ultima lettera, codice di controllo.
    Solleva InvalidDataError se l'input contiene caratteri non ammessi. """
    try:
        resto = sum([controllo[i][(n+1)%2] for n, i in enumerate(codice)])%26
    except KeyError:
        raise InvalidDataError('caratteri non validi in input')
    return alfabeto[resto]


def codice_fiscale(cognome, nome, nascita, sesso, stato, provincia, comune, db):
    """Restituisce il codice fiscale a partire dai dati anagrafici.
    Solleva InvalidDataError se nome o cognome contengono caratteri non ammessi.
    @type  cognome: unicode
    @type  nome: unicode
    @type  nascita: datetime.date
    @param db: un callable che restituisce il codice del comume di nascita
               (pescandolo da un db o altro storage). La signature deve essere
               db(stato, provincia, comune).
    """
    codice = (codice_cognome(cognome) +
              codice_nome(nome) +
              codice_nascita(nascita, sesso) +
              codice_geografia(stato, provincia, comune, db))
    return codice + codice_controllo(codice)


if __name__ == '__main__':
    # una piccola interfaccia testuale per giocare un po'...
    import sys
    import db
    try:
        con = db.Connessione()
    except:
        input('Problema con il database... Invio per terminare.')
        sys.exit(1)

    enc = sys.stdin.encoding
    sep = '\n' + '='*30 + '\n\n'
    print('CALCOLO DEL CODICE FISCALE\n\n')
    while True:
        if input('Vuoi calcolare un CF? (s/n)') != 's': break
        nome =      input('Nome?               ').strip().decode(enc)
        cognome =   input('Cognome?            ').strip().decode(enc)
        sesso =     input('Sesso? (m/f)        ').strip()
        giorno =    input('Giorno di nascita?  ').strip()
        mese =      input('Mese di nascita?    ').strip()
        anno =      input('Anno di nascita?    ').strip()
        stato =     input('Stato di nascita?   ').strip().upper().decode(enc)
        provincia = input('Prov. di nascita?   ').strip().upper().decode(enc)
        comune =    input('Comune di nascita?  ').strip().upper().decode(enc)
        try:
            nascita = date(int(anno), int(mese), int(giorno))
        except ValueError:
            print('Data di nascita non valida.', sep)
            continue
        try:
            cod = codice_fiscale(cognome, nome, nascita,
                                 sesso, stato, provincia, comune,
                                 con.codici_geografici)
            print('CF: ', cod, sep)
        except InvalidDataError:
            print('Nome o cognome contengono caratteri non validi.', sep)
        except db.DBQueryError:
            print('Ci sono problemi con la query del database.', sep)
        except db.DBNoDataError:
            print('Non esiste un codice per il comune/stato immesso.', sep)

