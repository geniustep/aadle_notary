# ⚡ حل سريع: إضافة template_id

## 🎯 المشكلة

```
لم يتم تعيين معرّف القالب (template_id) لنوع الوثيقة "عقد زواج"
يرجى إضافته في إعدادات أنواع الوثائق
```

## ✅ الحل السريع

### الطريقة 1: من Odoo Shell (الأسرع)

```bash
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 odoo/odoo-bin shell -c /etc/odoo18.conf -d aadle --no-http"
```

ثم في Shell:

```python
# إضافة template_id لنوع "عقد زواج"
marriage_type = env['notary.document.type'].search([('code', '=', 'marriage_contract')], limit=1)
if marriage_type:
    # ⚠️ استبدل 'your-uuid-here' بـ UUID فعلي من aadle_docgen
    marriage_type.template_id = 'your-uuid-here'
    env.cr.commit()
    print(f'✅ تم تحديث template_id: {marriage_type.template_id}')
else:
    print('❌ لم يتم العثور على نوع "عقد زواج"')
```

---

### الطريقة 2: استخدام Script

```python
# من Odoo Shell
exec(open('/opt/odoo18/custom_models/aadle_notary/scripts/add_template_id_quick.py').read())

# إضافة template_id
add_template_id(env, 'marriage_contract', 'your-uuid-here')

# أو بالاسم
add_template_id_by_name(env, 'عقد زواج', 'your-uuid-here')
```

---

### الطريقة 3: من Odoo UI

1. افتح **Settings → Technical → Database Structure → Models**
2. ابحث عن `notary.document.type`
3. افتح نوع "عقد زواج"
4. أضف `template_id` (UUID) في الحقل المخصص
5. احفظ

---

## 🔍 كيفية الحصول على UUID

### من واجهة aadle_docgen:

1. افتح: **https://docgen.propanel.ma/docs**
2. اذهب إلى قسم **Templates**
3. اعرض قائمة القوالب
4. انسخ **UUID** للقالب المطلوب

### من API (إذا كان متاحاً):

```bash
curl https://docgen.propanel.ma/templates
```

---

## 📋 مثال كامل

```python
# 1. فتح Odoo Shell
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 odoo/odoo-bin shell -c /etc/odoo18.conf -d aadle --no-http"

# 2. في Shell:
marriage_type = env['notary.document.type'].search([('code', '=', 'marriage_contract')], limit=1)

# 3. إضافة template_id (استبدل بـ UUID فعلي)
marriage_type.template_id = '550e8400-e29b-41d4-a716-446655440000'  # ⚠️ استبدل
env.cr.commit()

# 4. التحقق
print(f'✅ template_id: {marriage_type.template_id}')

# 5. إعادة المحاولة في Odoo UI
```

---

## ⚠️ ملاحظات مهمة

1. **UUID فعلي:** يجب استبدال `'your-uuid-here'` بـ UUID فعلي من aadle_docgen
2. **التحقق:** بعد الإضافة، تحقق من أن template_id تم حفظه
3. **الاختبار:** أعد المحاولة في Odoo UI بعد إضافة template_id

---

## 🚨 إذا لم يكن لديك UUID بعد

يمكنك استخدام UUID مؤقت للاختبار (لكن لن يعمل مع aadle_docgen):

```python
marriage_type = env['notary.document.type'].search([('code', '=', 'marriage_contract')], limit=1)
marriage_type.template_id = 'test-uuid-temporary'  # ⚠️ مؤقت فقط
env.cr.commit()
```

**⚠️ تحذير:** هذا لن يعمل مع aadle_docgen، لكنه سيسمح لك باختبار الكود.

---

## ✅ بعد الإضافة

1. أعد المحاولة في Odoo UI
2. إذا ظهر خطأ "Template not found"، تحقق من:
   - UUID صحيح
   - القالب موجود في aadle_docgen
   - aadle_docgen متاح

---

## 📞 الدعم

راجع:
- `GET_TEMPLATE_UUIDS.md` - دليل الحصول على UUIDs
- `TEMPLATE_ID_SETUP.md` - دليل إعداد template_id
- `scripts/add_template_id_quick.py` - Script سريع

