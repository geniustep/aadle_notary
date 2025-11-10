#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script لإضافة template_id مباشرة
"""

# إضافة template_id لنوع "عقد زواج"
marriage_type = env['notary.document.type'].search([('code', '=', 'marriage_contract')], limit=1)
if marriage_type:
    print(f'✅ تم العثور على: {marriage_type.name}')
    print(f'   template_id الحالي: {marriage_type.template_id or "فارغ"}')
    marriage_type.template_id = 'marriage_contract'
    env.cr.commit()
    print(f'✅ تم تحديث template_id: {marriage_type.template_id}')
    
    # التحقق
    marriage_type.invalidate_recordset(['template_id'])
    print(f'📋 التحقق: template_id = {marriage_type.template_id}')
    
    # التحقق من الوثيقة ID 3
    doc = env['notary.document'].browse(3)
    if doc.exists():
        print(f'\n📄 الوثيقة ID 3: {doc.name}')
        print(f'   template_id: {doc.document_type_id.template_id if doc.document_type_id else "N/A"}')
        print('\n✅ جاهز للاختبار! يمكنك الآن إعادة المحاولة في Odoo UI')
else:
    print('❌ لم يتم العثور على نوع "عقد زواج"')

