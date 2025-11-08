# Aadle Notary - Postman Collection Guide

## دليل اختبار APIs مع Postman

هذا الدليل يشرح كيفية اختبار جميع APIs الخاصة بنظام الوثائق العدلية باستخدام Postman.

---

## الإعدادات الأولية

### 1. متغيرات البيئة (Environment Variables)

أنشئ Environment جديد في Postman باسم `Aadle Notary` وأضف المتغيرات التالية:

```
base_url = http://localhost:8069
database = your_database_name
username = admin
password = admin
session_id = (سيتم ملؤه تلقائياً بعد Login)
```

---

## 1. Authentication

### Login (تسجيل الدخول)

**Request:**
```
POST {{base_url}}/web/session/authenticate
Content-Type: application/json
```

**Body:**
```json
{
    "jsonrpc": "2.0",
    "params": {
        "db": "{{database}}",
        "login": "{{username}}",
        "password": "{{password}}"
    }
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": null,
    "result": {
        "uid": 2,
        "is_system": true,
        "is_admin": true,
        "user_context": {...},
        "db": "your_database",
        "server_version": "18.0",
        "session_id": "abc123..."
    }
}
```

**Tests Script (في Postman):**
```javascript
// حفظ session_id تلقائياً
var jsonData = pm.response.json();
pm.environment.set("session_id", jsonData.result.session_id);
```

---

## 2. Document Types (أنواع الوثائق)

### 2.1 قراءة جميع أنواع الوثائق

**Request:**
```
POST {{base_url}}/web/dataset/call_kw/notary.document.type/search_read
Content-Type: application/json
Cookie: session_id={{session_id}}
```

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document.type",
        "method": "search_read",
        "args": [],
        "kwargs": {
            "domain": [],
            "fields": ["id", "name", "name_fr", "code", "default_price", "sequence_prefix", "is_active"],
            "limit": 100
        }
    },
    "id": 1
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": [
        {
            "id": 1,
            "name": "عقد زواج",
            "name_fr": "Contrat de Mariage",
            "code": "marriage_contract",
            "default_price": 500.0,
            "sequence_prefix": "MC-",
            "is_active": true
        },
        ...
    ]
}
```

### 2.2 قراءة نوع وثيقة واحد

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document.type",
        "method": "read",
        "args": [[1]],
        "kwargs": {
            "fields": ["name", "code", "default_price", "description"]
        }
    },
    "id": 2
}
```

### 2.3 إنشاء نوع وثيقة جديد (Admin فقط)

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document.type",
        "method": "create",
        "args": [{
            "name": "عقد إيجار",
            "name_fr": "Contrat de Location",
            "code": "rental_contract",
            "sequence_prefix": "RC-",
            "default_price": 350.0,
            "description": "عقد إيجار عقار أو محل تجاري"
        }],
        "kwargs": {}
    },
    "id": 3
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 3,
    "result": 8
}
```

---

## 3. Documents (الوثائق)

### 3.1 إنشاء وثيقة جديدة

**Request:**
```
POST {{base_url}}/web/dataset/call_kw/notary.document/create
Content-Type: application/json
Cookie: session_id={{session_id}}
```

**Body - مثال عقد زواج:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "create",
        "args": [{
            "document_type_id": 1,
            "partner_id": 7,
            "data": {
                "groom": {
                    "name": "أحمد محمد علي",
                    "national_id": "AB123456",
                    "birth_date": "1990-05-15",
                    "address": "الدار البيضاء، المغرب"
                },
                "bride": {
                    "name": "فاطمة حسن",
                    "national_id": "CD789012",
                    "birth_date": "1995-08-20",
                    "address": "الرباط، المغرب"
                },
                "dowry": {
                    "amount": 50000,
                    "currency": "MAD",
                    "paid": 20000,
                    "remaining": 30000
                },
                "witnesses": [
                    {"name": "محمد عبد الله", "national_id": "EF345678"},
                    {"name": "علي حسين", "national_id": "GH901234"}
                ],
                "marriage_date": "2025-01-15"
            },
            "price": 500.0
        }],
        "kwargs": {}
    },
    "id": 10
}
```

