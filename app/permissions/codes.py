"""
Permission codes for the system

This file defines all permission codes that can be assigned to users.
When adding new features, add new permission codes here.
"""

# User management permissions
PERMISSION_CREATE_USER = "create_user"
PERMISSION_UPDATE_USER = "update_user"
PERMISSION_DELETE_USER = "delete_user"
PERMISSION_VIEW_USERS = "view_users"

# Permission management
PERMISSION_MANAGE_PERMISSIONS = "manage_permissions"

# System permissions
PERMISSION_VIEW_LOGS = "view_logs"
PERMISSION_SYSTEM_SETTINGS = "system_settings"

# Editor permissions (can be extended)
PERMISSION_EDIT_CONTENT = "edit_content"
PERMISSION_PUBLISH_CONTENT = "publish_content"

# Shopify permissions
SHOPIFY_ORDERS_VIEW = "shopify_orders_view"
SHOPIFY_ORDERS_MANAGE = "shopify_orders_manage"

# All available permissions with Bulgarian descriptions
ALL_PERMISSIONS = [
    {
        "code": PERMISSION_CREATE_USER,
        "name": "Създаване на потребители",
        "description": "Може да създава нови потребители в системата"
    },
    {
        "code": PERMISSION_UPDATE_USER,
        "name": "Редактиране на потребители",
        "description": "Може да редактира съществуващи потребители"
    },
    {
        "code": PERMISSION_DELETE_USER,
        "name": "Изтриване на потребители",
        "description": "Може да изтрива потребители от системата"
    },
    {
        "code": PERMISSION_VIEW_USERS,
        "name": "Преглед на потребители",
        "description": "Може да преглежда списък с потребители"
    },
    {
        "code": PERMISSION_MANAGE_PERMISSIONS,
        "name": "Управление на права",
        "description": "Може да управлява правата на потребителите"
    },
    {
        "code": PERMISSION_VIEW_LOGS,
        "name": "Преглед на логове",
        "description": "Може да преглежда системни логове"
    },
    {
        "code": PERMISSION_SYSTEM_SETTINGS,
        "name": "Системни настройки",
        "description": "Може да променя системните настройки"
    },
    {
        "code": PERMISSION_EDIT_CONTENT,
        "name": "Редактиране на съдържание",
        "description": "Може да редактира съдържание"
    },
    {
        "code": PERMISSION_PUBLISH_CONTENT,
        "name": "Публикуване на съдържание",
        "description": "Може да публикува съдържание"
    },
    {
        "code": SHOPIFY_ORDERS_VIEW,
        "name": "Преглед на Shopify поръчки",
        "description": "Може да преглежда поръчки и артикули от Shopify"
    },
    {
        "code": SHOPIFY_ORDERS_MANAGE,
        "name": "Управление на Shopify поръчки",
        "description": "Може да управлява поръчки в Shopify"
    }
]


# Default permissions for each role
ROLE_PERMISSIONS = {
    "admin": [p["code"] for p in ALL_PERMISSIONS],  # Admin has all permissions
    "editor": [
        PERMISSION_VIEW_USERS,
        PERMISSION_EDIT_CONTENT,
        PERMISSION_PUBLISH_CONTENT,
    ],
    "user": [
        PERMISSION_VIEW_USERS,
    ]
}
