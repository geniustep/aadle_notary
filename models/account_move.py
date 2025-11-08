# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    """
    تمديد نموذج الفاتورة لربطها بالوثائق العدلية
    """
    _inherit = 'account.move'

    # ============ الحقول الإضافية ============

    notary_document_id = fields.Many2one(
        'notary.document',
        string='الوثيقة العدلية',
        copy=False,
        help='الوثيقة العدلية المرتبطة بهذه الفاتورة'
    )

    is_notary_invoice = fields.Boolean(
        string='فاتورة عدلية',
        default=False,
        copy=False,
        help='هل هذه فاتورة مرتبطة بوثيقة عدلية'
    )

    # ============ Computed Fields ============

    notary_document_name = fields.Char(
        related='notary_document_id.name',
        string='رقم الوثيقة',
        readonly=True,
        help='رقم الوثيقة المرتبطة'
    )

    notary_document_type = fields.Char(
        related='notary_document_id.document_type_id.name',
        string='نوع الوثيقة',
        readonly=True,
        help='نوع الوثيقة المرتبطة'
    )

    # ============ Actions ============

    def action_view_notary_document(self):
        """
        فتح الوثيقة العدلية المرتبطة
        Smart Button Action
        """
        self.ensure_one()
        if not self.notary_document_id:
            return

        return {
            'name': _('الوثيقة العدلية'),
            'type': 'ir.actions.act_window',
            'res_model': 'notary.document',
            'res_id': self.notary_document_id.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
        }