**Body - مثال رسم إرث:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "create",
        "args": [{
            "document_type_id": 2,
            "partner_id": 8,
            "data": {
                "deceased": {
                    "name": "محمد بن عبد الله",
                    "national_id": "IJ567890",
                    "death_date": "2024-12-01"
                },
                "estate": {
                    "total_value": 2000000,
                    "currency": "MAD",
                    "properties": [
                        {"type": "house", "value": 1500000},
                        {"type": "savings", "value": 500000}
                    ]
                },
                "heirs": [
                    {"name": "فاطمة", "relation": "wife", "share": null},
                    {"name": "أحمد", "relation": "son", "share": null},
                    {"name": "خديجة", "relation": "daughter", "share": null}
                ]
            },
            "price": 800.0
        }],
        "kwargs": {}
    },
    "id": 11
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 10,
    "result": 15
}
```

### 3.2 قراءة وثيقة

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "read",
        "args": [[15]],
        "kwargs": {
            "fields": [
                "name",
                "document_type_id",
                "partner_id",
                "notary_id",
                "date_created",
                "state",
                "price",
                "data",
                "invoice_id",
                "invoice_state"
            ]
        }
    },
    "id": 12
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 12,
    "result": [{
        "id": 15,
        "name": "MC-2025-000001",
        "document_type_id": [1, "عقد زواج"],
        "partner_id": [7, "أحمد محمد علي"],
        "notary_id": [2, "Admin"],
        "date_created": "2025-01-10",
        "state": "draft",
        "price": 500.0,
        "data": {...},
        "invoice_id": [20, "INV/2025/00001"],
        "invoice_state": "not_paid"
    }]
}
```

### 3.3 البحث والفلترة

**مثال 1: وثائقي فقط**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "search_read",
        "args": [],
        "kwargs": {
            "domain": [["notary_id", "=", 2]],
            "fields": ["name", "document_type_id", "partner_id", "state", "price"],
            "limit": 20,
            "offset": 0,
            "order": "date_created desc"
        }
    },
    "id": 13
}
```

**مثال 2: المسودات فقط**
```json
{
    "domain": [["state", "=", "draft"]],
    ...
}
```

**مثال 3: وثائق عقود الزواج**
```json
{
    "domain": [["document_type_id.code", "=", "marriage_contract"]],
    ...
}
```

**مثال 4: وثائق هذا الشهر**
```json
{
    "domain": [
        ["date_created", ">=", "2025-01-01"],
        ["date_created", "<=", "2025-01-31"]
    ],
    ...
}
```

**مثال 5: فلاتر متعددة**
```json
{
    "domain": [
        ["state", "=", "confirmed"],
        ["invoice_state", "=", "not_paid"],
        ["notary_id", "=", 2]
    ],
    ...
}
```

### 3.4 تحديث وثيقة

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "write",
        "args": [
            [15],
            {
                "price": 550.0,
                "data": {
                    "groom": {...},
                    "bride": {...},
                    "additional_notes": "تم الاتفاق على زيادة الصداق"
                }
            }
        ],
        "kwargs": {}
    },
    "id": 14
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 14,
    "result": true
}
```

### 3.5 تأكيد وثيقة

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "action_confirm",
        "args": [[15]],
        "kwargs": {}
    },
    "id": 15
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 15,
    "result": true
}
```

**Tests Script:**
```javascript
// التحقق من النجاح
pm.test("Document confirmed successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.result).to.eql(true);
});
```

### 3.6 إتمام وثيقة

**ملاحظة:** يجب أن تكون الفاتورة مدفوعة أولاً

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "action_finalize",
        "args": [[15]],
        "kwargs": {}
    },
    "id": 16
}
```

### 3.7 إلغاء وثيقة

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "action_cancel",
        "args": [[15]],
        "kwargs": {}
    },
    "id": 17
}
```

### 3.8 حذف وثيقة (Draft فقط)

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "unlink",
        "args": [[15]],
        "kwargs": {}
    },
    "id": 18
}
```

---

## 4. Partners (الزبائن)

### 4.1 إنشاء زبون جديد

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "res.partner",
        "method": "create",
        "args": [{
            "name": "أحمد محمد علي",
            "is_client": true,
            "national_id": "AB123456",
            "email": "ahmed@example.com",
            "phone": "+212600000000",
            "street": "شارع المسيرة، رقم 123",
            "city": "الدار البيضاء",
            "country_id": 149
        }],
        "kwargs": {}
    },
    "id": 20
}
```

### 4.2 البحث عن زبون

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "res.partner",
        "method": "search_read",
        "args": [],
        "kwargs": {
            "domain": [["is_client", "=", true]],
            "fields": ["id", "name", "national_id", "email", "phone", "document_count"],
            "limit": 50
        }
    },
    "id": 21
}
```

