# 📋 Scripts للحصول على UUIDs وتحديث قاعدة البيانات

## 🎯 الهدف

هذه الـ scripts تساعدك في:
1. الحصول على UUIDs للقوالب من aadle_docgen
2. تحديث `template_id` في قاعدة بيانات Odoo

---

## 📁 الملفات المتاحة

### 1. `get_templates_from_docgen.py`

**الغرض:** الحصول على قائمة القوالب من aadle_docgen API

**الاستخدام:**

```bash
# من Terminal
cd /opt/odoo18/custom_models/aadle_notary/scripts
python3 get_templates_from_docgen.py
```

**أو من Odoo Shell:**

```python
exec(open('/opt/odoo18/custom_models/aadle_notary/scripts/get_templates_from_docgen.py').read())
templates = get_templates_from_api('https://docgen.propanel.ma', auth_token='YOUR_TOKEN')
update_odoo_template_ids(env, templates, interactive=True)
```

---

### 2. `update_template_ids_manual.py`

**الغرض:** تحديث `template_id` يدوياً في قاعدة بيانات Odoo

**الاستخدام من Odoo Shell:**

```python
exec(open('/opt/odoo18/custom_models/aadle_notary/scripts/update_template_ids_manual.py').read())

# عرض الحالة الحالية
show_current_template_ids(env)

# تحديث UUID محدد
set_template_id(env, 'marriage_contract', 'uuid-actual-here')
set_template_id(env, 'divorce', 'uuid-actual-here')

# أو تحديث جميع الأنواع
update_template_ids(env)  # ⚠️ يجب تحديث UUIDs في الكود أولاً
```

---

## 🚀 الخطوات السريعة

### الخطوة 1: الحصول على UUIDs

```bash
# محاولة من Terminal
curl https://docgen.propanel.ma/templates

# أو استخدام Script
python3 scripts/get_templates_from_docgen.py
```

### الخطوة 2: تحديث قاعدة البيانات

```python
# من Odoo Shell
exec(open('/opt/odoo18/custom_models/aadle_notary/scripts/update_template_ids_manual.py').read())
set_template_id(env, 'marriage_contract', 'uuid-from-step-1')
```

### الخطوة 3: التحقق

```python
# من Odoo Shell
env['notary.document.type'].search([]).read(['name', 'code', 'template_id'])
```

---

## 📝 مثال كامل

```python
# 1. فتح Odoo Shell
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 odoo/odoo-bin shell -c /etc/odoo18.conf -d aadle --no-http"

# 2. في Shell:
exec(open('/opt/odoo18/custom_models/aadle_notary/scripts/get_templates_from_docgen.py').read())

# 3. الحصول على القوالب
templates = get_templates_from_api('https://docgen.propanel.ma')

# 4. تحديث قاعدة البيانات
update_odoo_template_ids(env, templates, interactive=True)

# 5. التحقق
env['notary.document.type'].search([]).read(['name', 'code', 'template_id'])
```

---

## ⚠️ ملاحظات مهمة

1. **UUIDs الفعلية:** يجب استبدال UUIDs الافتراضية بـ UUIDs الفعلية من aadle_docgen
2. **Authentication:** قد تحتاج Bearer Token للوصول إلى API
3. **النسخ الاحتياطي:** احفظ UUIDs في مكان آمن

---

## 📞 الدعم

راجع `../GET_TEMPLATE_UUIDS.md` للتفاصيل الكاملة.

