# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    """
    تمديد نموذج الشريك (Partner) لإضافة معلومات الزبائن العدليين
    """
    _inherit = 'res.partner'

    # ============ الحقول الإضافية ============

    is_client = fields.Boolean(
        string='زبون عدلي',
        default=False,
        help='هل هذا الشريك زبون في النظام العدلي'
    )

    national_id = fields.Char(
        string='رقم البطاقة الوطنية',
        help='رقم البطاقة الوطنية أو جواز السفر'
    )

    # ============ العلاقات ============

    document_ids = fields.One2many(
        'notary.document',
        'partner_id',
        string='الوثائق',
        help='وثائق الزبون العدلية'
    )

    # ============ الحقول المحسوبة ============

    document_count = fields.Integer(
        string='عدد الوثائق',
        compute='_compute_document_count',
        help='عدد الوثائق المرتبطة بهذا الزبون'
    )

    total_invoiced = fields.Monetary(
        string='إجمالي المبالغ',
        compute='_compute_total_invoiced',
        currency_field='currency_id',
        help='إجمالي المبالغ المفوترة للزبون'
    )

    finalized_document_count = fields.Integer(
        string='عدد الوثائق المُتمة',
        compute='_compute_document_count',
        help='عدد الوثائق المُتمة'
    )

    # ============ Computed Methods ============

    @api.depends('document_ids')
    def _compute_document_count(self):
        """حساب عدد الوثائق"""
        for partner in self:
            partner.document_count = len(partner.document_ids)
            partner.finalized_document_count = len(
                partner.document_ids.filtered(lambda d: d.state == 'finalized')
            )

    @api.depends('document_ids', 'document_ids.invoice_id', 'document_ids.invoice_id.amount_total')
    def _compute_total_invoiced(self):
        """حساب إجمالي المبالغ المفوترة"""
        for partner in self:
            total = 0.0
            for document in partner.document_ids:
                if document.invoice_id:
                    total += document.invoice_id.amount_total
            partner.total_invoiced = total

    # ============ Actions ============

    def action_view_documents(self):
        """
        فتح قائمة وثائق الزبون
        Smart Button Action
        """
        self.ensure_one()
        return {
            'name': _('وثائق الزبون - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'notary.document',
            'view_mode': 'tree,form,kanban',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
                'search_default_partner_id': self.id,
            },
        }

    def action_view_invoices(self):
        """
        فتح قائمة فواتير الزبون العدلية
        """
        self.ensure_one()
        invoice_ids = self.document_ids.mapped('invoice_id').ids
        return {
            'name': _('فواتير الزبون - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', invoice_ids), ('move_type', '=', 'out_invoice')],
            'context': {
                'default_partner_id': self.id,
            },
        }
