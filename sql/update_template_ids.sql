-- ============================================
-- SQL Script: تحديث template_id لأنواع الوثائق
-- ============================================
-- 
-- هذا الملف يحتوي على أوامر SQL لتحديث template_id
-- لكل نوع وثيقة في قاعدة البيانات
--
-- ⚠️ ملاحظة: يجب استبدال UUIDs التالية بـ UUIDs الفعلية
--    من نظام aadle_docgen
--
-- ============================================

-- مثال: تحديث template_id لعقد الزواج
UPDATE notary_document_type 
SET template_id = 'uuid-for-marriage-contract'  -- ⚠️ استبدل بـ UUID الفعلي
WHERE code = 'marriage_contract';

-- مثال: تحديث template_id للطلاق
UPDATE notary_document_type 
SET template_id = 'uuid-for-divorce'  -- ⚠️ استبدل بـ UUID الفعلي
WHERE code = 'divorce';

-- مثال: تحديث template_id للوكالة
UPDATE notary_document_type 
SET template_id = 'uuid-for-power-of-attorney'  -- ⚠️ استبدل بـ UUID الفعلي
WHERE code = 'power_of_attorney';

-- مثال: تحديث template_id للميراث
UPDATE notary_document_type 
SET template_id = 'uuid-for-inheritance'  -- ⚠️ استبدل بـ UUID الفعلي
WHERE code = 'inheritance';

-- مثال: تحديث template_id لعقد البيع
UPDATE notary_document_type 
SET template_id = 'uuid-for-sale-contract'  -- ⚠️ استبدل بـ UUID الفعلي
WHERE code = 'sale_contract';

-- ============================================
-- للتحقق من التحديثات:
-- ============================================
-- SELECT id, name, code, template_id 
-- FROM notary_document_type 
-- ORDER BY code;

-- ============================================
-- للعرض في Odoo Shell:
-- ============================================
-- env['notary.document.type'].search([]).read(['name', 'code', 'template_id'])