### 4.3 قراءة وثائق زبون

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "search_read",
        "args": [],
        "kwargs": {
            "domain": [["partner_id", "=", 7]],
            "fields": ["name", "document_type_id", "state", "price", "date_created"],
            "order": "date_created desc"
        }
    },
    "id": 22
}
```

---

## 5. Invoices (الفواتير)

### 5.1 قراءة فواتير عدلية

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "account.move",
        "method": "search_read",
        "args": [],
        "kwargs": {
            "domain": [["is_notary_invoice", "=", true]],
            "fields": [
                "name",
                "notary_document_id",
                "partner_id",
                "invoice_date",
                "amount_total",
                "payment_state"
            ],
            "limit": 50
        }
    },
    "id": 30
}
```

### 5.2 قراءة فاتورة وثيقة

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "read",
        "args": [[15]],
        "kwargs": {
            "fields": ["invoice_id", "invoice_state", "is_invoice_paid"]
        }
    },
    "id": 31
}
```

---

## 6. Reports & Statistics

### 6.1 إحصائيات عامة

**عدد الوثائق حسب الحالة:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "notary.document",
        "method": "read_group",
        "args": [],
        "kwargs": {
            "domain": [],
            "fields": ["state"],
            "groupby": ["state"]
        }
    },
    "id": 40
}
```

**Response:**
```json
{
    "result": [
        {"state": "draft", "state_count": 15},
        {"state": "confirmed", "state_count": 8},
        {"state": "finalized", "state_count": 42}
    ]
}
```

### 6.2 إحصائيات حسب نوع الوثيقة

```json
{
    "kwargs": {
        "domain": [],
        "fields": ["document_type_id", "price:sum"],
        "groupby": ["document_type_id"]
    }
}
```

### 6.3 إحصائيات العدل

```json
{
    "kwargs": {
        "domain": [],
        "fields": ["notary_id", "price:sum"],
        "groupby": ["notary_id"]
    }
}
```

---

## 7. Error Handling

### أخطاء شائعة:

**1. غير مصرح (Unauthorized):**
```json
{
    "jsonrpc": "2.0",
    "error": {
        "code": 100,
        "message": "Odoo Session Expired"
    }
}
```
**الحل:** قم بتسجيل الدخول مرة أخرى

**2. لا يمكن إتمام الوثيقة:**
```json
{
    "error": {
        "data": {
            "message": "يجب دفع الفاتورة قبل إتمام الوثيقة!"
        }
    }
}
```

**3. لا توجد صلاحية:**
```json
{
    "error": {
        "data": {
            "message": "Access Denied"
        }
    }
}
```

---

## 8. Collection Structure (هيكل Collection في Postman)

```
Aadle Notary API
├── 1. Authentication
│   └── Login
├── 2. Document Types
│   ├── Get All Document Types
│   ├── Get Document Type by ID
│   ├── Create Document Type
│   └── Update Document Type
├── 3. Documents
│   ├── Create Document (Marriage Contract)
│   ├── Create Document (Inheritance)
│   ├── Get Document by ID
│   ├── Search Documents (My Documents)
│   ├── Search Documents (Drafts)
│   ├── Search Documents (This Month)
│   ├── Update Document
│   ├── Confirm Document
│   ├── Finalize Document
│   ├── Cancel Document
│   └── Delete Document
├── 4. Partners
│   ├── Create Partner
│   ├── Search Partners (Clients)
│   └── Get Partner Documents
├── 5. Invoices
│   ├── Get Notary Invoices
│   └── Get Document Invoice
└── 6. Reports
    ├── Documents by State
    ├── Documents by Type
    └── Documents by Notary
```

---

## 9. Testing Scenarios

### Scenario 1: إنشاء وثيقة كاملة

1. Login
2. Get Document Types
3. Create Partner
4. Create Document
5. Confirm Document
6. Get Document Invoice
7. (دفع الفاتورة يدوياً من Odoo)
8. Finalize Document

### Scenario 2: البحث والإحصائيات

1. Login
2. Search My Documents
3. Search Drafts
4. Get Statistics by State
5. Get Statistics by Type

### Scenario 3: إدارة أنواع الوثائق (Admin)

1. Login as Admin
2. Get All Document Types
3. Create New Document Type
4. Update Document Type
5. Deactivate Document Type

---

## 10. Environment Setup للفرق

### Development
```
base_url = http://localhost:8069
database = aadle_notary_dev
```

### Staging
```
base_url = https://staging.aadle.com
database = aadle_notary_staging
```

### Production
```
base_url = https://api.aadle.com
database = aadle_notary_prod
```

---

**Made with ❤️ by Aadle Team**
