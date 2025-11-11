#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script للحصول على القوالب من aadle_docgen وتحديث قاعدة بيانات Odoo

الاستخدام:
    python3 get_templates_from_docgen.py

أو من Odoo Shell:
    exec(open('/opt/odoo18/custom_models/aadle_notary/scripts/get_templates_from_docgen.py').read())
"""

import requests
import json
from typing import Dict, List, Optional


def get_templates_from_api(base_url: str = 'https://docgen.propanel.ma', 
                           auth_token: Optional[str] = None) -> List[Dict]:
    """
    الحصول على قائمة القوالب من aadle_docgen API
    
    Args:
        base_url: URL الأساسي لـ aadle_docgen
        auth_token: Bearer token للـ authentication (اختياري)
    
    Returns:
        List[Dict]: قائمة القوالب مع UUIDs
    """
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        # محاولة endpoint مختلف
        endpoints = [
            f'{base_url}/templates',
            f'{base_url}/api/templates',
            f'{base_url}/docs/templates',
        ]
        
        for endpoint in endpoints:
            try:
                print(f'🔄 جاري المحاولة: {endpoint}')
                response = requests.get(endpoint, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f'✅ نجح الاتصال: {endpoint}')
                    
                    # معالجة الاستجابة المختلفة
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        if 'templates' in data:
                            return data['templates']
                        elif 'result' in data:
                            return data['result']
                        elif 'data' in data:
                            return data['data']
                    
                    return data
                else:
                    print(f'⚠️  HTTP {response.status_code}: {endpoint}')
            except requests.exceptions.RequestException as e:
                print(f'❌ خطأ في الاتصال: {endpoint} - {str(e)}')
                continue
        
        print('❌ فشل الحصول على القوالب من جميع الـ endpoints')
        return []
        
    except Exception as e:
        print(f'❌ خطأ عام: {str(e)}')
        return []


def map_template_to_document_type(template: Dict, doc_type_code: str) -> Optional[str]:
    """
    محاولة مطابقة القالب مع نوع الوثيقة
    
    Args:
        template: بيانات القالب من API
        doc_type_code: كود نوع الوثيقة (marriage_contract, divorce, etc.)
    
    Returns:
        Optional[str]: UUID القالب إذا تمت المطابقة
    """
    # الحصول على UUID
    template_id = template.get('id') or template.get('uuid') or template.get('template_id')
    if not template_id:
        return None
    
    # الحصول على اسم القالب
    template_name = template.get('name', '').lower()
    template_code = template.get('code', '').lower()
    
    # محاولة المطابقة
    doc_type_lower = doc_type_code.lower()
    
    # مطابقة مباشرة
    if doc_type_lower in template_name or doc_type_lower in template_code:
        return str(template_id)
    
    # مطابقة يدوية
    mapping = {
        'marriage_contract': ['marriage', 'wedding', 'زواج', 'عقد زواج'],
        'divorce': ['divorce', 'طلاق', 'عقد طلاق'],
        'power_of_attorney': ['attorney', 'power', 'وكالة', 'وكيل'],
        'inheritance': ['inheritance', 'ميراث', 'تركة'],
        'sale_contract': ['sale', 'بيع', 'عقد بيع'],
    }
    
    if doc_type_lower in mapping:
        keywords = mapping[doc_type_lower]
        for keyword in keywords:
            if keyword.lower() in template_name or keyword.lower() in template_code:
                return str(template_id)
    
    return None


def update_odoo_template_ids(env, templates: List[Dict], interactive: bool = True):
    """
    تحديث template_id في قاعدة بيانات Odoo
    
    Args:
        env: Odoo environment
        templates: قائمة القوالب من API
        interactive: إذا كان True، يطلب التأكيد قبل التحديث
    """
    doc_types = env['notary.document.type'].search([])
    
    print('\n📋 أنواع الوثائق الموجودة:')
    print('=' * 60)
    for doc_type in doc_types:
        print(f'  - {doc_type.name} (code: {doc_type.code}, template_id: {doc_type.template_id or "فارغ"})')
    
    print('\n📋 القوالب المتاحة من aadle_docgen:')
    print('=' * 60)
    for template in templates:
        template_id = template.get('id') or template.get('uuid') or template.get('template_id')
        template_name = template.get('name', 'غير معروف')
        print(f'  - {template_name} (UUID: {template_id})')
    
    print('\n🔄 محاولة المطابقة التلقائية:')
    print('=' * 60)
    
    updates = []
    for doc_type in doc_types:
        if not doc_type.code:
            continue
        
        # محاولة المطابقة
        matched_template_id = None
        for template in templates:
            template_id = map_template_to_document_type(template, doc_type.code)
            if template_id:
                matched_template_id = template_id
                template_name = template.get('name', 'غير معروف')
                print(f'  ✅ {doc_type.name} → {template_name} (UUID: {template_id})')
                break
        
        if matched_template_id:
            if doc_type.template_id != matched_template_id:
                updates.append({
                    'doc_type': doc_type,
                    'old_value': doc_type.template_id,
                    'new_value': matched_template_id,
                })
        else:
            print(f'  ⚠️  {doc_type.name}: لم يتم العثور على قالب مطابق')
    
    if not updates:
        print('\n✅ لا توجد تحديثات مطلوبة')
        return
    
    print(f'\n📝 التحديثات المطلوبة ({len(updates)}):')
    print('=' * 60)
    for update in updates:
        print(f'  - {update["doc_type"].name}:')
        print(f'      من: {update["old_value"] or "فارغ"}')
        print(f'      إلى: {update["new_value"]}')
    
    if interactive:
        confirm = input('\n❓ هل تريد تطبيق هذه التحديثات؟ (y/n): ')
        if confirm.lower() != 'y':
            print('❌ تم إلغاء التحديثات')
            return
    
    # تطبيق التحديثات
    print('\n🔄 جاري التحديث...')
    for update in updates:
        update['doc_type'].template_id = update['new_value']
        print(f'  ✅ تم تحديث {update["doc_type"].name}')
    
    env.cr.commit()
    print('\n✅ تم تطبيق جميع التحديثات بنجاح!')


def main():
    """
    الدالة الرئيسية
    """
    print('=' * 60)
    print('🔧 Script للحصول على القوالب من aadle_docgen')
    print('=' * 60)
    
    # الحصول على القوالب
    base_url = input('\n📝 أدخل URL لـ aadle_docgen (افتراضي: https://docgen.propanel.ma): ').strip()
    if not base_url:
        base_url = 'https://docgen.propanel.ma'
    
    auth_token = input('📝 أدخل Bearer Token (اختياري - اضغط Enter للتخطي): ').strip()
    if not auth_token:
        auth_token = None
    
    print(f'\n🔄 جاري الاتصال بـ {base_url}...')
    templates = get_templates_from_api(base_url, auth_token)
    
    if not templates:
        print('\n❌ لم يتم العثور على قوالب')
        print('\n💡 يمكنك:')
        print('  1. التحقق من URL و Authentication')
        print('  2. فتح https://docgen.propanel.ma/docs في المتصفح')
        print('  3. نسخ UUIDs يدوياً وتحديث قاعدة البيانات')
        return
    
    print(f'\n✅ تم العثور على {len(templates)} قالب')
    
    # عرض القوالب
    print('\n📋 القوالب المتاحة:')
    for i, template in enumerate(templates, 1):
        template_id = template.get('id') or template.get('uuid') or template.get('template_id')
        template_name = template.get('name', 'غير معروف')
        print(f'  {i}. {template_name} → UUID: {template_id}')
    
    # حفظ في ملف JSON
    output_file = '/tmp/aadle_docgen_templates.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)
    print(f'\n💾 تم حفظ القوالب في: {output_file}')
    
    print('\n💡 للاستخدام في Odoo Shell:')
    print('=' * 60)
    print('exec(open("/opt/odoo18/custom_models/aadle_notary/scripts/get_templates_from_docgen.py").read())')
    print('update_odoo_template_ids(env, templates)')


if __name__ == '__main__':
    main()

