# Copyright 2024-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    #    DATA MIGRATION TOOL MAPPED FIELDS
    # ------ TABLE --> Utenti
    migrated__utenti_id = fields.Integer(string='Migrated Id')
    migrated__utenti_cognome = fields.Char(string='Migrated Cognome')
    migrated__utenti_data_nascita = fields.Date(string='Migrated Data Nascita')
    migrated__utenti_codice_fiscale = fields.Char(string='Migrated Codice Fiscale')
    migrated__utenti_sesso = fields.Selection([('m', 'Maschio'), ('f', 'Femmina'), ('x', 'X')],
                                              string='Migrated Sesso')
    migrated__utenti_data_iscrizione = fields.Date(string='Migrated Data Iscrizione')
    migrated__utenti_stato_account = fields.Selection(
        [('active', 'Attivo'), ('inactive', 'Inattivo'), ('suspended', 'Sospeso')],
        string='Migrated Stato Account')
    migrated__utenti_ultimo_accesso = fields.Datetime(string='Migrated UltimoAccesso')
    migrated__utenti_password_hash = fields.Char(string='Migrated PasswordHash')
    migrated__utenti_punti_fedelta = fields.Integer(string='Migrated Punti Fedelta')
    migrated__utenti_ruolo = fields.Selection(
        [('user', 'User'), ('admin', 'Admin'), ('guest', 'Guest')],
        string='Migrated Ruolo')
    migrated__utenti_vat = fields.Char(string='Migrated Iva')

    # ------ TABLE --> IndirizziUtente
    webfusion_indirizzi_utente_ids = fields.One2many('webfusion_indirizzi.utente', 'partner_id')


class WebFusionIndirizziUtente(models.Model):
    _name = 'webfusion_indirizzi.utente'

    # ------ TABLE --> IndirizziUtente
    migrated__indirizziutente_id = fields.Integer(string='Migrated ID')
    migrated__indirizziutente_utente_id = fields.Integer(string='Migrated Utente')
    migrated__indirizziutente_tipo_indirizzo = fields.Selection(
        [('home', 'Home'), ('office', 'Office'), ('other', 'Other')],
        string='Migrated TipoIndirizzo')
    migrated__indirizziutente_indirizzo = fields.Char(string='Migrated Indirizzo')
    migrated__indirizziutente_cap = fields.Char(string='Migrated CAP')
    migrated__indirizziutente_citta = fields.Char(string='Migrated Città')
    migrated__indirizziutente_provincia = fields.Char(string='Migrated Provincia')
    migrated__indirizziutente_nazione = fields.Char(string='Migrated Nazione')
    migrated__indirizziutente_data_aggiunta = fields.Datetime(string='Migrated Data Aggiunta')

    # ------ TABLE --> res.partner
    partner_id = fields.Many2one('res.partner')
