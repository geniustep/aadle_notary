#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script سريع لإضافة template_id لنوع وثيقة محدد

الاستخدام من Odoo Shell:
    exec(open('/opt/odoo18/custom_models/aadle_notary/scripts/add_template_id_quick.py').read())
    add_template_id(env, 'marriage_contract', 'your-uuid-here')
"""

def add_template_id(env, doc_type_code: str, template_id: str):
    """
    إضافة template_id لنوع وثيقة محدد
    
    Args:
        env: Odoo environment
        doc_type_code: كود نوع الوثيقة (marriage_contract, divorce_contract, etc.)
        template_id: UUID القالب من aadle_docgen
    """
    doc_type = env['notary.document.type'].search([('code', '=', doc_type_code)], limit=1)
    
    if not doc_type:
        print(f'❌ لم يتم العثور على نوع وثيقة بالكود: {doc_type_code}')
        return False
    
    old_value = doc_type.template_id
    doc_type.template_id = template_id
    env.cr.commit()
    
    print(f'✅ تم تحديث {doc_type.name} ({doc_type_code}):')
    print(f'   من: {old_value or "فارغ"}')
    print(f'   إلى: {template_id}')
    
    return True


def add_template_id_by_name(env, doc_type_name: str, template_id: str):
    """
    إضافة template_id لنوع وثيقة بالاسم
    
    Args:
        env: Odoo environment
        doc_type_name: اسم نوع الوثيقة (عقد زواج، عقد طلاق، etc.)
        template_id: UUID القالب من aadle_docgen
    """
    doc_type = env['notary.document.type'].search([('name', '=', doc_type_name)], limit=1)
    
    if not doc_type:
        print(f'❌ لم يتم العثور على نوع وثيقة بالاسم: {doc_type_name}')
        return False
    
    old_value = doc_type.template_id
    doc_type.template_id = template_id
    env.cr.commit()
    
    print(f'✅ تم تحديث {doc_type.name} ({doc_type.code}):')
    print(f'   من: {old_value or "فارغ"}')
    print(f'   إلى: {template_id}')
    
    return True


def show_doc_types(env):
    """
    عرض جميع أنواع الوثائق مع template_id
    """
    print('📋 أنواع الوثائق:')
    print('=' * 60)
    
    doc_types = env['notary.document.type'].search([])
    for dt in doc_types:
        status = '✅' if dt.template_id and not dt.template_id.startswith('uuid-for-') else '❌'
        print(f'{status} {dt.name} (code: {dt.code})')
        print(f'   template_id: {dt.template_id or "فارغ"}')
        print()


# مثال للاستخدام:
if __name__ == '__main__':
    print('💡 للاستخدام من Odoo Shell:')
    print('=' * 60)
    print('exec(open("/opt/odoo18/custom_models/aadle_notary/scripts/add_template_id_quick.py").read())')
    print('add_template_id(env, "marriage_contract", "your-uuid-here")')
    print()
    print('أو:')
    print('add_template_id_by_name(env, "عقد زواج", "your-uuid-here")')

