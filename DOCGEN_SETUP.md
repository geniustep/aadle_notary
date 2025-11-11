# 🔧 إعداد aadle_docgen Service

## 📋 الإعدادات المطلوبة

يمكنك إعداد خدمة aadle_docgen من خلال إعدادات Odoo:

### 1. الوصول إلى الإعدادات

**الطريقة 1: من خلال Terminal**
```bash
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 odoo/odoo-bin shell -c /etc/odoo18.conf -d aadle --no-http"
```

**الطريقة 2: من خلال Odoo UI**
- اذهب إلى: **Settings → Technical → Parameters → System Parameters**
- أو استخدم XML-RPC/JSON-RPC

### 2. الإعدادات المتاحة

#### URLs
- `aadle.docgen_url`: URL الخادم الأساسي (افتراضي: `https://docgen.propanel.ma`)
- `aadle.docgen_fallback_url`: URL الخادم الاحتياطي (افتراضي: `http://64.226.110.81:5000`)

#### API Path
- `aadle.docgen_api_path`: المسار الصحيح للـ API endpoint (افتراضي: `/api/generate`)

#### Authentication
- `aadle.docgen_api_key`: API Key للـ authentication
- `aadle.docgen_api_token`: Bearer Token للـ authentication (يُستخدم كـ fallback)
- `aadle.docgen_auth_type`: نوع authentication (`bearer` أو `api_key`)

**ملاحظة مهمة:** إذا كان `auth_type = 'bearer'`، سيتم أخذ Bearer Token تلقائياً من جلسة المستخدم الحالي في Odoo. إذا لم يكن متاحاً، سيتم استخدام `aadle.docgen_api_token` من الإعدادات.

### 3. أمثلة على الإعداد

#### مثال 1: Bearer Token (من جلسة المستخدم تلقائياً)
```python
ICP = env['ir.config_parameter'].sudo()
ICP.set_param('aadle.docgen_api_path', '/api/v1/generate')
ICP.set_param('aadle.docgen_auth_type', 'bearer')
# لا حاجة لإعداد api_token - سيتم أخذه تلقائياً من جلسة المستخدم
# يمكن إضافة fallback token إذا لزم:
# ICP.set_param('aadle.docgen_api_token', 'fallback-token-here')
```

**أولوية Bearer Token:**
1. Session token من جلسة المستخدم الحالي (تلقائياً)
2. `aadle.docgen_api_token` من الإعدادات (fallback)
3. `aadle.docgen_api_key` كـ Bearer token (fallback آخر)

#### مثال 2: API Key
```python
ICP = env['ir.config_parameter'].sudo()
ICP.set_param('aadle.docgen_api_path', '/api/v1/generate')
ICP.set_param('aadle.docgen_api_key', 'your-api-key-here')
ICP.set_param('aadle.docgen_auth_type', 'api_key')
```

#### مثال 3: بدون Authentication
```python
ICP = env['ir.config_parameter'].sudo()
ICP.set_param('aadle.docgen_api_path', '/api/generate')
# لا حاجة لإعداد authentication
```

### 4. التحقق من الإعدادات

```python
ICP = env['ir.config_parameter'].sudo()
print(f"URL: {ICP.get_param('aadle.docgen_url')}")
print(f"API Path: {ICP.get_param('aadle.docgen_api_path', '/api/generate')}")
print(f"Auth Type: {ICP.get_param('aadle.docgen_auth_type', 'bearer')}")
print(f"Has Token: {bool(ICP.get_param('aadle.docgen_api_token'))}")
print(f"Has Key: {bool(ICP.get_param('aadle.docgen_api_key'))}")
```

## 🔍 اختبار الاتصال

بعد إعداد الإعدادات، يمكنك اختبار الاتصال من خلال:

1. فتح وثيقة في Odoo
2. الضغط على زر "توليد PDF"
3. مراقبة رسائل الخطأ (إذا فشل) للحصول على معلومات مفيدة

## 📝 ملاحظات

- إذا لم يتم تحديد `aadle.docgen_api_path`، سيتم استخدام `/api/generate` كافتراضي
- إذا تم تحديد `api_key` و `api_token` معاً، سيتم استخدام `api_token` أولاً
- إذا كان `auth_type` هو `bearer` وتم تحديد `api_key` فقط، سيتم استخدام `api_key` كـ Bearer token
- إذا كان `auth_type` هو `api_key`، سيتم إرسال API key في header `X-API-Key`

