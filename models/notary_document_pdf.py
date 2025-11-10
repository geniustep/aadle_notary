# -*- coding: utf-8 -*-
"""
إضافة method action_generate_pdf إلى notary.document model
يجب إضافة هذا الكود إلى: /opt/aadle/aadle_notary/models/notary_document.py
"""

import base64
import hashlib
import qrcode
import requests
import logging
from io import BytesIO
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


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
        يدعم FastAPI الجديد و Flask القديم
        """
        self.ensure_one()

        _logger.info("=" * 80)
        _logger.info(f"[PDF Generation] بدء عملية توليد PDF للوثيقة ID: {self.id}, Name: {self.name}")
        _logger.info(f"[PDF Generation] حالة الوثيقة: {self.state}")
        _logger.info(f"[PDF Generation] نوع الوثيقة: {self.document_type_id.name if self.document_type_id else 'غير محدد'}")

        # التحقق من أن الوثيقة مؤكدة
        if self.state not in ['confirmed', 'finalized']:
            _logger.warning(f"[PDF Generation] فشل: الوثيقة ليست مؤكدة (الحالة: {self.state})")
            raise UserError(_('لا يمكن توليد PDF إلا للوثائق المؤكدة أو المكتملة'))

        # الحصول على URL لخدمة aadle_docgen من الإعدادات
        ICP = self.env['ir.config_parameter'].sudo()
        primary_url = ICP.get_param('aadle.docgen_url', 'https://docgen.aadle.com')
        fallback_url = ICP.get_param('aadle.docgen_fallback_url', '')

        # الحصول على معلومات authentication
        api_key = ICP.get_param('aadle.docgen_api_key', '')
        api_token = ICP.get_param('aadle.docgen_api_token', '')
        auth_type = ICP.get_param('aadle.docgen_auth_type', 'bearer')  # 'bearer' or 'api_key'

        _logger.info(f"[PDF Generation] إعدادات الخادم:")
        _logger.info(f"[PDF Generation]   - Primary URL: {primary_url}")
        _logger.info(f"[PDF Generation]   - Fallback URL: {fallback_url or 'غير محدد'}")
        _logger.info(f"[PDF Generation]   - Auth Type: {auth_type}")
        _logger.info(f"[PDF Generation]   - API Key موجود: {'نعم' if api_key else 'لا'}")
        _logger.info(f"[PDF Generation]   - API Token موجود: {'نعم' if api_token else 'لا'}")

        # دالة مساعدة للحصول على session token من جلسة المستخدم الحالي
        def get_session_token():
            """الحصول على session token من جلسة المستخدم الحالي في Odoo"""
            try:
                # محاولة 1: من HTTP request (عند الاستدعاء من الويب)
                from odoo import http
                if hasattr(http, 'request') and http.request:
                    session_id = getattr(http.request.session, 'session_id', None)
                    if session_id:
                        return session_id
            except Exception:
                pass

            try:
                # محاولة 2: من context إذا كان متاحاً
                if self.env.context.get('session_id'):
                    return self.env.context.get('session_id')
            except Exception:
                pass

            # محاولة 3: من request object مباشرة
            try:
                import odoo.http as http_module
                request = getattr(http_module, 'request', None)
                if request and hasattr(request, 'session'):
                    return getattr(request.session, 'session_id', None)
            except Exception:
                pass

            return None

        # قائمة الـ URLs للتجربة بالترتيب (إزالة التكرار)
        docgen_urls = []
        for url in [primary_url, fallback_url]:
            if url and url.strip() and url.strip() not in docgen_urls:
                docgen_urls.append(url.strip())

        # إذا لم تكن هناك خوادم، استخدم الافتراضي
        if not docgen_urls:
            docgen_urls = ['https://docgen.aadle.com']

        # تحضير البيانات للإرسال إلى aadle_docgen
        _logger.info(f"[PDF Generation] تحضير بيانات الوثيقة...")
        document_data = self._prepare_document_data_for_pdf()
        _logger.info(f"[PDF Generation] تم تحضير البيانات: {len(str(document_data))} حرف")

        # الحصول على template_id من نوع الوثيقة
        if not self.document_type_id:
            _logger.error(f"[PDF Generation] ❌ فشل: نوع الوثيقة غير محدد")
            raise UserError(_('يجب تحديد نوع الوثيقة أولاً'))
        
        # محاولة استخدام template_id من قاعدة البيانات أولاً
        template_id = self.document_type_id.template_id
        template_name_fallback = self._get_template_name()
        
        # إذا لم يكن template_id موجوداً، استخدم template_name كـ fallback
        if not template_id:
            _logger.warning(f"[PDF Generation] ⚠️  template_id غير موجود، استخدام template_name: {template_name_fallback}")
            template_id = template_name_fallback
        else:
            _logger.info(f"[PDF Generation] ✅ template_id: {template_id}")

        # تنظيف إضافي للبيانات قبل الإرسال (ضمان JSON serialization)
        _logger.info(f"[PDF Generation] تم تنظيف البيانات للـ JSON")
        sanitized_data = self._sanitize_data_for_json(document_data)

        # متغيرات لحفظ آخر خطأ
        last_error = None
        last_url = None
        response = None
        success = False

        # محاولة كل URL بالترتيب
        _logger.info(f"[PDF Generation] بدء محاولة الاتصال بالخوادم ({len(docgen_urls)} خادم)")
        for idx, docgen_url in enumerate(docgen_urls, 1):
            try:
                # تنظيف URL
                docgen_url = docgen_url.strip().rstrip('/')
                _logger.info(f"[PDF Generation] محاولة {idx}/{len(docgen_urls)}: {docgen_url}")

                # تحديد endpoint و payload بناءً على نوع الخادم
                # FastAPI الجديد (docgen.aadle.com)
                # API الصحيح: POST /docs/render (حسب OpenAPI schema)
                if 'docgen.aadle.com' in docgen_url:
                    endpoint = f'{docgen_url}/docs/render'
                    payload = {
                        'template_id': template_id,
                        'data': sanitized_data,
                        'include_qr': True,
                        'include_signature': True
                    }
                    _logger.info(f"[PDF Generation]   - نوع الخادم: FastAPI")
                    _logger.info(f"[PDF Generation]   - Endpoint: {endpoint}")
                    _logger.info(f"[PDF Generation]   - Template ID: {template_id}")
                else:
                    # Flask القديم (localhost:5000 أو IP:5000)
                    endpoint = f'{docgen_url}/api/generate'
                    payload = {
                        'template': template_id,
                        'data': sanitized_data,
                        'format': 'pdf',
                    }
                    _logger.info(f"[PDF Generation]   - نوع الخادم: Flask")
                    _logger.info(f"[PDF Generation]   - Endpoint: {endpoint}")
                    _logger.info(f"[PDF Generation]   - Template: {template_id}")

                # إعداد headers
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Odoo-Notary-Document/1.0',
                    'Accept': 'application/json',
                }

                # إضافة authentication headers
                if auth_type == 'bearer':
                    # محاولة الحصول على session token من جلسة المستخدم الحالي
                    current_session_token = get_session_token()
                    _logger.info(f"[PDF Generation]   - Session Token: {'موجود' if current_session_token else 'غير موجود'}")

                    # استخدام session token إذا كان متاحاً، وإلا استخدام api_token من الإعدادات
                    token_to_use = current_session_token or api_token
                    if token_to_use:
                        headers['Authorization'] = f'Bearer {token_to_use}'
                        _logger.info(f"[PDF Generation]   - استخدام Bearer Token")
                elif auth_type == 'api_key' and api_key:
                    headers['X-API-Key'] = api_key
                    _logger.info(f"[PDF Generation]   - استخدام API Key")
                elif api_key:  # fallback: استخدام api_key كـ Bearer token
                    headers['Authorization'] = f'Bearer {api_key}'
                    _logger.info(f"[PDF Generation]   - استخدام API Key كـ Bearer (fallback)")

                # استدعاء خدمة aadle_docgen مع timeout أطول
                _logger.info(f"[PDF Generation]   - إرسال الطلب إلى {endpoint}...")
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=(10, 60),  # (connect timeout, read timeout)
                    verify=True  # التحقق من SSL
                )
                _logger.info(f"[PDF Generation]   - استجابة HTTP: {response.status_code}")

                if response.status_code == 200:
                    # نجح! نكمل العملية
                    _logger.info(f"[PDF Generation] ✅ نجح الاتصال بالخادم: {docgen_url}")
                    success = True
                    break
                else:
                    # فشل، نجرب التالي
                    try:
                        error_msg = response.json().get('error') or response.json().get('detail', 'خطأ غير معروف')
                    except:
                        error_msg = response.text[:200] if response.text else f'HTTP {response.status_code}'
                    last_error = f'HTTP {response.status_code}: {error_msg}'
                    last_url = endpoint
                    _logger.warning(f"[PDF Generation] ❌ فشل الطلب: {last_error}")
                    continue

            except requests.exceptions.SSLError as e:
                last_error = f'SSL Error: {str(e)}'
                last_url = docgen_url
                _logger.error(f"[PDF Generation] ❌ خطأ SSL: {str(e)}")
                continue
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_error = str(e)
                last_url = docgen_url
                _logger.error(f"[PDF Generation] ❌ خطأ اتصال/Timeout: {str(e)}")
                continue
            except Exception as e:
                last_error = f'{type(e).__name__}: {str(e)}'
                last_url = docgen_url
                _logger.error(f"[PDF Generation] ❌ خطأ غير متوقع: {type(e).__name__}: {str(e)}", exc_info=True)
                continue

        # التحقق من نجاح أحد الـ URLs
        if not success or not response or response.status_code != 200:
            _logger.error(f"[PDF Generation] ❌ فشل توليد PDF من جميع الخوادم")
            # تحسين رسالة الخطأ
            error_details = []
            error_details.append(_('فشل توليد PDF من جميع خوادم aadle_docgen'))
            error_details.append('')
            error_details.append(_('الخوادم المجربة:'))
            for url in docgen_urls:
                error_details.append(f'  - {url}')
            error_details.append('')

            if last_url and last_error:
                error_details.append(_('آخر خطأ:'))
                error_details.append(f'  URL: {last_url}')
                error_details.append(f'  الخطأ: {last_error}')
            else:
                error_details.append(_('لم يتم الوصول إلى أي خادم'))

            error_details.append('')
            error_details.append(_('يرجى التحقق من:'))
            error_details.append(_('  1. اتصال الإنترنت'))
            error_details.append(_('  2. إعدادات aadle.docgen_url و aadle.docgen_fallback_url'))
            error_details.append(_('  3. حالة الخوادم'))

            # التحقق من authentication
            current_session_token = get_session_token()
            if current_session_token:
                error_details.append(_('  4. ✅ Bearer Token: تم إرساله من جلسة المستخدم'))
            elif api_token:
                error_details.append(_('  4. ✅ Bearer Token: موجود في الإعدادات'))
            elif api_key:
                error_details.append(_('  4. ✅ API Key: موجود في الإعدادات'))
            else:
                error_details.append(_('  4. ⚠️  لا توجد معلومات authentication في الإعدادات'))

            raise UserError('\n'.join(error_details))

        # الحصول على PDF من الاستجابة
        _logger.info(f"[PDF Generation] معالجة استجابة الخادم...")
        try:
            response_data = response.json()
            _logger.info(f"[PDF Generation] نوع الاستجابة: JSON")
            
            # FastAPI يرجع pdf_url و sha256، بينما Flask القديم يرجع PDF مباشرة
            if 'pdf_url' in response_data:
                # FastAPI - تحميل PDF من URL
                pdf_url = response_data['pdf_url']
                _logger.info(f"[PDF Generation] تحميل PDF من URL: {pdf_url}")
                pdf_response = requests.get(pdf_url, timeout=30)
                if pdf_response.status_code != 200:
                    _logger.error(f"[PDF Generation] ❌ فشل تحميل PDF من URL: HTTP {pdf_response.status_code}")
                    raise UserError(_('فشل تحميل PDF من الخادم'))
                pdf_content = pdf_response.content
                file_hash = response_data.get('sha256', hashlib.sha256(pdf_content).hexdigest())
                _logger.info(f"[PDF Generation] ✅ تم تحميل PDF: {len(pdf_content)} بايت")
            else:
                # Flask القديم - PDF في الاستجابة مباشرة
                _logger.info(f"[PDF Generation] PDF في الاستجابة مباشرة (Flask)")
                pdf_content = response.content
                file_hash = hashlib.sha256(pdf_content).hexdigest()
                _logger.info(f"[PDF Generation] ✅ تم استخراج PDF: {len(pdf_content)} بايت")
        except ValueError:
            # إذا لم يكن JSON، افترض أن الاستجابة هي PDF مباشرة
            _logger.info(f"[PDF Generation] الاستجابة ليست JSON، افتراض PDF مباشر")
            pdf_content = response.content
            file_hash = hashlib.sha256(pdf_content).hexdigest()
            _logger.info(f"[PDF Generation] ✅ تم استخراج PDF: {len(pdf_content)} بايت")

        # حساب Hash للملف (إذا لم يكن موجوداً)
        if not file_hash:
            file_hash = hashlib.sha256(pdf_content).hexdigest()
        _logger.info(f"[PDF Generation] Hash الملف: {file_hash}")

        # توليد QR Code للتحقق
        _logger.info(f"[PDF Generation] توليد QR Code...")
        qr_data = self._generate_qr_data(file_hash)
        qr_code_data = self._generate_qr_code(qr_data)
        _logger.info(f"[PDF Generation] ✅ تم توليد QR Code")

        # تحديد اسم الملف
        pdf_filename = f"{self.name}.pdf"
        _logger.info(f"[PDF Generation] اسم الملف: {pdf_filename}")

        # حفظ البيانات
        _logger.info(f"[PDF Generation] حفظ البيانات في قاعدة البيانات...")
        self.write({
            'pdf_file': base64.b64encode(pdf_content),
            'pdf_filename': pdf_filename,
            'file_hash': file_hash,
            'qr_code': qr_code_data,
        })
        _logger.info(f"[PDF Generation] ✅ تم حفظ البيانات بنجاح")

        # إبطال التخزين المؤقت لضمان تحديث البيانات
        self.invalidate_recordset(['pdf_file', 'pdf_filename', 'file_hash', 'qr_code'])

        # إضافة رسالة في السجل (Chatter)
        self.message_post(
            body=_('تم توليد ملف PDF بنجاح: %s') % pdf_filename,
            subject=_('توليد PDF'),
        )
        _logger.info(f"[PDF Generation] ✅ تم إضافة رسالة في Chatter")

        _logger.info(f"[PDF Generation] ✅✅✅ تم إكمال عملية توليد PDF بنجاح! ✅✅✅")
        _logger.info("=" * 80)

        # إعادة تحميل الصفحة لعرض الملف مباشرة
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
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
        تحضير بيانات خاصة بعقد الزواج - متوافق مع القالب المغربي
        """
        self.ensure_one()
        data = self.data or {}

        # تحضير البيانات مع تنظيف التواريخ
        result = {
            # ========== معلومات المحكمة ==========
            'court': {
                'name': data.get('court_name', self.company_id.name if self.company_id else ''),
                'type': data.get('court_type', 'الابتدائية'),
                'city': data.get('court_city', self.company_id.city if self.company_id else ''),
            },

            # ========== معلومات الوثيقة ==========
            'document': {
                'number': self.name or '',
                'page': data.get('document_page', ''),
                'registry': data.get('document_registry', ''),
                'date': self._safe_json_value(self.date_created),
            },

            # ========== معلومات العدول ==========
            'notary': {
                'first': data.get('notary_first', self.notary_id.name if self.notary_id else ''),
                'second': data.get('notary_second', ''),
            },

            # ========== معلومات المذكرة ==========
            'memo': {
                'number': data.get('memo_number', ''),
                'record': data.get('memo_record', ''),
                'page': data.get('memo_page', ''),
            },

            # ========== معلومات الوقت ==========
            'time': {
                'hour': data.get('time_hour', self._get_current_time_hour()),
                'period': data.get('time_period', self._get_current_time_period()),
            },

            # ========== معلومات التاريخ ==========
            'date': {
                'day': data.get('date_day', self._get_day_name()),
                'hijri': data.get('date_hijri', self._get_hijri_date()),
                'gregorian': data.get('date_gregorian', self._safe_json_value(self.date_created)),
            },

            # ========== معلومات الترخيص ==========
            'authorization': {
                'number': data.get('authorization_number', ''),
                'date': self._safe_json_value(data.get('authorization_date', '')),
            },

            # ========== معلومات الملف ==========
            'file': {
                'number': data.get('file_number', ''),
            },

            # ========== بيانات الزوج (groom) ==========
            'groom': {
                'name': data.get('groom_name', data.get('husband_name_ar', '')),
                'birthplace': data.get('groom_birthplace', data.get('husband_birthplace', '')),
                'district': data.get('groom_district', ''),
                'province': data.get('groom_province', ''),
                'birth_year': data.get('groom_birth_year', self._extract_year(data.get('husband_birthdate', ''))),
                'father': data.get('groom_father', data.get('husband_father_name', '')),
                'mother': data.get('groom_mother', data.get('husband_mother_name', '')),
                'birth_certificate': data.get('groom_birth_certificate', ''),
                'commune': data.get('groom_commune', ''),
                'national_id': data.get('groom_national_id', data.get('husband_national_id', '')),
                'occupation': data.get('groom_occupation', ''),
                'marital_status': data.get('groom_marital_status', 'أعزب'),
                'certificate_number': data.get('groom_certificate_number', ''),
                'certificate_commune': data.get('groom_certificate_commune', ''),
                'certificate_province': data.get('groom_certificate_province', ''),
                'address': data.get('groom_address', data.get('husband_address', '')),
            },

            # ========== بيانات الزوجة (bride) ==========
            'bride': {
                'name': data.get('bride_name', data.get('wife_name_ar', '')),
                'birthplace': data.get('bride_birthplace', data.get('wife_birthplace', '')),
                'district': data.get('bride_district', ''),
                'birth_year': data.get('bride_birth_year', self._extract_year(data.get('wife_birthdate', ''))),
                'father': data.get('bride_father', data.get('wife_father_name', '')),
                'mother': data.get('bride_mother', data.get('wife_mother_name', '')),
                'birth_certificate': data.get('bride_birth_certificate', ''),
                'commune': data.get('bride_commune', ''),
                'residence_certificate': data.get('bride_residence_certificate', ''),
                'leadership': data.get('bride_leadership', ''),
                'occupation': data.get('bride_occupation', ''),
                'marital_status': data.get('bride_marital_status', 'عزباء'),
                'certificate_number': data.get('bride_certificate_number', ''),
                'certificate_commune': data.get('bride_certificate_commune', ''),
                'certificate_district': data.get('bride_certificate_district', ''),
                'address': data.get('bride_address', data.get('wife_address', '')),
                'province': data.get('bride_province', ''),
            },

            # ========== بيانات المهر (dowry) ==========
            'dowry': {
                'amount_text': data.get('dowry_amount_text', self._number_to_arabic_text(data.get('dowry_total', 0))),
                'amount_number': self._safe_json_value(data.get('dowry_total', 0)),
            },

            # ========== البيانات القديمة للتوافق مع الأنظمة القديمة ==========
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

            # بيانات المهر (النسخة القديمة)
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

    def _get_current_time_hour(self):
        """
        الحصول على الساعة الحالية
        """
        now = datetime.now()
        return now.strftime('%I:%M')  # صيغة 12 ساعة

    def _get_current_time_period(self):
        """
        الحصول على فترة اليوم (صباحا/مساء)
        """
        now = datetime.now()
        hour = now.hour

        if hour < 12:
            return 'صباحا'
        else:
            return 'مساء'

    def _get_day_name(self):
        """
        الحصول على اسم اليوم بالعربية
        """
        # أيام الأسبوع بالعربية
        arabic_days = {
            0: 'الاثنين',
            1: 'الثلاثاء',
            2: 'الأربعاء',
            3: 'الخميس',
            4: 'الجمعة',
            5: 'السبت',
            6: 'الأحد',
        }

        today = datetime.now().weekday()
        return arabic_days.get(today, '')

    def _get_hijri_date(self):
        """
        الحصول على التاريخ الهجري
        ملاحظة: يتطلب تثبيت مكتبة hijri-converter
        pip install hijri-converter
        """
        try:
            from hijri_converter import Gregorian
            now = datetime.now()
            hijri = Gregorian(now.year, now.month, now.day).to_hijri()

            # أسماء الشهور الهجرية
            hijri_months = [
                '', 'محرم', 'صفر', 'ربيع الأول', 'ربيع الثاني', 'جمادى الأولى',
                'جمادى الثانية', 'رجب', 'شعبان', 'رمضان', 'شوال',
                'ذو القعدة', 'ذو الحجة'
            ]

            month_name = hijri_months[hijri.month] if hijri.month <= len(hijri_months) else ''
            return f'{hijri.day} {month_name} {hijri.year}'

        except ImportError:
            # إذا لم تكن المكتبة مثبتة، نرجع تنسيق افتراضي
            _logger.warning("hijri-converter library not installed. Install it with: pip install hijri-converter")
            return 'يرجى تثبيت hijri-converter'
        except Exception as e:
            _logger.error(f"Error converting to Hijri date: {str(e)}")
            return ''

    def _extract_year(self, date_value):
        """
        استخراج السنة من تاريخ
        """
        if not date_value:
            return ''

        # إذا كان string
        if isinstance(date_value, str):
            # محاولة استخراج السنة من التاريخ بصيغة YYYY-MM-DD
            if len(date_value) >= 4:
                return date_value[:4]

        # إذا كان date أو datetime
        if hasattr(date_value, 'year'):
            return str(date_value.year)

        return ''

    def _number_to_arabic_text(self, number):
        """
        تحويل رقم إلى نص عربي
        مثال: 50000 => خمسون ألف
        """
        try:
            number = float(number)

            # للأرقام الصغيرة، يمكنك إضافة منطق التحويل الكامل
            # هنا نستخدم تحويل بسيط

            ones = ['', 'واحد', 'اثنان', 'ثلاثة', 'أربعة', 'خمسة', 'ستة', 'سبعة', 'ثمانية', 'تسعة']
            tens = ['', 'عشرة', 'عشرون', 'ثلاثون', 'أربعون', 'خمسون', 'ستون', 'سبعون', 'ثمانون', 'تسعون']
            hundreds = ['', 'مئة', 'مئتان', 'ثلاثمئة', 'أربعمئة', 'خمسمئة', 'ستمئة', 'سبعمئة', 'ثمانمئة', 'تسعمئة']

            if number == 0:
                return 'صفر'

            if number < 0:
                return 'سالب ' + self._number_to_arabic_text(abs(number))

            # تحويل بسيط للأرقام الشائعة
            num_int = int(number)

            # للأرقام الكبيرة، نستخدم تنسيق بسيط
            if num_int >= 1000000:
                millions = num_int // 1000000
                rest = num_int % 1000000
                result = self._number_to_arabic_text(millions) + ' مليون'
                if rest > 0:
                    result += ' و' + self._number_to_arabic_text(rest)
                return result

            if num_int >= 1000:
                thousands = num_int // 1000
                rest = num_int % 1000
                result = self._number_to_arabic_text(thousands) + ' ألف'
                if rest > 0:
                    result += ' و' + self._number_to_arabic_text(rest)
                return result

            if num_int >= 100:
                hundred = num_int // 100
                rest = num_int % 100
                result = hundreds[hundred]
                if rest > 0:
                    result += ' و' + self._number_to_arabic_text(rest)
                return result

            if num_int >= 20:
                ten = num_int // 10
                rest = num_int % 10
                result = tens[ten]
                if rest > 0:
                    result += ' و' + ones[rest]
                return result

            if num_int >= 11:
                # الأعداد من 11 إلى 19
                special = ['', 'أحد عشر', 'اثنا عشر', 'ثلاثة عشر', 'أربعة عشر', 'خمسة عشر',
                          'ستة عشر', 'سبعة عشر', 'ثمانية عشر', 'تسعة عشر']
                return special[num_int - 10]

            if num_int == 10:
                return 'عشرة'

            return ones[num_int]

        except Exception as e:
            _logger.error(f"Error converting number to Arabic text: {str(e)}")
            return str(number)

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
