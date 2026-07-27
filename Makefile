
.PHONY: help migrations migrate runserver superuser docker-up docker-down

help:
	@echo "Yordamchi buyruqlar:"
	@echo "  make migrations  - Migratsiya fayllarini yaratish"
	@echo "  make migrate     - Bazaga migratsiyalarni qo'llash"
	@echo "  make runserver   - Django serverini ishga tushirish"
	@echo "  make superuser   - Admin foydalanuvchisini yaratish"
	@echo "  make docker-up   - Docker konteynerlarini ishga tushirish"
	@echo "  make docker-down - Docker konteynerlarini to'xtatish"

migrations:
	python manage.py makemigrations

migrate:
	python manage.py  migrate

runserver:
	python manage.py runserver

user:
	python manage.py createsuperuser

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down
