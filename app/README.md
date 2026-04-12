# AstroNova Admin System

Административна система за управление на потребители с автентикация и разграничаване на права.

## Характеристики

✨ **Функционалности:**
- 🔐 JWT автентикация
- 👥 Управление на потребители (създаване, редактиране, изтриване)
- 🎭 Три нива на достъп: Admin, Editor, User
- 🔒 Гъвкава система за права (permissions)
- 🛍️ Shopify интеграция - синхронизация на поръчки и анализи
- ⭐ Астрологични анализи с подробни данни за раждане
- 🌍 Автоматично изчисляване на часови зони от координати
- 🎨 Цветово кодирани продукти (розово за любовни, синьо за детайлни анализи)
- 🇧🇬 Пълен превод на български език
- 🎨 Модерен UI с AstroNova бранд цветовете
- 📊 Административен панел със статистики

## Роли и Права

### Администратор (Admin)
- Пълен достъп до всички функции
- Може да създава, редактира и изтрива потребители
- Може да управлява правата на потребителите
- Автоматично има всички системни права

### Редактор (Editor)
- Може да преглежда потребители
- Може да редактира и публикува съдържание
- Ограничен достъп до администраторски функции

### Потребител (User)
- Може да преглежда потребители
- Основни права за достъп

## Инсталация и Стартиране

### 1. Подгответе базата данни

Уверете се, че Docker контейнерите работят:

```powershell
cd app
docker compose up -d
```

### 2. Активирайте виртуалната среда

```powershell
cd c:\dev\AstroNova-f
.\.venv\Scripts\Activate.ps1
```

### 3. Инициализирайте базата данни

```powershell
cd app
python init_db.py
```

Това ще:
- Създаде всички необходими таблици
- Създаде всички системни права
- Създаде администраторски акаунт по подразбиране

**默认 Admin данни:**
- Потребител: `admin`
- Парола: `admin123`

⚠️ **ВАЖНО:** Сменете паролата веднага след първия вход!

### 4. Стартирайте сървъра

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Отворете Admin панела

Отворете браузър и отидете на:
```
http://localhost:8000/
```

Ще бъдете пренасочени към страницата за вход.

## Shopify Интеграция

### Конфигурация

1. **Създайте Shopify приложение:**
   - Отидете на вашия Shopify Admin → Settings → Apps and sales channels → Develop apps
   - Създайте ново приложение
   - Конфигурирайте Admin API scopes:
     - `read_orders` - за четене на поръчки
     - `read_products` - за информация за продукти
   - Генерирайте Admin API access token

2. **TimeZoneDB API ключ:**
   - Регистрирайте се безплатно на: https://timezonedb.com/
   - Копирайте вашия API ключ

3. **Добавете credentials в .env файла:**

```env
# Shopify Configuration
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxx
SHOPIFY_API_VERSION=2024-01

# TimeZoneDB API
TIMEZONEDB_API_KEY=your_timezonedb_api_key
```

### Как работи интеграцията

#### 1. Структура на данните

Всяка Shopify поръчка може да съдържа **множество анализи**:
- **Поръчка** (ShopifyOrder) - инф ормация за клиента и платената сума
- **Анализ** (Analysis) - всеки line item е отделен анализ за конкретен човек или двойка

#### 2. Типове продукти

Системата разпознава два типа анализи с цветово кодиране:

| Тип | Цвят | Описание |
|-----|------|----------|
| **Любовна синастрия** (`love_synastry`) | 🩷 Розов (`#FF69B4`) | Анализ на двойка - изисква данни за 2 души |
| **Подробен анализ** (`detailed_analysis`) | 💙 Светло син (`#87CEEB`) | Индивидуален анализ - изисква данни за 1 човек |

#### 3. Изискващи се данни за всеки човек

За всеки анализ системата извлича следните данни от Shopify line item properties:

- **Име** (person1_name / person2_name)
- **Пол** (male, female, other)
- **Дата на раждане** (YYYY-MM-DD формат)
- **Час на раждане** (HH:MM формат)
- **Място на раждане** (grad, locality, etc.)
- **Географска ширина** (latitude)
- **Географска дължина** (longitude)
- **Часова зона** (автоматично изчислена от координатите)

