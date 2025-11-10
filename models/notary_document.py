# -*- coding: utf-8 -*-

import json
import hashlib
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class NotaryDocument(models.Model):
    """
    الوثائق العدلية
    إدارة الوثائق التي ينشئها العدل مع كل التفاصيل والـ workflows
    """
    _name = 'notary.document'
    _description = 'الوثيقة العدلية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc, id desc'
    _rec_name = 'name'

    # ============ الحقول الأساسية ============

    name = fields.Char(
        string='رقم الوثيقة',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default='/',
        help='رقم الوثيقة (يُنشأ تلقائياً)'
    )

    document_type_id = fields.Many2one(
        'notary.document.type',
        string='نوع الوثيقة',
        required=True,
        tracking=True,
        ondelete='restrict',
        help='نوع الوثيقة العدلية'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='الزبون',
        required=True,
        tracking=True,
        ondelete='restrict',
        help='الزبون الذي تُنشأ له الوثيقة'
    )

    notary_id = fields.Many2one(
        'res.users',
        string='العدل',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        ondelete='restrict',
        help='العدل المسؤول عن إنشاء الوثيقة'
    )

    company_id = fields.Many2one(
        'res.company',
        string='المكتب/الشركة',
        required=True,
        default=lambda self: self.env.company,
        help='المكتب أو الشركة المالكة للوثيقة'
    )

    # ============ التواريخ ============

    date_created = fields.Date(
        string='تاريخ الإنشاء',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help='تاريخ إنشاء الوثيقة'
    )

    date_finalized = fields.Date(
        string='تاريخ الإتمام',
        readonly=True,
        tracking=True,
        copy=False,
        help='تاريخ إتمام الوثيقة'
    )

    # ============ البيانات (JSON) ============

    data = fields.Json(
        string='بيانات الوثيقة',
        help='البيانات المرنة للوثيقة بصيغة JSON (تختلف حسب نوع الوثيقة)',
        default=dict
    )

    data_display = fields.Text(
        string='عرض البيانات',
        compute='_compute_data_display',
        help='عرض منسّق للبيانات'
    )

    # ============ الحالة ============

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('confirmed', 'مؤكد'),
        ('finalized', 'مُتمّ'),
        ('cancelled', 'ملغي'),
    ], string='الحالة', default='draft', required=True, tracking=True, help='حالة الوثيقة')

    # ============ السعر ============

    price = fields.Float(
        string='السعر',
        required=True,
        default=0.0,
        tracking=True,
        help='السعر الفعلي للوثيقة (قابل للتعديل)'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='العملة',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help='عملة السعر'
    )

    # ============ الملفات ============

    pdf_file = fields.Binary(
        string='ملف PDF',
        attachment=True,
        copy=False,
        help='ملف PDF المولد للوثيقة'
    )

    pdf_filename = fields.Char(
        string='اسم الملف',
        help='اسم ملف PDF'
    )

    pdf_url = fields.Char(
        string='رابط الملف',
        help='رابط الملف في MinIO أو نظام التخزين'
    )

    qr_code = fields.Char(
        string='رمز QR',
        help='رمز QR للتحقق من الوثيقة'
    )

    file_hash = fields.Char(
        string='Hash الملف',
        help='SHA256 hash للملف للتحقق من صحته'
    )

    has_pdf = fields.Boolean(
        string='يوجد PDF',
        compute='_compute_has_pdf',
        help='هل تم توليد ملف PDF للوثيقة'
    )

    pdf_file_size = fields.Integer(
        string='حجم الملف (بايت)',
        compute='_compute_pdf_file_size',
        help='حجم ملف PDF بالبايت'
    )

    pdf_file_size_display = fields.Char(
        string='حجم الملف',
        compute='_compute_pdf_file_size',
        help='حجم ملف PDF بشكل منسق'
    )

    # ============ الفاتورة ============

    invoice_id = fields.Many2one(
        'account.move',
        string='الفاتورة',
        copy=False,
        readonly=True,
        help='الفاتورة المرتبطة بالوثيقة'
    )

    invoice_state = fields.Selection(
        related='invoice_id.payment_state',
        string='حالة الفاتورة',
        help='حالة دفع الفاتورة'
    )

    is_invoice_paid = fields.Boolean(
        string='الفاتورة مدفوعة',
        compute='_compute_is_invoice_paid',
        help='هل الفاتورة مدفوعة بالكامل'
    )

    # ============ حقول مساعدة ============

    notes = fields.Text(
        string='ملاحظات',
        help='ملاحظات إضافية على الوثيقة'
    )

    # ============ SQL Constraints ============

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'رقم الوثيقة يجب أن يكون فريداً!'),
        ('price_positive', 'CHECK(price >= 0)', 'السعر لا يمكن أن يكون سالباً!'),
    ]

    # ============ Computed Fields ============

    @api.depends('data')
    def _compute_data_display(self):
        """عرض منسّق للبيانات JSON"""
        for record in self:
            if record.data:
                try:
                    record.data_display = json.dumps(record.data, ensure_ascii=False, indent=2)
                except:
                    record.data_display = str(record.data)
            else:
                record.data_display = ''

    @api.depends('pdf_file', 'pdf_url')
    def _compute_has_pdf(self):
        """التحقق من وجود ملف PDF"""
        for record in self:
            record.has_pdf = bool(record.pdf_file or record.pdf_url)

    @api.depends('pdf_file')
    def _compute_pdf_file_size(self):
        """حساب حجم ملف PDF"""
        import base64
        for record in self:
            if record.pdf_file:
                try:
                    # فك تشفير base64 وحساب الحجم
                    decoded = base64.b64decode(record.pdf_file)
                    size_bytes = len(decoded)
                    record.pdf_file_size = size_bytes
                    
                    # تنسيق الحجم
                    if size_bytes < 1024:
                        record.pdf_file_size_display = f"{size_bytes} بايت"
                    elif size_bytes < 1024 * 1024:
                        size_kb = size_bytes / 1024
                        record.pdf_file_size_display = f"{size_kb:.2f} KB"
                    else:
                        size_mb = size_bytes / (1024 * 1024)
                        record.pdf_file_size_display = f"{size_mb:.2f} MB"
                except Exception:
                    record.pdf_file_size = 0
                    record.pdf_file_size_display = "غير متاح"
            else:
                record.pdf_file_size = 0
                record.pdf_file_size_display = ""

    @api.depends('invoice_id', 'invoice_id.payment_state')
    def _compute_is_invoice_paid(self):
        """التحقق من دفع الفاتورة"""
        for record in self:
            record.is_invoice_paid = record.invoice_id and record.invoice_id.payment_state == 'paid'

    # ============ Onchange Methods ============

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        """عند تغيير نوع الوثيقة، نحدّث السعر"""
        if self.document_type_id:
            self.price = self.document_type_id.default_price
            self.currency_id = self.document_type_id.currency_id

    # ============ CRUD Methods ============

    @api.model_create_multi
    def create(self, vals_list):
        """إنشاء وثيقة مع رقم تلقائي"""
        for vals in vals_list:
            # توليد رقم الوثيقة إذا لم يُعطَ
            if vals.get('name', '/') == '/':
                document_type = self.env['notary.document.type'].browse(vals.get('document_type_id'))
                if document_type and document_type.sequence_prefix:
                    sequence_code = f'notary.document.{document_type.code}'
                    # محاولة الحصول على sequence موجود
                    sequence = self.env['ir.sequence'].search([('code', '=', sequence_code)], limit=1)
                    if not sequence:
                        # إنشاء sequence جديد إذا لم يكن موجوداً
                        sequence = self.env['ir.sequence'].sudo().create({
                            'name': f'Notary Document - {document_type.name}',
                            'code': sequence_code,
                            'prefix': f'{document_type.sequence_prefix}%(year)s-',
                            'padding': 6,
                            'company_id': vals.get('company_id', self.env.company.id),
                        })
                    vals['name'] = sequence.next_by_id()
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('notary.document.default') or '/'

            # إذا لم يُحدد السعر، نأخذه من نوع الوثيقة
            if 'price' not in vals or vals['price'] == 0.0:
                document_type = self.env['notary.document.type'].browse(vals.get('document_type_id'))
                if document_type:
                    vals['price'] = document_type.default_price

        documents = super().create(vals_list)

        # لا يتم إنشاء الفاتورة تلقائياً - سيتم إنشاؤها عند التأكيد
        # for document in documents:
        #     if not document.invoice_id:
        #         document._create_invoice()

        return documents

    def write(self, vals):
        """التحقق من الصلاحيات عند التعديل وتحديث الفاتورة"""
        # حفظ السعر القديم قبل التحديث
        old_prices = {}
        if 'price' in vals:
            for record in self:
                old_prices[record.id] = record.price
        
        for record in self:
            # منع التعديل على وثيقة مُتمة
            if record.state == 'finalized' and not self.env.user.has_group('aadle_notary.group_notary_admin'):
                raise UserError(_('لا يمكن تعديل وثيقة مُتمة!'))

        # حفظ التغييرات أولاً
        result = super().write(vals)
        
        # تحديث السعر في الفاتورة بعد حفظ التغييرات
        if 'price' in vals:
            for record in self:
                if record.invoice_id and record.invoice_id.invoice_line_ids:
                    new_price = record.price  # السعر الجديد بعد الحفظ
                    invoice = record.invoice_id
                    invoice_line = invoice.invoice_line_ids[0]
                    old_price = invoice_line.price_unit
                    
                    # تحديث السعر فقط إذا تغير
                    if new_price != old_price:
                        # تحديث السعر في سطر الفاتورة
                        invoice_line.write({'price_unit': new_price})
                        
                        # إعادة حساب الفاتورة
                        invoice._onchange_invoice_line_ids()
                        if hasattr(invoice, '_recompute_tax_lines'):
                            invoice._recompute_tax_lines()
                        if hasattr(invoice, '_recompute_payment_terms_lines'):
                            invoice._recompute_payment_terms_lines()
                        
                        # إضافة رسالة
                        record.message_post(body=_('تم تحديث السعر في الفاتورة من %s إلى %s') % (old_price, new_price))
                        invoice.message_post(body=_('تم تحديث السعر من الوثيقة: %s') % record.name)
        
        return result

    def unlink(self):
        """التحقق من الصلاحيات عند الحذف"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('يمكن حذف الوثائق في حالة المسودة فقط!'))
        return super().unlink()

    # ============ Action Methods ============

    def action_confirm(self):
        """تأكيد الوثيقة وإنشاء وتأكيد الفاتورة"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('يمكن تأكيد الوثائق في حالة المسودة فقط!'))

            # التحقق من اكتمال البيانات الأساسية
            if not record.partner_id:
                raise UserError(_('يجب اختيار الزبون قبل التأكيد!'))
            
            if not record.document_type_id:
                raise UserError(_('يجب اختيار نوع الوثيقة قبل التأكيد!'))
            
            # البيانات JSON اختيارية - فقط التحقق من وجودها إذا كانت مطلوبة
            # (يمكن إضافة التحقق الإضافي حسب نوع الوثيقة لاحقاً)

            # إنشاء الفاتورة إذا لم تكن موجودة
            if not record.invoice_id:
                record._create_invoice()
            
            # تأكيد الفاتورة
            if record.invoice_id:
                if record.invoice_id.state == 'draft':
                    record.invoice_id.action_post()
                    record.message_post(body=_('تم تأكيد الوثيقة وإنشاء وتأكيد الفاتورة'))
                else:
                    record.message_post(body=_('تم تأكيد الوثيقة'))
            else:
                record.message_post(body=_('تم تأكيد الوثيقة'))
            
            record.state = 'confirmed'

    def action_finalize(self):
        """إتمام الوثيقة"""
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_('يمكن إتمام الوثائق المؤكدة فقط!'))

            # التحقق من دفع الفاتورة
            if not record.is_invoice_paid:
                raise UserError(_('يجب دفع الفاتورة قبل إتمام الوثيقة!'))

            record.write({
                'state': 'finalized',
                'date_finalized': fields.Date.context_today(record),
            })
            record.message_post(body=_('تم إتمام الوثيقة'))

    def action_cancel(self):
        """إلغاء الوثيقة"""
        for record in self:
            if record.state == 'finalized':
                raise UserError(_('لا يمكن إلغاء وثيقة مُتمة!'))

            record.state = 'cancelled'
            record.message_post(body=_('تم إلغاء الوثيقة'))

    def action_draft(self):
        """إرجاع إلى المسودة"""
        for record in self:
            if record.state == 'finalized':
                raise UserError(_('لا يمكن إرجاع وثيقة مُتمة إلى المسودة!'))

            record.state = 'draft'
            record.message_post(body=_('تم إرجاع الوثيقة إلى المسودة'))

    def action_view_invoice(self):
        """فتح الفاتورة المرتبطة"""
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_('لا توجد فاتورة مرتبطة بهذه الوثيقة!'))

        return {
            'name': _('الفاتورة'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
        }

    def action_create_invoice(self):
        """إنشاء فاتورة يدوياً"""
        for record in self:
            if record.invoice_id:
                raise UserError(_('توجد فاتورة مرتبطة بالفعل!'))
            record._create_invoice()

    def _create_invoice(self):
        """إنشاء فاتورة للوثيقة"""
        self.ensure_one()

        # التحقق من وجود journal
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not journal:
            raise UserError(_('لا يوجد journal مبيعات! يرجى إنشاء واحد أولاً.'))

        # البحث عن حساب الدخل (البحث ثم التصفية حسب الشركة)
        # في Odoo 18، account.account لا يحتوي على company_id مباشرة
        income_accounts = self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('deprecated', '=', False)
        ], limit=10)
        
        # تصفية حسب الشركة
        income_account = income_accounts.filtered(
            lambda a: self.company_id.id in a.company_ids.ids
        )[:1]

        if not income_account:
            # محاولة الحصول على أي حساب income_other
            income_other_accounts = self.env['account.account'].search([
                ('account_type', '=', 'income_other'),
                ('deprecated', '=', False)
            ], limit=10)
            
            income_account = income_other_accounts.filtered(
                lambda a: self.company_id.id in a.company_ids.ids
            )[:1]
        
        # إذا لم نجد حساب مرتبط بالشركة، نبحث عن أي حساب income
        if not income_account:
            income_account = self.env['account.account'].search([
                ('account_type', 'in', ['income', 'income_other']),
                ('deprecated', '=', False)
            ], limit=1)

        if not income_account:
            raise UserError(_('لا يوجد حساب دخل! يرجى إنشاء حساب دخل في المحاسبة.'))

        # إنشاء الفاتورة
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'company_id': self.company_id.id,
            'journal_id': journal.id,
            'notary_document_id': self.id,
            'is_notary_invoice': True,
            'invoice_line_ids': [(0, 0, {
                'name': _('وثيقة عدلية: %s') % self.document_type_id.name,
                'quantity': 1,
                'price_unit': self.price,
                'account_id': income_account.id,
            })],
        }

        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice.id

        self.message_post(body=_('تم إنشاء الفاتورة: %s') % invoice.name)

        return invoice

    # تم نقل method action_generate_pdf إلى notary_document_pdf.py
    # حيث يتم التكامل الكامل مع aadle_docgen service

    def action_calculate_inheritance(self):
        """
        حساب الإرث الشرعي
        TODO: التكامل مع aadle_api
        """
        self.ensure_one()

        if self.document_type_id.code != 'inheritance_deed':
            raise UserError(_('هذه الوظيفة متاحة فقط لوثائق الإرث!'))

        # Placeholder للتكامل المستقبلي مع aadle_api
        raise UserError(_(
            'حساب الإرث: قيد التطوير\n'
            'سيتم التكامل مع نظام aadle_api لحساب الإرث الشرعي'
        ))

        # مثال على الكود المستقبلي:
        # response = requests.post(
        #     'http://aadle-api/calculate-inheritance',
        #     json=self.data
        # )
        # self.data['inheritance_calculation'] = response.json()
