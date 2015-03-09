# -*- coding: utf-8 -*-
"""
Calcolo del codice fiscale italiano a partire dai dati anagrafici. 
Vedi http://it.wikipedia.org/wiki/Codice_fiscale per ulteriori informazioni.
Vedi http://it.wikipedia.org/wiki/Omocodia per limitazioni all'uso di questo 
codice.

Questo modulo contiene una gui (in wxPython) per le routine di codicefiscale.py
"""
import datetime
import wx
import wx.lib.masked as masked

import db
from codicefiscale import codice_fiscale


class CFValidator(wx.PyValidator):
    def __init__(self, *a, **k): wx.PyValidator.__init__(self, *a, **k)
    def Clone(self): return CFValidator() # ci vuole... non chiedersi perche'!
    
    def Validate(self, w):
        'Ritorna False se il controllo non ha dati (e lo colora in giallo).'
        ctl = self.GetWindow()
        if not ctl.IsEnabled(): # se e' disabilitato, e' sempre valido
            return True
        val = ctl.GetValue().strip()
        if not val: 
            ctl.SetBackgroundColour('yellow')
            ctl.Refresh()
            return False
        else:
            ctl.SetBackgroundColour(wx.SystemSettings_GetColour(
                                                    wx.SYS_COLOUR_WINDOW))
            ctl.Refresh()
            return True