#### 4. Автоматично изчисляване на часова зона

При синхронизация системата:
1. Извлича координатите от Shopify properties
2. Използва TimeZoneDB API за точно определяне на часовата зона
3. Запазва timezone име (напр. "Europe/Sofia") и offset (напр. "+03:00")
4. При липса на API ключ използва fallback изчисление (longitude / 15)

#### 5. Shopify Property Names

Системата разпознава следните имена на properties (Bulgarian имена):

**За Човек 1:**
- Име: `Име`, `Name`, `Име на първия човек`
- Пол: `Пол`, `Gender`
- Дата: `Дата на раждане`, `Birth Date`, `Дата`
- Час: `Час на раждане`, `Birth Time`, `Час`
- Място: `Място на раждане`, `Birth Place`, `Град`, `Locality`
- Координати: `Latitude`, `Longitude`, `Ширина`, `Дължина`

**За Човек 2** (само за двойки):
- Добавете "2" или "втори" в името: `Име 2`, `Име на втория човек`
- Има същите варианти като за Човек 1

### Използване на Shopify панела

1. **Навигация:**
   - От главното меню изберете **"Shopify Поръчки"**

2. **Синхронизация:**
   - Кликнете бутона **"Синхронизирай от Shopify"**
   - Системата ще извлече последните 50 поръчки от вашия магазин
   - Ще се парсват всички line items и ще се създадат анализи

3. **Преглед на поръчки:**
   - Поръчките се показват в цветни панели
   - Цветът на границата показва типа продукт (розов/син)
   - Кликнете на поръчката за разгъване

4. **Детайли на анализ:**
   - Разгънете поръчка за да видите всички анализи
   - Всеки анализ показва:
     - Данни за Човек 1 (име, пол, дата, час, място, координати, timezone)
     - Данни за Човек 2 (за двойки)
     - Checkbox за отбелязване на обработен анализ

5. **Маркиране като обработен:**
   - Отметнете checkbox "Обработен" когато завършите анализа
   - Системата автоматично запазва статуса

### API Endpoints за Shopify

```
POST   /api/shopify/sync                          # Синхронизация от Shopify
GET    /api/shopify/local/orders                  # Локални поръчки (с пагинация)
GET    /api/shopify/local/analyses                # Всички анализи с филтриране
PUT    /api/shopify/local/analyses/{id}/mark-processed  # Отбележи като обработен
```

### Troubleshooting

