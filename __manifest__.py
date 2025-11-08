# -*- coding: utf-8 -*-
{
    'name': 'Aadle Notary - نظام إدارة الوثائق العدلية',
    'version': '18.0.1.0.0',
    'category': 'Services/Notary',
    'summary': 'نظام متكامل لإدارة الوثائق العدلية، الزبائن، والفواتير',
    'description': """
نظام إدارة الوثائق العدلية - Aadle Notary
===============================================

نظام شامل لإدارة:
* أنواع الوثائق العدلية (عقود زواج، رسوم إرث، توكيلات، إلخ)
* الوثائق والزبائن
* الفواتير المرتبطة بالوثائق
* صلاحيات المستخدمين (عدل، مدير، إداري)
* Workflows متكاملة (مسودة → تأكيد → إتمام)
* تكامل مع أنظمة توليد الوثائق والحسابات الشرعية

الميزات الرئيسية:
------------------
* إدارة أنواع الوثائق وأسعارها
* حقول JSON مرنة لبيانات الوثائق
* إنشاء فواتير تلقائي
* تتبع حالة الوثائق
* صلاحيات متقدمة
* واجهة عربية كاملة
* جاهز للتكامل مع APIs خارجية
    """,
    'author': 'Aadle',
    'website': 'https://aadle.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account',
        'contacts',
    ],
    'data': [
        # Security
        'security/notary_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/ir_sequence_data.xml',
        'data/notary_document_type_data.xml',

        # Views
        'views/notary_document_type_views.xml',
        'views/notary_document_views.xml',
        'views/notary_menus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/icon.png'],
}