class CFPanel(wx.Panel):
    def __init__(self, *a, **k):
        wx.Panel.__init__(self, *a, **k)

        # controlli ------------------------------------------------------------
        self.cognome = wx.TextCtrl(self, validator=CFValidator())
        self.nome = wx.TextCtrl(self, validator=CFValidator())
        self.sesso = wx.RadioBox(self, -1, choices=['M', 'F'])
        self.nascita = masked.Ctrl(self, autoformat='EUDATEDDMMYYYY.', 
                                   emptyInvalid=True)
        self.stato = wx.ComboBox(self, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.provincia = wx.ComboBox(self, style=wx.CB_DROPDOWN|wx.CB_READONLY, 
                                     validator=CFValidator())
        self.comune = wx.ComboBox(self, style=wx.CB_DROPDOWN|wx.CB_READONLY, 
                                  validator=CFValidator())
        calcola = wx.Button(self, -1, 'CALCOLA CODICE')
        reset = wx.Button(self, -1, 'resetta')
        self.codice = wx.TextCtrl(self)
        copia = wx.Button(self, -1, 'copia')
        
        # setting --------------------------------------------------------------
        self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, 
                             wx.FONTSTYLE_NORMAL))
        self.codice.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, 
                                    wx.FONTSTYLE_NORMAL, wx.FONTSTYLE_NORMAL))
        self.codice.SetEditable(False)
        calcola.SetDefault()
        self.stato.SetItems(['ITALIA'] + self._chiedi_al_db('lista_stati'))
        self.stato.SetValue('ITALIA')
        self.provincia.SetItems([''] + self._chiedi_al_db('lista_province'))
        self.provincia.SetValue('')
        
        # bindig ---------------------------------------------------------------
        for ctl, evt in ((calcola, self.su_calcola), (reset, self.su_reset), 
                         (copia, self.su_copia)):
            ctl.Bind(wx.EVT_BUTTON, evt)
        for ctl, evt in ((self.stato, self.su_stato), 
                         (self.provincia, self.su_provincia)):
            ctl.Bind(wx.EVT_COMBOBOX, evt)
        
        # layout ---------------------------------------------------------------
        g = wx.FlexGridSizer(7, 2, 5, 5)
        g.AddGrowableCol(1)
        for lab, ctl, flag in (
                ('cognome', self.cognome, wx.EXPAND), 
                ('nome', self.nome, wx.EXPAND), ('sesso', self.sesso, 0), 
                ('nato il', self.nascita, 0), ('stato', self.stato, wx.EXPAND), 
                ('provincia', self.provincia, wx.EXPAND),
                ('comune', self.comune, wx.EXPAND)):
            g.Add(wx.StaticText(self, -1, lab), 0, wx.ALIGN_CENTER_VERTICAL)
            g.Add(ctl, 0, flag)
        
        b1 = wx.BoxSizer()
        b1.Add(calcola, 2, wx.EXPAND|wx.ALL, 5)
        b1.Add(reset, 1, wx.EXPAND|wx.ALL, 5)
        
        b2 = wx.BoxSizer()
        b2.Add(self.codice, 2, wx.EXPAND|wx.ALL, 5)
        b2.Add(copia, 1, wx.EXPAND|wx.ALL, 5)
        
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(g, 0, wx.EXPAND|wx.ALL, 5)
        s.Add((5, 5))
        s.Add(b1, 0, wx.EXPAND)
        s.Add((5, 5))
        s.Add(b2, 0, wx.EXPAND)
        self.SetSizer(s)
        self.Fit()
        
    def _chiedi_al_db(self, func, *args, **kwargs):
        """Interroga il db. 
        'func' e' il nome del metodo voluto di 'Connessione'.
        Seguono gli eventuali argomenti con cui chiamare 'func'."""
        try:
            res = getattr(wx.GetApp().db, func)(*args, **kwargs)
        except db.DBQueryError:
            wx.MessageBox('Problemi con il database.', 'Errore', wx.ICON_ERROR)
            return [] 
        return res

    def su_reset(self, evt):
        for ctl in (self.cognome, self.nome, self.codice):
            ctl.SetValue('')
        self.sesso.SetSelection(0)
        self.nascita.SetValue('  .  .    ')
        self.stato.SetValue('ITALIA')
        for ctl in (self.provincia, self.comune):
            ctl.Enable(True)
            ctl.SetValue('')
        self.comune.SetItems([])
        
    def su_copia(self, evt):
        data = wx.TextDataObject()  
        data.SetText(self.codice.GetValue())  
        wx.TheClipboard.Open()  
        wx.TheClipboard.SetData(data)  
        wx.TheClipboard.Close()  

    def su_stato(self, evt): 
        '(Dis)abilito provincia e comune se (non) siamo in Italia.'
        st = (self.stato.GetValue() == 'ITALIA')
        for ctl in (self.provincia, self.comune):
            ctl.Enable(st)
            ctl.SetValue('')
        self.comune.SetItems([])
        
    def su_provincia(self, evt):
        'Popolo la lista dei comuni della provincia.'
        prov = self.provincia.GetValue()
        if prov:
            self.comune.SetItems([''] + 
                                 self._chiedi_al_db('lista_comuni', prov))

    def su_calcola(self, evt):
        self.codice.SetValue('')
        self.nascita.Refresh() # per renderlo giallo se e' vuoto!
        if not self.Validate() or not self.nascita.IsValid():
            wx.MessageBox('Dati non validi.', 'Errore', wx.ICON_ERROR)
            return False
        try:
            cod = codice_fiscale(self.cognome.GetValue().strip(),
                                 self.nome.GetValue().strip(), 
                                 datetime.datetime.strptime(
                                        self.nascita.GetValue(), '%d.%m.%Y'),
                                 self.sesso.GetStringSelection(),
                                 self.stato.GetValue(),
                                 self.provincia.GetValue(),
                                 self.comune.GetValue(),
                                 wx.GetApp().db.codici_geografici)
        except db.DBNoDataError:
            wx.MessageBox('Non esiste un codice per il comune/stato immesso.', 
                          'Errore', wx.ICON_ERROR)
            return False
        except db.DBQueryError:
            wx.MessageBox('Problemi con il database.', 'Errore', wx.ICON_ERROR)
            return False
        self.codice.SetValue(cod)


class MainFrame(wx.Frame):
    def __init__(self, *a, **k):
        wx.Frame.__init__(self, *a, **k)
        CFPanel(self)
        self.Fit()
        self.SetTitle('Calcolo Codice Fiscale')
        
        
class App(wx.App):
    def OnInit(self):
        try:
            self.db = db.Connessione()
        except db.DBQueryError:
            wx.MessageBox('Errore del database.', 'Errore', wx.ICON_ERROR)
            return False # e questo chiude l'applicazione...
        fr = MainFrame(None)
        fr.Show()
        return True
        
    def OnExit(self):
        self.db.chiudi()



if __name__ == '__main__':
    app = App(False)
    app.MainLoop()
