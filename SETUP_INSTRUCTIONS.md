# 🔧 دليل إعداد aadle_docgen

## الطرق المختلفة للإعداد

### الطريقة 1: من خلال Terminal (الأسهل) ✅

افتح Terminal وقم بتنفيذ:

```bash
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 odoo/odoo-bin shell -c /etc/odoo18.conf -d aadle --no-http"
```

ثم في shell الذي سيظهر، انسخ والصق:

```python
ICP = env['ir.config_parameter'].sudo()

# إعداد المسار
ICP.set_param('aadle.docgen_api_path', '/api/v1/generate')

# إعداد نوع authentication
ICP.set_param('aadle.docgen_auth_type', 'bearer')

print('✅ تم الإعداد بنجاح!')
```

---

### الطريقة 2: من خلال Odoo UI (واجهة المستخدم)

1. سجّل الدخول إلى Odoo كـ Administrator
2. اذهب إلى: **Settings → Technical → Parameters → System Parameters**
3. اضغط على **Create** لإضافة كل إعداد:

   **الإعداد 1:**
   - Key: `aadle.docgen_api_path`
   - Value: `/api/v1/generate` (أو المسار الصحيح)

   **الإعداد 2:**
   - Key: `aadle.docgen_auth_type`
   - Value: `bearer`

---

### الطريقة 3: استخدام سكريبت Bash

قم بتشغيل:

```bash
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 odoo/odoo-bin shell -c /etc/odoo18.conf -d aadle --no-http << 'EOF'
ICP = env['ir.config_parameter'].sudo()
ICP.set_param('aadle.docgen_api_path', '/api/v1/generate')
ICP.set_param('aadle.docgen_auth_type', 'bearer')
print('✅ تم الإعداد بنجاح!')
EOF
"
```

---

### الطريقة 4: من خلال Python Script

أنشئ ملف `setup_docgen.py`:

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/odoo18')

import odoo
from odoo import api, SUPERUSER_ID

# تهيئة Odoo
odoo.tools.config.parse_config(['-c', '/etc/odoo18.conf'])
odoo.tools.config['init'] = {}
odoo.tools.config['update'] = {}

# الاتصال بقاعدة البيانات
env = api.Environment(odoo.registry('aadle'), SUPERUSER_ID, {})

# الإعداد
ICP = env['ir.config_parameter'].sudo()
ICP.set_param('aadle.docgen_api_path', '/api/v1/generate')
ICP.set_param('aadle.docgen_auth_type', 'bearer')

print('✅ تم الإعداد بنجاح!')
```

ثم قم بتشغيله:
```bash
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 setup_docgen.py"
```

---

## التحقق من الإعدادات

بعد الإعداد، يمكنك التحقق من خلال:

```bash
cd /opt/odoo18
sudo -u odoo18 bash -c "source venv/bin/activate && python3 odoo/odoo-bin shell -c /etc/odoo18.conf -d aadle --no-http << 'EOF'
ICP = env['ir.config_parameter'].sudo()
print('📋 الإعدادات الحالية:')
print(f'   API Path: {ICP.get_param(\"aadle.docgen_api_path\", \"/api/generate\")}')
print(f'   Auth Type: {ICP.get_param(\"aadle.docgen_auth_type\", \"bearer\")}')
print(f'   Primary URL: {ICP.get_param(\"aadle.docgen_url\", \"https://docgen.propanel.ma\")}')
print(f'   Fallback URL: {ICP.get_param(\"aadle.docgen_fallback_url\", \"http://64.226.110.81:5000\")}')
EOF
"
```

---

## ملاحظات مهمة

1. **المسار الصحيح**: تأكد من أن المسار `/api/v1/generate` هو الصحيح. إذا كان مختلفاً، غيّره.
2. **Bearer Token**: سيتم أخذه تلقائياً من جلسة المستخدم، لا حاجة لإعداده يدوياً.
3. **Fallback Token**: إذا أردت إضافة token احتياطي، استخدم:
   ```python
   ICP.set_param('aadle.docgen_api_token', 'your-fallback-token')
   ```

---

## استكشاف الأخطاء

إذا واجهت مشاكل:

1. تأكد من أنك تستخدم قاعدة البيانات الصحيحة (`aadle`)
2. تأكد من أن المستخدم لديه صلاحيات `sudo()`
3. تحقق من الإعدادات بعد التعديل

