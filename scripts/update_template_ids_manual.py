#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script لتحديث template_id يدوياً في قاعدة بيانات Odoo

الاستخدام من Odoo Shell:
    exec(open('/opt/odoo18/custom_models/aadle_notary/scripts/update_template_ids_manual.py').read())
    update_template_ids(env)
"""

def update_template_ids(env):
    """
    تحديث template_id لأنواع الوثائق يدوياً
    
    ⚠️  يجب استبدال UUIDs التالية بـ UUIDs الفعلية من aadle_docgen
    """
    
    # ⚠️  استبدل هذه UUIDs بـ UUIDs الفعلية من aadle_docgen
    template_mapping = {
        'marriage_contract': 'uuid-for-marriage-contract',  # ⚠️ استبدل
        'divorce': 'uuid-for-divorce',  # ⚠️ استبدل
        'power_of_attorney': 'uuid-for-power-of-attorney',  # ⚠️ استبدل
        'inheritance': 'uuid-for-inheritance',  # ⚠️ استبدل
        'sale_contract': 'uuid-for-sale-contract',  # ⚠️ استبدل
    }
    
    print('🔄 جاري تحديث template_id لأنواع الوثائق...')
    print('=' * 60)
    
    doc_types = env['notary.document.type'].search([])
    
    updated_count = 0
    for doc_type in doc_types:
        if not doc_type.code:
            continue
        
        template_id = template_mapping.get(doc_type.code)
        if template_id and template_id.startswith('uuid-for-'):
            print(f'  ⚠️  {doc_type.name} ({doc_type.code}): UUID غير محدث - {template_id}')
            continue
        
        if template_id:
            old_value = doc_type.template_id
            doc_type.template_id = template_id
            updated_count += 1
            print(f'  ✅ {doc_type.name} ({doc_type.code}): {old_value or "فارغ"} → {template_id}')
        else:
            print(f'  ⚠️  {doc_type.name} ({doc_type.code}): لا يوجد UUID في القائمة')
    
    if updated_count > 0:
        env.cr.commit()
        print(f'\n✅ تم تحديث {updated_count} نوع وثيقة')
    else:
        print('\n⚠️  لم يتم تحديث أي نوع وثيقة')
        print('💡 تأكد من استبدال UUIDs في template_mapping')
    
    print('\n📋 الحالة الحالية:')
    print('=' * 60)
    for doc_type in doc_types:
        status = '✅' if doc_type.template_id and not doc_type.template_id.startswith('uuid-for-') else '❌'
        print(f'  {status} {doc_type.name} ({doc_type.code}): {doc_type.template_id or "فارغ"}')


def show_current_template_ids(env):
    """
    عرض template_id الحالي لأنواع الوثائق
    """
    print('📋 template_id الحالي لأنواع الوثائق:')
    print('=' * 60)
    
    doc_types = env['notary.document.type'].search([])
    for doc_type in doc_types:
        status = '✅' if doc_type.template_id and not doc_type.template_id.startswith('uuid-for-') else '❌'
        print(f'  {status} {doc_type.name} ({doc_type.code}): {doc_type.template_id or "فارغ"}')


def set_template_id(env, doc_type_code: str, template_id: str):
    """
    تعيين template_id لنوع وثيقة محدد
    
    Args:
        env: Odoo environment
        doc_type_code: كود نوع الوثيقة (marriage_contract, divorce, etc.)
        template_id: UUID القالب من aadle_docgen
    """
    doc_type = env['notary.document.type'].search([('code', '=', doc_type_code)], limit=1)
    
    if not doc_type:
        print(f'❌ لم يتم العثور على نوع وثيقة بالكود: {doc_type_code}')
        return
    
    old_value = doc_type.template_id
    doc_type.template_id = template_id
    env.cr.commit()
    
    print(f'✅ تم تحديث {doc_type.name} ({doc_type_code}):')
    print(f'   من: {old_value or "فارغ"}')
    print(f'   إلى: {template_id}')