**Проблем:** Неуспешна синхронизация
- ✅ Проверете че Shop URL е правилен (без https://)
- ✅ Проверете че Access Token е валиден
- ✅ Уверете се че приложението има `read_orders` scope

**Проблем:** Не се извличат данните за хора
- ✅ Проверете имената на properties в Shopify
- ✅ Добавете debug logs в `shopify_parser.py`
- ✅ Уверете се че координатите са във валиден формат

**Проблем:** Часовата зона не се изчислява
- ✅ Проверете TimeZoneDB API ключа
- ✅ Системата ще използва fallback метод (longitude/15) автоматично

Ще бъдете пренасочени към страницата за вход.

## Структура на проекта

```
app/
├── api/                    # API endpoints
│   ├── auth.py            # Authentication endpoints
│   ├── users.py           # User management endpoints
│   ├── permissions.py     # Permissions endpoints
│   ├── admin.py           # Admin dashboard endpoints
│   └── shopify.py         # Shopify integration endpoints
├── auth/                  # Authentication logic
│   └── dependencies.py    # Auth dependencies (get_current_user, etc.)
├── core/                  # Core configuration
│   ├── config.py         # Application settings
│   └── security.py       # Security functions (JWT, password hashing)
├── db/                    # Database configuration
│   ├── database.py       # Database connection
│   └── base.py           # Base model imports
├── models/                # SQLAlchemy models
│   ├── user.py           # User model
│   ├── permission.py     # Permission model
│   └── shopify_order.py  # ShopifyOrder and Analysis models
├── permissions/           # Permission system
│   └── codes.py          # Permission codes and definitions
├── schemas/               # Pydantic schemas
│   ├── user.py           # User schemas
│   ├── permission.py     # Permission schemas
│   ├── token.py          # Token schemas
│   └── shopify_order.py  # Shopify schemas
├── services/              # Business logic services
│   ├── shopify_client.py # Shopify API client
│   ├── shopify_parser.py # Parse Shopify data to extract person info
│   ├── shopify_sync.py   # Sync Shopify orders to database
│   └── timezone_service.py # Calculate timezone from coordinates
├── static/                # Frontend files
│   ├── login.html        # Login page
│   ├── dashboard.html    # Dashboard with user management
│   ├── shopify-orders.html # Shopify orders viewer 
│   ├── permissions.html  # Permissions overview
│   ├── styles.css        # Styling
│   └── auth.js           # Auth helper functions
├── main.py               # FastAPI application
├── init_db.py            # Database initialization script
├── create_shopify_tables.py  # Create Shopify tables
└── add_shopify_permissions.py # Add Shopify permissions
```
├── models/                # SQLAlchemy models
│   ├── user.py           # User model
│   └── permission.py     # Permission model
├── permissions/           # Permission system
│   └── codes.py          # Permission codes and definitions
├── schemas/               # Pydantic schemas
│   ├── user.py           # User schemas
│   ├── permission.py     # Permission schemas
│   └── token.py          # Token schemas
├── static/                # Frontend files
│   ├── login.html        # Login page
│   ├── dashboard.html    # Dashboard
│   ├── users.html        # User management
│   ├── permissions.html  # Permissions overview
│   ├── styles.css        # Styling
│   └── auth.js           # Auth helper functions
├── main.py               # FastAPI application
└── init_db.py            # Database initialization script
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Вход в системата
- `GET /api/auth/me` - Информация за текущия потребител

### Users (Admin only)
- `GET /api/users/` - Списък с потребители
- `GET /api/users/{id}` - Информация за потребител
- `POST /api/users/` - Създаване на потребител
- `PUT /api/users/{id}` - Редактиране на потребител
- `DELETE /api/users/{id}` - Изтриване на потребител

### Permissions (Admin only)
- `GET /api/permissions/` - Списък с права

### Admin Dashboard (Admin only)
- `GET /api/admin/stats` - Статистики за системата

### Shopify Integration (requires SHOPIFY_ORDERS_VIEW permission)
- `POST /api/shopify/sync` - Синхронизация на поръчки от Shopify
- `GET /api/shopify/local/orders` - Локални поръчки с анализи (поддържа пагинация)
- `GET /api/shopify/local/analyses` - Списък с всички анализи (може да се филтрира по processed статус)
- `PUT /api/shopify/local/analyses/{id}/mark-processed` - Отбележи анализ като обработен

## Добавяне на нови права

Когато добавяте нови функции към системата:

1. Отворете `permissions/codes.py`
2. Добавете нов код за право:
   ```python
   PERMISSION_NEW_FEATURE = "new_feature"
   ```
3. Добавете го в списъка `ALL_PERMISSIONS`:
   ```python
   {
       "code": PERMISSION_NEW_FEATURE,
       "name": "Име на правото (БГ)",
       "description": "Описание на правото"
   }
   ```
4. Рестартирайте приложението и новото право ще се появи в системата

## Цветова палитра (AstroNova)

- **Primary BG:** `#5F667B` - Основен фон
- **Accent/CTA:** `#E2A293` - Акцентен цвят за бутони
- **Supporting:** `#F3EFEA`, `#F6D6D0` - Поддържащи цветове
- **Dark:** `#4F566B` - Тъмен вариант за картички

## Сигурност

- Пароли се хешират с bcrypt
- JWT токени за автентикация
- Token срок на валидност: 24 часа
- CORS конфигуриран
- SQL injection защита чрез SQLAlchemy ORM
- Role-based access control (RBAC)

## Разработка

За разработка с hot reload:

```powershell
uvicorn main:app --reload
```

За производство (production):

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Технологии

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL
- **Authentication:** JWT (python-jose), bcrypt (passlib)
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Database:** PostgreSQL
- **Language:** Python 3.11+

---

Направено за AstroNova 🌟
