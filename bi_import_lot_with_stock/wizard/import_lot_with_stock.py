from odoo import api, models, fields, exceptions, tools, _
from odoo.exceptions import warnings
from odoo.exceptions import AccessError, UserError, ValidationError
# import datetime
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)
import io

try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')
try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')
# for xls 
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')
import tempfile
import binascii


class StockImport(models.TransientModel):
    _name = "stock.import"
    _description = "stock import"

    file = fields.Binary('File')
    filename = fields.Char(string="filename")
    location = fields.Many2one('stock.location', string="Location", required=True)
    name = fields.Char('Name', required=True)
    lot_with_date = fields.Boolean('Import lot with date details', required=True)
    import_prod_option = fields.Selection([('barcode', 'Barcode'), ('code', 'Code'), ('name', 'Name')],
                                          string='Import Product By ', default='code')
    import_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select', default='csv')
    
    sample_option = fields.Selection([('csv', 'CSV'),('xls', 'XLS')],string='Sample Type',default='csv')
    down_samp_file = fields.Boolean(string='Download Sample Files')

    def import_file(self):
        product_obj = self.env['product.product']
        stock_lot_obj = self.env['stock.lot']
        
        if not self.file:
            raise UserError("Please upload a file to import")
        if self.import_option == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xls")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except:
                raise UserError(_("Please select a XLS file or You have selected invalid file"))

            res_user_id = self.env['res.users'].browse(self.env.uid)

            
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row: row.value.encode('utf-8'), \
                                 sheet.row(row_no))
                else:
                    line = list(map(lambda row: isinstance(row.value, bytes) \
                                                and row.value.encode('utf-8') \
                                                or str(row.value), sheet.row(row_no)))
                    if line:
                        if self.import_prod_option == 'name':
                            product_id = product_obj.search([('name', '=', line[1])], limit=1)
                            if not product_id:
                                raise ValidationError('Product name is not available')
                        elif self.import_prod_option == 'code':
                            product_id = product_obj.search([('default_code', '=', line[1])], limit=1)
                            if not product_id:
                                raise ValidationError('Product code is not available')
                        elif self.import_prod_option == 'barcode':
                            product_id = product_obj.search([('barcode', '=', line[1].split('.')[0])], limit=1)
                            if not product_id:
                                raise ValidationError('Product barcode is not available')
                        if product_id:
                            if self.lot_with_date == True:

                                if len(line) < 7:
                                    raise UserError("Dates not found in Xls file")
                                for rec in range(4, 8):
                                    if isinstance(line[rec], str):
                                        if line[rec].split('/'):
                                            if len(line[rec].split('-')) > 1 or len(line[rec].split('/')[0]) > 2 or len(
                                                    line[rec].split(':')) < 3:
                                                raise ValidationError(
                                                    _('Wrong Date Format. Date Should be in format MM/DD/YYYY H:M:S.'))

                                best_date = datetime.strptime(line[4], "%m/%d/%Y %H:%M:%S") - timedelta(hours=5,
                                                                                                        minutes=30)
                                removal_date = datetime.strptime(line[5], "%m/%d/%Y %H:%M:%S") - timedelta(hours=5,
                                                                                                           minutes=30)
                                exp_date = datetime.strptime(line[6], "%m/%d/%Y %H:%M:%S") - timedelta(hours=5,
                                                                                                       minutes=30)
                                alert_date = datetime.strptime(line[7], "%m/%d/%Y %H:%M:%S") - timedelta(hours=5,
                                                                                                         minutes=30)

                                values.update({
                                    'serial/lot number': line[0],
                                    'product': line[1],
                                    'qty': line[2],
                                    'Internal ref': line[3],
                                    'best before date': best_date,
                                    'removal Date': removal_date,
                                    'end of life date': exp_date,
                                    'alert date': alert_date
                                })

                                product_uom_id = product_id.uom_id
                                lot_id = False
                                if values.get('serial/lot number'):
                                    lot_id = stock_lot_obj.search([
                                        ('product_id', '=', product_id.id),
                                        ('name', '=', values.get('serial/lot number'))
                                    ])
                                    lot_id.write({'use_date': values.get('best before date'),
                                                  'removal_date': values.get('removal Date'),
                                                  'expiration_date': values.get('end of life date'),
                                                  'alert_date': values.get('alert date')
                                                  })

                                    if not lot_id:
                                        lot = stock_lot_obj.create({
                                            'name': values.get('serial/lot number'),
                                            'product_id': product_id.id,
                                            'company_id': self.env.user.company_id.id,
                                            'qty_file': values.get('qty'),
                                            'ref': str(values.get('Internal ref')),
                                            'use_date': values.get('best before date'),
                                            'removal_date': values.get('removal Date'),
                                            'expiration_date': values.get('end of life date'),
                                            'alert_date': values.get('alert date')})

                                        lot_id = lot
                                if lot_id:
                                    lot_id = lot_id.id
                                    product_id.write({
                                        'tracking': 'lot'
                                    })

                            else:
                                values.update({
                                    'serial/lot number': line[0],
                                    'product': line[1],
                                    'qty': line[2],
                                    'Internal ref': line[3],
                                })
                                product_uom_id = product_id.uom_id
                                lot_id = False
                                if values.get('serial/lot number'):
                                    lot_id = stock_lot_obj.search([
                                        ('product_id', '=', product_id.id),
                                        ('name', '=', values.get('serial/lot number'))
                                    ])
                                    if not lot_id:
                                        lot = stock_lot_obj.create({
                                            'name': values.get('serial/lot number'),
                                            'product_id': product_id.id,
                                            'company_id': self.env.user.company_id.id,
                                            'qty_file': values['qty'],
                                            'ref': str(values.get('Internal ref'))})
                                        lot_id = lot
                                if lot_id:
                                    lot_id = lot_id.id
                                    product_id.write({
                                        'tracking': 'lot'
                                    })
                            
        else:
            data = base64.b64decode(self.file)
            try:
                file_input = io.StringIO(data.decode("utf-8"))
            except UnicodeError:
                raise ValidationError('Invalid CSV file!')
            keys = ['serial/lot number', 'product', 'qty', 'Internal ref', 'best before date', 'removal date',
                    'end of life date',
                    'alert date']
            csv_data = base64.b64decode(self.file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=',')

            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise ValidationError(_("Invalid CSV file!"))
            values = {}
            res_user_id = self.env['res.users'].browse(self.env.uid)

            
            for i in range(len(file_reader)):
                if i != 0:

                    val = {}
                    list1 = []
                    try:
                        field = list(map(str, file_reader[i]))
                    except ValueError:
                        raise ValidationError(_("Don't Use Character only, Use numbers too..!!"))
                    values = dict(zip(keys, field))
                    if values:
                        if i == 0:
                            continue
                        else:
                            if self.import_prod_option == 'name':
                                product_id = product_obj.search([('name', '=', values['product'])], limit=1)
                                if not product_id:
                                    raise ValidationError('Product name is not available')
                            elif self.import_prod_option == 'code':
                                product_id = product_obj.search([('default_code', '=', values['product'])], limit=1)
                                if not product_id:
                                    raise ValidationError('Product code is not available')
                            elif self.import_prod_option == 'barcode':
                                product_id = product_obj.search([('barcode', '=', values['product'])], limit=1)
                                if not product_id:
                                    raise ValidationError('Product barcode is not available')
                            if product_id:

                                if self.lot_with_date == True:

                                    if not values.get('best before date'):
                                        raise UserError('Best before date not found in file')
                                    if not values.get('removal date'):
                                        raise UserError('Removal date not found in file')
                                    if not values.get('end of life date'):
                                        raise UserError('Expiration date not found in file')
                                    if not values.get('alert date'):
                                        raise UserError('Alert date date not found in file')

                                    if isinstance(values['best before date'], str):
                                        date = values['best before date']
                                        if date.split('/'):
                                            if len(date.split('-')) > 1 or len(date.split('/')[0]) > 2 or len(
                                                    date.split(':')) < 3:
                                                raise ValidationError(
                                                    _('Wrong Date Format. Date Should be in format MM/DD/YYYY H:M:S.'))

                                    if isinstance(values['removal date'], str):
                                        date = values['removal date']
                                        if date.split('/'):
                                            if len(date.split('-')) > 1 or len(date.split('/')[0]) > 2 or len(
                                                    date.split(':')) < 3:
                                                raise ValidationError(
                                                    _('Wrong Date Format. Date Should be in format MM/DD/YYYY H:M:S.'))
                                    if isinstance(values['end of life date'], str):
                                        date = values['end of life date']
                                        if date.split('/'):
                                            if len(date.split('-')) > 1 or len(date.split('/')[0]) > 2 or len(
                                                    date.split(':')) < 3:
                                                raise ValidationError(
                                                    _('Wrong Date Format. Date Should be in format MM/DD/YYYY H:M:S.'))
                                    if isinstance(values['alert date'], str):
                                        date = values['alert date']
                                        if date.split('/'):
                                            if len(date.split('-')) > 1 or len(date.split('/')[0]) > 2 or len(
                                                    date.split(':')) < 3:
                                                raise ValidationError(
                                                    _('Wrong Date Format. Date Should be in format MM/DD/YYYY H:M:S.'))

                                    best_date = datetime.strptime(values['best before date'],
                                                                  "%m/%d/%Y %H:%M:%S") - timedelta(hours=5, minutes=30)
                                    removal_date = datetime.strptime(values['removal date'],
                                                                     "%m/%d/%Y %H:%M:%S") - timedelta(hours=5,
                                                                                                      minutes=30)
                                    exp_date = datetime.strptime(values['end of life date'],
                                                                 "%m/%d/%Y %H:%M:%S") - timedelta(hours=5, minutes=30)
                                    alert_date = datetime.strptime(values['alert date'],
                                                                   "%m/%d/%Y %H:%M:%S") - timedelta(hours=5, minutes=30)

                                    product_uom_id = product_id.uom_id
                                    lot_id = False
                                    if values.get('serial/lot number'):
                                        lot_id = stock_lot_obj.search([
                                            ('product_id', '=', product_id.id),
                                            ('name', '=', values.get('serial/lot number'))
                                        ])
                                        lot_id.write({'use_date': best_date,
                                                      'removal_date': removal_date,
                                                      'expiration_date': exp_date,
                                                      'alert_date': alert_date})

                                        if not lot_id:
                                            lot = stock_lot_obj.create({
                                                'name': values.get('serial/lot number'),
                                                'product_id': product_id.id,
                                                'company_id': self.env.user.company_id.id,
                                                'qty_file': values['qty'],
                                                'ref': str(values.get('Internal ref')),
                                                'use_date': best_date,
                                                'removal_date': removal_date,
                                                'expiration_date': exp_date,
                                                'alert_date': alert_date})
                                            lot_id = lot
                                    if lot_id:
                                        lot_id = lot_id.id
                                        product_id.write({
                                            'tracking': 'lot'
                                        })
                                else:
                                    product_uom_id = product_id.uom_id
                                    lot_id = False
                                    if values.get('serial/lot number'):
                                        lot_id = stock_lot_obj.search([
                                            ('product_id', '=', product_id.id),
                                            ('name', '=', values.get('serial/lot number'))
                                        ])
                                        if not lot_id:
                                            lot = stock_lot_obj.create({
                                                'name': values.get('serial/lot number'),
                                                'product_id': product_id.id,
                                                'company_id': self.env.user.company_id.id,
                                                'qty_file': values.get('qty'),
                                                'ref': str(values.get('Internal ref'))})
                                            lot_id = lot
                                    if lot_id:
                                        lot_id = lot_id.id
                                        product_id.write({
                                            'tracking': 'lot'
                                        })
                                        
    
    def download_auto(self):
        return {
             'type' : 'ir.actions.act_url',
             'url': '/web/binary/download_document?model=stock.import&id=%s'%(self.sudo().id),
             'target': 'new',
             }
    

class ProductionLotInherit(models.Model):
    _inherit = 'stock.lot'

    qty_file = fields.Float('Qty')

    def _product_qty(self):
        for lot in self:
            if lot.qty_file:
                lot.update({'product_qty': lot.qty_file})
            else:
                # We only care for the quants in internal or transit locations.
                quants = lot.quant_ids.filtered(lambda q: q.location_id.usage == 'internal' or (
                        q.location_id.usage == 'transit' and q.location_id.company_id))
                lot.product_qty = sum(quants.mapped('quantity'))
