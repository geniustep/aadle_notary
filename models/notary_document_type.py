# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class NotaryDocumentType(models.Model):
    """
    أنواع الوثائق العدلية
    تعريف أنواع الوثائق المتاحة مع أسعارها الافتراضية
    """
    _name = 'notary.document.type'
    _description = 'نوع الوثيقة العدلية'
    _order = 'sequence, name'
    _rec_name = 'name'

    # الحقول الأساسية
    name = fields.Char(
        string='الاسم (عربي)',
        required=True,
        translate=True,
        help='اسم نوع الوثيقة بالعربية'
    )
    name_fr = fields.Char(
        string='الاسم (فرنسية)',
        translate=True,
        help='اسم نوع الوثيقة بالفرنسية'
    )
    code = fields.Char(
        string='الكود',
        required=True,
        help='كود فريد للنوع (marriage_contract, inheritance_deed, etc.)'
    )

    # السعر والعملة
    default_price = fields.Float(
        string='السعر الافتراضي',
        required=True,
        default=0.0,
        help='السعر الافتراضي لهذا النوع من الوثائق'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='العملة',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help='العملة المستخدمة للسعر'
    )

    # الوصف والتفاصيل
    description = fields.Text(
        string='الوصف',
        translate=True,
        help='وصف تفصيلي لنوع الوثيقة'
    )

    # الحالة والترتيب
    is_active = fields.Boolean(
        string='فعّال',
        default=True,
        help='إذا كان غير فعال، لن يظهر في القوائم'
    )
    sequence = fields.Integer(
        string='الترتيب',
        default=10,
        help='ترتيب العرض في القوائم'
    )

    # التكامل مع نظام توليد الوثائق (اختياري حالياً)
    template_id = fields.Char(
        string='معرّف القالب',
        help='معرّف القالب في نظام aadle_docgen (للاستخدام المستقبلي)'
    )

    # حقول إحصائية
    document_count = fields.Integer(
        string='عدد الوثائق',
        compute='_compute_document_count',
        help='عدد الوثائق من هذا النوع'
    )

    # Prefix للـ Sequence
    sequence_prefix = fields.Char(
        string='بادئة الترقيم',
        required=True,
        help='البادئة المستخدمة في ترقيم الوثائق (مثلاً MC- لعقد الزواج)'
    )

    # SQL Constraints
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'الكود يجب أن يكون فريداً!'),
        ('sequence_prefix_unique', 'UNIQUE(sequence_prefix)', 'بادئة الترقيم يجب أن تكون فريدة!'),
        ('default_price_positive', 'CHECK(default_price >= 0)', 'السعر لا يمكن أن يكون سالباً!'),
    ]

    @api.depends('code')
    def _compute_document_count(self):
        """حساب عدد الوثائق لكل نوع"""
        for record in self:
            record.document_count = self.env['notary.document'].search_count([
                ('document_type_id', '=', record.id)
            ])

    @api.constrains('default_price')
    def _check_default_price(self):
        """التحقق من أن السعر غير سالب"""
        for record in self:
            if record.default_price < 0:
                raise ValidationError(_('السعر الافتراضي لا يمكن أن يكون سالباً!'))

    @api.constrains('code')
    def _check_code(self):
        """التحقق من صيغة الكود"""
        for record in self:
            if record.code:
                # التحقق من أن الكود يحتوي على أحرف وأرقام و underscores فقط
                if not record.code.replace('_', '').isalnum():
                    raise ValidationError(_('الكود يجب أن يحتوي على أحرف وأرقام و underscores فقط!'))

    def action_view_documents(self):
        """
        فتح قائمة الوثائق المرتبطة بهذا النوع
        """
        self.ensure_one()
        return {
            'name': _('الوثائق - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'notary.document',
            'view_mode': 'tree,form,kanban',
            'domain': [('document_type_id', '=', self.id)],
            'context': {
                'default_document_type_id': self.id,
            },
        }
