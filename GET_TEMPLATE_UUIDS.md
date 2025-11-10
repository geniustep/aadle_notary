# 🔧 دليل الحصول على UUIDs من aadle_docgen

## 📋 الخطوات المطلوبة

### 🔧 الخطوة #1: الحصول على UUIDs من API

#### الطريقة 1: من Terminal

```bash
# محاولة 1: endpoint مباشر
curl https://docgen.aadle.com/templates

# محاولة 2: مع authentication
curl -H "Authorization: Bearer YOUR_TOKEN" https://docgen.aadle.com/templates

# محاولة 3: API path مختلف
curl https://docgen.aadle.com/api/templates
```

#### الطريقة 2: استخدام Python Script

```bash
cd /opt/odoo18/custom_models/aadle_notary/scripts
python3 get_templates_from_docgen.py
```

#### الطريقة 3: من Odoo Shell

```python
# فتح Odoo Shell
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 odoo/odoo-bin shell -c /etc/odoo18.conf -d aadle --no-http"

# في Shell:
exec(open('/opt/odoo18/custom_models/aadle_notary/scripts/get_templates_from_docgen.py').read())
templates = get_templates_from_api('https://docgen.aadle.com', auth_token='YOUR_TOKEN')
print(templates)
```

---

### 🔧 الخطوة #2: الحصول على UUIDs من واجهة aadle_docgen

1. افتح المتصفح واذهب إلى: **https://docgen.aadle.com/docs**
2. اعرض قائمة القوالب (Templates)
3. انسخ UUID لكل قالب
4. استخدم UUIDs لتحديث قاعدة البيانات

---

### 🔧 الخطوة #3: تحديث قاعدة البيانات

#### الطريقة 1: من Odoo Shell (تلقائي)

```python
# فتح Odoo Shell
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 odoo/odoo-bin shell -c /etc/odoo18.conf -d aadle --no-http"

# في Shell:
exec(open('/opt/odoo18/custom_models/aadle_notary/scripts/get_templates_from_docgen.py').read())
templates = get_templates_from_api('https://docgen.aadle.com')
update_odoo_template_ids(env, templates, interactive=True)
```

#### الطريقة 2: من Odoo Shell (يدوي)

```python
# فتح Odoo Shell
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 odoo/odoo-bin shell -c /etc/odoo18.conf -d aadle --no-http"

# في Shell:
exec(open('/opt/odoo18/custom_models/aadle_notary/scripts/update_template_ids_manual.py').read())

# تحديث UUIDs (استبدل بـ UUIDs الفعلية)
set_template_id(env, 'marriage_contract', 'uuid-actual-here')
set_template_id(env, 'divorce', 'uuid-actual-here')
set_template_id(env, 'power_of_attorney', 'uuid-actual-here')
set_template_id(env, 'inheritance', 'uuid-actual-here')
set_template_id(env, 'sale_contract', 'uuid-actual-here')
```

#### الطريقة 3: من Odoo UI

1. افتح **Settings → Technical → Database Structure → Models**
2. ابحث عن `notary.document.type`
3. افتح كل نوع وثيقة
4. أضف `template_id` (UUID) في الحقل المخصص

#### الطريقة 4: من SQL

```sql
-- استبدل UUIDs بـ UUIDs الفعلية
UPDATE notary_document_type 
SET template_id = 'uuid-actual-here'
WHERE code = 'marriage_contract';

UPDATE notary_document_type 
SET template_id = 'uuid-actual-here'
WHERE code = 'divorce';

-- وهكذا لباقي الأنواع...
```

---

### 🔧 الخطوة #4: إنشاء القوالب في aadle_docgen (إذا لم تكن موجودة)

إذا لم تكن القوالب موجودة في aadle_docgen، يجب إنشاؤها أولاً:

#### من API:

```bash
# إنشاء قالب جديد
curl -X POST https://docgen.aadle.com/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "عقد الزواج",
    "code": "marriage_contract",
    "template_content": "..."
  }'

# الحصول على UUID من الاستجابة
```

#### من واجهة aadle_docgen:

1. افتح **https://docgen.aadle.com/docs**
2. اذهب إلى قسم Templates
3. اضغط على "Create Template"
4. أدخل بيانات القالب
5. انسخ UUID من الاستجابة

---

## 📊 ملخص المشكلة الحالية

| الجزء | الحالي (خطأ) | المطلوب (صحيح) |
|-------|--------------|-----------------|
| **Endpoint** | `/api/generate` | `/docs/render` ✅ |
| **معرف القالب** | `'template': 'marriage_contract'` | `'template_id': 'uuid-string'` ✅ |
| **حقل format** | `'format': 'pdf'` | (غير مطلوب - تم حذفه) ✅ |
| **template_id في DB** | فارغ (NULL) | **يجب ملؤه بـ UUIDs صحيحة** ⚠️ |
| **Authentication** | موجود | موجود ✅ |

---

## ✅ التحقق من التغييرات

### اختبار API مباشرة:

```bash
# اختبار endpoint
curl -X POST https://docgen.aadle.com/docs/render \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "template_id": "your-uuid-here",
    "data": {"test": "data"},
    "include_qr": true,
    "include_signature": true
  }'
```

### التحقق من قاعدة البيانات:

```python
# من Odoo Shell
env['notary.document.type'].search([]).read(['name', 'code', 'template_id'])
```

---

## 🚨 نقاط مهمة

1. **الخطأ "Template not found"** يحدث لأن:
   - ✅ Endpoint تم تصحيحه (`/docs/render`)
   - ⚠️ `template_id` فارغ في قاعدة البيانات - **يجب ملؤه**

2. **الأولوية:**
   - ✅ أولاً: تصحيح الكود (تم ✅)
   - ⚠️ ثانياً: ملء `template_id` في قاعدة البيانات (**مطلوب الآن**)
   - ✅ ثالثاً: التحقق من Authentication (موجود ✅)

3. **بعد إضافة UUIDs:**
   - اختبر توليد PDF من Odoo
   - تحقق من أن القالب موجود في aadle_docgen
   - تحقق من أن Authentication يعمل

---

## 📁 الملفات المتاحة

1. **`scripts/get_templates_from_docgen.py`**: Script للحصول على القوالب من API
2. **`scripts/update_template_ids_manual.py`**: Script لتحديث template_id يدوياً
3. **`sql/update_template_ids.sql`**: SQL script لتحديث template_id

---

## 💡 نصائح

1. **احفظ UUIDs في مكان آمن** - ستحتاجها لاحقاً
2. **اختبر كل قالب** بعد إضافته
3. **راجع logs** إذا واجهت مشاكل
4. **استخدم Bearer Token** من جلسة Odoo تلقائياً

---

## 📞 الدعم

إذا واجهت مشاكل:
1. تحقق من أن aadle_docgen يعمل: `curl https://docgen.aadle.com/docs`
2. تحقق من Authentication
3. راجع رسائل الخطأ في Odoo logs
4. تأكد من أن UUIDs صحيحة

