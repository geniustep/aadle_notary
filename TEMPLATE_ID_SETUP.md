# 📋 دليل إعداد template_id لأنواع الوثائق

## 🎯 الهدف

بعد التحديثات الأخيرة، أصبح الكود يستخدم `template_id` من `notary.document.type` بدلاً من `template_name`. يجب إضافة `template_id` لكل نوع وثيقة في قاعدة البيانات.

---

## ✅ التغييرات المطبقة

### 1. استخدام `template_id` من `document_type_id.template_id`
- ✅ تم تحديث الكود لاستخدام `template_id` مباشرة من نوع الوثيقة
- ✅ إضافة التحقق من وجود `template_id` قبل الإرسال
- ✅ رسالة خطأ واضحة إذا لم يكن `template_id` موجوداً

### 2. FastAPI Endpoint
- ✅ Endpoint: `/docs/render`
- ✅ Payload: `template_id` و `data`

### 3. Flask القديم (Fallback)
- ✅ Endpoint: `/api/generate`
- ✅ Payload: `template` (يستخدم `template_id` أو `template_name` كـ fallback)

---

## 🔧 كيفية إضافة template_id

### الطريقة 1: من Odoo UI

1. افتح **Settings → Technical → Database Structure → Models**
2. ابحث عن `notary.document.type`
3. افتح كل نوع وثيقة
4. أضف `template_id` في الحقل المخصص

### الطريقة 2: من Odoo Shell

```python
# فتح Odoo Shell
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 odoo/odoo-bin shell -c /etc/odoo18.conf -d aadle --no-http"

# في Shell:
env = env  # أو استخدم env الموجود

# الحصول على أنواع الوثائق
doc_types = env['notary.document.type'].search([])

# تحديث template_id لكل نوع
marriage = env['notary.document.type'].search([('code', '=', 'marriage_contract')], limit=1)
if marriage:
    marriage.template_id = 'uuid-for-marriage-contract'  # ⚠️ استبدل بـ UUID الفعلي

divorce = env['notary.document.type'].search([('code', '=', 'divorce')], limit=1)
if divorce:
    divorce.template_id = 'uuid-for-divorce'  # ⚠️ استبدل بـ UUID الفعلي

# وهكذا لباقي الأنواع...
```

### الطريقة 3: من SQL مباشرة

```sql
-- استخدام ملف sql/update_template_ids.sql
-- ⚠️ استبدل UUIDs بـ UUIDs الفعلية من نظام aadle_docgen

UPDATE notary_document_type 
SET template_id = 'uuid-for-marriage-contract'
WHERE code = 'marriage_contract';
```

---

## 📋 قائمة template_id المطلوبة

| نوع الوثيقة | Code | template_id (مطلوب) |
|------------|------|-------------------|
| عقد الزواج | `marriage_contract` | UUID من aadle_docgen |
| الطلاق | `divorce` | UUID من aadle_docgen |
| الوكالة | `power_of_attorney` | UUID من aadle_docgen |
| الميراث | `inheritance` | UUID من aadle_docgen |
| عقد البيع | `sale_contract` | UUID من aadle_docgen |

---

## ⚠️ ملاحظات مهمة

1. **UUIDs الفعلية**: يجب الحصول على UUIDs الفعلية من نظام `aadle_docgen`
2. **التحقق**: بعد إضافة `template_id`، تحقق من أن الوثائق تعمل بشكل صحيح
3. **Fallback**: للـ Flask القديم، إذا لم يكن `template_id` موجوداً، سيستخدم `template_name` كـ fallback

---

## 🔍 التحقق من الإعدادات

### من Odoo Shell:
```python
# عرض جميع أنواع الوثائق مع template_id
env['notary.document.type'].search([]).read(['name', 'code', 'template_id'])
```

### من SQL:
```sql
SELECT id, name, code, template_id 
FROM notary_document_type 
ORDER BY code;
```

---

## 🚨 رسائل الخطأ

إذا حاولت توليد PDF بدون `template_id`، ستحصل على:

```
لم يتم تعيين معرّف القالب (template_id) لنوع الوثيقة "عقد الزواج"
يرجى إضافته في إعدادات أنواع الوثائق
```

---

## 📝 الخطوات التالية

1. ✅ الحصول على UUIDs من نظام `aadle_docgen`
2. ✅ إضافة `template_id` لكل نوع وثيقة
3. ✅ اختبار توليد PDF لكل نوع
4. ✅ التحقق من أن FastAPI يعمل بشكل صحيح

---

## 📞 الدعم

إذا واجهت مشاكل:
1. تحقق من أن `template_id` موجود في قاعدة البيانات
2. تحقق من أن UUID صحيح من نظام `aadle_docgen`
3. راجع رسائل الخطأ في Odoo logs

