# -*- coding: utf-8 -*-
"""
إضافة method action_generate_pdf إلى notary.document model
يجب إضافة هذا الكود إلى: /opt/aadle/aadle_notary/models/notary_document.py
"""

import base64
import hashlib
import qrcode
import requests
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class NotaryDocument(models.Model):
    _inherit = 'notary.document'  # أو _name = 'notary.document' إذا كان هذا هو الملف الأساسي

    # الحقول الإضافية للـ PDF
    pdf_file = fields.Binary(string='ملف PDF', readonly=True, attachment=True)
    pdf_filename = fields.Char(string='اسم ملف PDF', readonly=True)
    file_hash = fields.Char(string='التوقيع الرقمي (Hash)', readonly=True, size=64)
    qr_code = fields.Char(string='رمز QR للتحقق', readonly=True)

    def action_generate_pdf(self):
        """
        توليد ملف PDF للوثيقة باستخدام aadle_docgen service
        """
        self.ensure_one()

        # التحقق من أن الوثيقة مؤكدة
        if self.state not in ['confirmed', 'finalized']:
            raise UserError(_('لا يمكن توليد PDF إلا للوثائق المؤكدة أو المكتملة'))

        # الحصول على URL لخدمة aadle_docgen من الإعدادات
        ICP = self.env['ir.config_parameter'].sudo()
        primary_url = ICP.get_param('aadle.docgen_url', 'https://docgen.aadle.com')
        fallback_url = ICP.get_param('aadle.docgen_fallback_url', 'http://64.226.110.81:5000')

        # قائمة الـ URLs للتجربة بالترتيب
        docgen_urls = [primary_url, fallback_url]

        # تحضير البيانات للإرسال إلى aadle_docgen
        document_data = self._prepare_document_data_for_pdf()

        # تحديد نوع القالب بناءً على نوع الوثيقة
        template_name = self._get_template_name()

        # تنظيف إضافي للبيانات قبل الإرسال (ضمان JSON serialization)
        request_data = {
            'template': template_name,
            'data': self._sanitize_data_for_json(document_data),
            'format': 'pdf',
        }

        # متغيرات لحفظ آخر خطأ
        last_error = None
        last_url = None

        # محاولة كل URL بالترتيب
        for docgen_url in docgen_urls:
            try:
                full_url = f'{docgen_url}/api/generate'

                # استدعاء خدمة aadle_docgen
                response = requests.post(
                    full_url,
                    json=request_data,
                    timeout=30
                )

                if response.status_code == 200:
                    # نجح! نكمل العملية
                    break
                else:
                    # فشل، نجرب التالي
                    try:
                        error_msg = response.json().get('error', 'خطأ غير معروف')
                    except:
                        error_msg = response.text[:200] if response.text else f'HTTP {response.status_code}'

                    last_error = f'HTTP {response.status_code}: {error_msg}'
                    last_url = full_url
                    continue

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                # خطأ في الاتصال، نجرب التالي
                last_error = str(e)
                last_url = f'{docgen_url}/api/generate'
                continue

            except Exception as e:
                # خطأ آخر، نجرب التالي
                last_error = f'{type(e).__name__}: {str(e)}'
                last_url = f'{docgen_url}/api/generate'
                continue

        # التحقق من نجاح أحد الـ URLs
        if response.status_code != 200:
            raise UserError(_(
                'فشل توليد PDF من جميع خوادم aadle_docgen\n'
                'آخر خطأ:\n'
                'URL: %s\n'
                'الخطأ: %s\n\n'
                'الخوادم المجربة: %s'
            ) % (last_url, last_error, ', '.join(docgen_urls)))

        # الحصول على PDF من الاستجابة
        pdf_content = response.content

        # حساب Hash للملف
        file_hash = hashlib.sha256(pdf_content).hexdigest()

        # توليد QR Code للتحقق
        qr_data = self._generate_qr_data(file_hash)
        qr_code_data = self._generate_qr_code(qr_data)

        # تحديد اسم الملف
        pdf_filename = f"{self.name}.pdf"

        # حفظ البيانات
        self.write({
            'pdf_file': base64.b64encode(pdf_content),
            'pdf_filename': pdf_filename,
            'file_hash': file_hash,
            'qr_code': qr_code_data,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('نجح'),
                'message': _('تم توليد ملف PDF بنجاح'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _safe_json_value(self, value):
        """
        تحويل القيمة إلى format آمن لـ JSON
        """
        # None و False يتم تحويلهما إلى فارغ
        if value is None:
            return None
        if value is False:
            return False

        # الأنواع الأساسية JSON-safe
        if isinstance(value, (int, float, str, bool)):
            return value

        # كائنات التاريخ والوقت (date, datetime)
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')

        # كائنات Odoo recordsets/models
        if hasattr(value, '_name') and hasattr(value, 'ensure_one'):
            # هذا recordset من Odoo
            if len(value) == 1:
                return value.name if hasattr(value, 'name') else str(value)
            elif len(value) > 1:
                return ', '.join([rec.name if hasattr(rec, 'name') else str(rec) for rec in value])
            else:
                return ''

        # أي شيء آخر نحوله إلى string
        return str(value)

    def _sanitize_data_for_json(self, data):
        """
        تنظيف البيانات بالكامل لتكون JSON-serializable
        """
        if isinstance(data, dict):
            return {k: self._sanitize_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_data_for_json(item) for item in data]
        else:
            return self._safe_json_value(data)

    def _prepare_document_data_for_pdf(self):
        """
        تحضير بيانات الوثيقة للإرسال إلى aadle_docgen
        """
        self.ensure_one()

        # بيانات أساسية
        data = {
            'document_name': self.name or '',
            'document_type': self.document_type_id.name if self.document_type_id else '',
            'document_type_fr': self.document_type_id.name_fr if self.document_type_id else '',
            'date_created': self._safe_json_value(self.date_created),
            'date_finalized': self._safe_json_value(self.date_finalized),
            'notary_name': self.notary_id.name if self.notary_id else '',
            'company_name': self.company_id.name if self.company_id else '',
            'company_address': self._get_company_address(),
            'partner_name': self.partner_id.name if self.partner_id else '',
            'price': float(self.price) if self.price else 0.0,
            'state': self.state or '',
        }

        # إضافة البيانات المخصصة من حقل data (JSON)
        if self.data:
            sanitized_custom_data = self._sanitize_data_for_json(self.data)
            data.update(sanitized_custom_data)

        # إضافة بيانات خاصة بنوع الوثيقة
        if self.document_type_id and self.document_type_id.code == 'marriage_contract':
            data.update(self._prepare_marriage_contract_data())
        elif self.document_type_id and self.document_type_id.code == 'divorce':
            data.update(self._prepare_divorce_data())
        # يمكن إضافة أنواع أخرى هنا

        # تنظيف نهائي للبيانات
        return self._sanitize_data_for_json(data)

    def _prepare_marriage_contract_data(self):
        """
        تحضير بيانات خاصة بعقد الزواج
        """
        self.ensure_one()
        data = self.data or {}

        # تحضير البيانات مع تنظيف التواريخ
        result = {
            # بيانات الزوج
            'husband_name_ar': data.get('husband_name_ar', ''),
            'husband_name_fr': data.get('husband_name_fr', ''),
            'husband_national_id': data.get('husband_national_id', ''),
            'husband_birthdate': self._safe_json_value(data.get('husband_birthdate', '')),
            'husband_birthplace': data.get('husband_birthplace', ''),
            'husband_address': data.get('husband_address', ''),
            'husband_phone': data.get('husband_phone', ''),
            'husband_father_name': data.get('husband_father_name', ''),
            'husband_mother_name': data.get('husband_mother_name', ''),

            # بيانات الزوجة
            'wife_name_ar': data.get('wife_name_ar', ''),
            'wife_name_fr': data.get('wife_name_fr', ''),
            'wife_national_id': data.get('wife_national_id', ''),
            'wife_birthdate': self._safe_json_value(data.get('wife_birthdate', '')),
            'wife_birthplace': data.get('wife_birthplace', ''),
            'wife_address': data.get('wife_address', ''),
            'wife_phone': data.get('wife_phone', ''),
            'wife_father_name': data.get('wife_father_name', ''),
            'wife_mother_name': data.get('wife_mother_name', ''),

            # بيانات الشهود
            'witness1_name': data.get('witness1_name', ''),
            'witness1_national_id': data.get('witness1_national_id', ''),
            'witness2_name': data.get('witness2_name', ''),
            'witness2_national_id': data.get('witness2_national_id', ''),

            # بيانات المهر
            'dowry_total': self._safe_json_value(data.get('dowry_total', 0)),
            'dowry_paid': self._safe_json_value(data.get('dowry_paid', 0)),
            'dowry_remaining': self._safe_json_value(
                float(self._safe_json_value(data.get('dowry_total', 0))) - 
                float(self._safe_json_value(data.get('dowry_paid', 0)))
            ),

            # بيانات إضافية
            'marriage_date': self._safe_json_value(data.get('marriage_date', '')),
            'marriage_place': data.get('marriage_place', ''),
            'notes': data.get('notes', ''),
        }
        
        # تنظيف نهائي
        return self._sanitize_data_for_json(result)

    def _prepare_divorce_data(self):
        """
        تحضير بيانات خاصة بعقد الطلاق
        """
        self.ensure_one()
        data = self.data or {}

        result = {
            'divorce_type': data.get('divorce_type', ''),
            'divorce_date': self._safe_json_value(data.get('divorce_date', '')),
            # أضف المزيد من الحقول حسب الحاجة
        }
        
        # تنظيف نهائي
        return self._sanitize_data_for_json(result)

    def _get_template_name(self):
        """
        الحصول على اسم القالب بناءً على نوع الوثيقة
        """
        self.ensure_one()

        template_mapping = {
            'marriage_contract': 'marriage_contract',
            'divorce': 'divorce',
            'power_of_attorney': 'power_of_attorney',
            'inheritance': 'inheritance',
            'sale_contract': 'sale_contract',
        }

        code = self.document_type_id.code if self.document_type_id else ''
        template = template_mapping.get(code, 'default')

        return template

    def _get_company_address(self):
        """
        الحصول على عنوان الشركة بشكل منسق
        """
        self.ensure_one()
        if not self.company_id:
            return ''

        company = self.company_id
        address_parts = []

        if company.street:
            address_parts.append(company.street)
        if company.city:
            address_parts.append(company.city)
        if company.country_id:
            address_parts.append(company.country_id.name)

        return ', '.join(address_parts)

    def _generate_qr_data(self, file_hash):
        """
        توليد البيانات التي سيتم وضعها في QR Code
        """
        self.ensure_one()

        # يمكن تخصيص البيانات حسب الحاجة
        # يمكن أن يكون رابط للتحقق من الوثيقة على موقع
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'http://localhost:8069'
        )

        verification_url = f"{base_url}/verify/{self.id}/{file_hash}"
        return verification_url

    def _generate_qr_code(self, data):
        """
        توليد QR Code وإرجاعه كـ Base64
        """
        # إنشاء QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # توليد صورة QR
        img = qr.make_image(fill_color="black", back_color="white")

        # تحويل إلى Base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return qr_base64
