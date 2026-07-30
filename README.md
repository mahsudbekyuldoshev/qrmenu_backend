# RestoFlow Backend

RestoFlow backend tizimi — restoranlar uchun QR-menyu, KDS (Kitchen Display System) va boshqaruv panellari uchun API xizmatlarini taqdim etuvchi server qismi.

## Texnologiyalar
*   **Backend:** Python, FastAPI
*   **Database:** PostgreSQL
*   **Containerization:** Docker, Docker Compose
*   **Real-time:** WebSockets

## O'rnatish va Ishga tushirish

1. **Loyihani klonlash:**
   ```bash
   git clone <repo-url>
   cd qrmenu_backend
   ```

2. **Muhit o'zgaruvchilari:**
   `.env.example` faylidan `.env` faylini yarating va PostgreSQL ma'lumotlari hamda boshqa konfiguratsiyalarni kiriting.

3. **Docker orqali ishga tushirish:**
   Docker Compose yordamida barcha servislarni (API va PostgreSQL) ishga tushiring:
   ```bash
   docker-compose up --build
   ```

4. **API hujjatlari:**
   Server ishga tushgandan so'ng, API hujjatlari (Swagger UI) quyidagi manzilda mavjud bo'ladi:
   `http://localhost:8000/docs`

## Asosiy funksional:
- Restoranlar va filiallarni boshqarish.
- Menu va taomlarni CRUD operatsiyalari.
- Buyurtmalarni real vaqt rejimida qabul qilish (WebSockets) va holatini o'zgartirish.
- Foydalanuvchi rollari (Super Admin, Direktor, Menejer, Ofitsiant, Oshpaz) asosida autentifikatsiya va avtorizatsiya.

---
*Ushbu loyiha RestoFlow tizimining server qismi hisoblanadi.*
