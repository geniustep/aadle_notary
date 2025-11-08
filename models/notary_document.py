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

        # إنشاء فاتورة تلقائياً لكل وثيقة
        for document in documents:
            if not document.invoice_id:
                document._create_invoice()

        return documents

    def write(self, vals):
        """التحقق من الصلاحيات عند التعديل"""
        for record in self:
            # منع التعديل على وثيقة مُتمة
            if record.state == 'finalized' and not self.env.user.has_group('aadle_notary.group_notary_admin'):
                raise UserError(_('لا يمكن تعديل وثيقة مُتمة!'))

        return super().write(vals)

    def unlink(self):
        """التحقق من الصلاحيات عند الحذف"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('يمكن حذف الوثائق في حالة المسودة فقط!'))
        return super().unlink()

    # ============ Action Methods ============

    def action_confirm(self):
        """تأكيد الوثيقة"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('يمكن تأكيد الوثائق في حالة المسودة فقط!'))

            # التحقق من اكتمال البيانات
            if not record.data or not record.partner_id:
                raise UserError(_('يجب إدخال بيانات الوثيقة والزبون قبل التأكيد!'))

            record.state = 'confirmed'
            record.message_post(body=_('تم تأكيد الوثيقة'))

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

        # البحث عن حساب الدخل
        income_account = self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not income_account:
            # محاولة الحصول على أي حساب income_other
            income_account = self.env['account.account'].search([
                ('account_type', '=', 'income_other'),
                ('company_id', '=', self.company_id.id)
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

    def action_generate_pdf(self):
        """
        توليد PDF للوثيقة
        TODO: التكامل مع aadle_docgen
        """
        self.ensure_one()

        # Placeholder للتكامل المستقبلي مع aadle_docgen
        # هنا سيتم استدعاء API لتوليد PDF

        raise UserError(_(
            'توليد PDF: قيد التطوير\n'
            'سيتم التكامل مع نظام aadle_docgen لتوليد الوثائق'
        ))

        # مثال على الكود المستقبلي:
        # response = requests.post(
        #     'http://aadle-docgen-api/generate',
        #     json={
        #         'template_id': self.document_type_id.template_id,
        #         'data': self.data,
        #     }
        # )
        # self.pdf_file = response.content
        # self.pdf_filename = f'{self.name}.pdf'
        # self.file_hash = hashlib.sha256(response.content).hexdigest()

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
