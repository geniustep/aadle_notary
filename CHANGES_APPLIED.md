# ✅ التغييرات المطبقة - notary_document_pdf.py

## 📋 ملخص التغييرات

تم تطبيق جميع التغييرات المطلوبة بنجاح.

---

## ✅ التغيير #1: استخدام template_id من document_type_id

### قبل:
```python
template_name = self._get_template_name()
```

### بعد:
```python
# الحصول على template_id من نوع الوثيقة
if not self.document_type_id:
    raise UserError(_('يجب تحديد نوع الوثيقة أولاً'))

template_id = self.document_type_id.template_id
if not template_id:
    raise UserError(_(
        'لم يتم تعيين معرّف القالب (template_id) لنوع الوثيقة "%s"\n'
        'يرجى إضافته في إعدادات أنواع الوثائق'
    ) % self.document_type_id.name)
```

**الموقع:** السطور 90-99

---

## ✅ التغيير #2: تحديث Payload للـ FastAPI

### قبل:
```python
payload = {
    'template_id': template_name,  # ❌ كان يستخدم template_name
    'data': sanitized_data,
    'include_qr': True,
    'include_signature': True
}
```

### بعد:
```python
payload = {
    'template_id': template_id,  # ✅ يستخدم template_id من document_type_id
    'data': sanitized_data,
    'include_qr': True,
    'include_signature': True
}
```

**الموقع:** السطور 120-125

---

## ✅ التغيير #3: Flask Fallback

### الكود الحالي:
```python
else:
    # Flask القديم (localhost:5000 أو IP:5000)
    # استخدام template_id أو fallback إلى template_name
    endpoint = f'{docgen_url}/api/generate'
    template_name_fallback = self._get_template_name()
    payload = {
        'template': template_id or template_name_fallback,
        'data': sanitized_data,
        'format': 'pdf',
    }
```

**الموقع:** السطور 126-136

**ملاحظة:** `_get_template_name()` لا تزال مستخدمة كـ fallback للـ Flask القديم.

---

## ✅ التغيير #4: Authentication

### الكود الحالي:
```python
# إعداد headers
headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Odoo-Notary-Document/1.0',
    'Accept': 'application/json',
}

# إضافة authentication headers
if auth_type == 'bearer':
    current_session_token = get_session_token()
    token_to_use = current_session_token or api_token
    if token_to_use:
        headers['Authorization'] = f'Bearer {token_to_use}'
elif auth_type == 'api_key' and api_key:
    headers['X-API-Key'] = api_key
elif api_key:  # fallback
    headers['Authorization'] = f'Bearer {api_key}'
```

**الموقع:** السطور 138-146

**ملاحظة:** Authentication موجود بالفعل ومحسّن.

---

## 📊 مقارنة Endpoints

| الخادم | Endpoint | Payload |
|--------|----------|---------|
| **FastAPI** (`docgen.propanel.ma`) | `/docs/render` | `template_id`, `data`, `include_qr`, `include_signature` |
| **Flask** (localhost/IP:5000) | `/api/generate` | `template` (template_id أو template_name), `data`, `format` |

---

## ⚠️ الخطوات المطلوبة بعد التحديث

### 1. إضافة template_id لأنواع الوثائق

يجب إضافة `template_id` (UUID) لكل نوع وثيقة في قاعدة البيانات.

**الطرق المتاحة:**
- ✅ من Odoo UI: Settings → Technical → Database Structure → Models → `notary.document.type`
- ✅ من Odoo Shell: راجع `TEMPLATE_ID_SETUP.md`
- ✅ من SQL: راجع `sql/update_template_ids.sql`

### 2. الحصول على UUIDs من aadle_docgen

يجب الحصول على UUIDs الفعلية من نظام `aadle_docgen` لكل قالب.

---

## 📁 الملفات المضافة

1. **`sql/update_template_ids.sql`**: SQL script لتحديث template_id
2. **`TEMPLATE_ID_SETUP.md`**: دليل شامل لإعداد template_id
3. **`CHANGES_APPLIED.md`**: هذا الملف - ملخص التغييرات

---

## 🔍 التحقق من التطبيق

### من Odoo Shell:
```python
# التحقق من وجود template_id
env['notary.document.type'].search([]).read(['name', 'code', 'template_id'])
```

### اختبار توليد PDF:
1. افتح وثيقة في Odoo
2. اضغط على زر "توليد PDF"
3. إذا لم يكن `template_id` موجوداً، ستحصل على رسالة خطأ واضحة

---

## ✅ الحالة الحالية

- ✅ الكود محدث ويستخدم `template_id`
- ✅ التحقق من وجود `template_id` قبل الإرسال
- ✅ FastAPI endpoint: `/docs/render`
- ✅ Flask fallback: `/api/generate`
- ✅ Authentication محسّن
- ✅ رسائل خطأ واضحة
- ⚠️ **مطلوب:** إضافة `template_id` لكل نوع وثيقة

---

## 📞 الدعم

إذا واجهت مشاكل:
1. راجع `TEMPLATE_ID_SETUP.md` للتعليمات
2. تحقق من وجود `template_id` في قاعدة البيانات
3. راجع رسائل الخطأ في Odoo logs

