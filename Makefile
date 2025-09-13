# Makefile for Django EventlineZ Project

.PHONY: help install migrate seed seed-fresh seed-clear runserver shell test clean collectstatic check-imports check-user reset-user-password docker-status db-test list-users pgadmin fix-event-ownership check-event-ownership clear-all-data seed-super-fresh debug-events check-db-state seed-cities seed-categories seed-locations-categories check-connection force-seed-now seed-direct

# Default target
help:
	@echo "Available commands:"
	@echo "  install       - Install dependencies"
	@echo "  migrate       - Run Django migrations"
	@echo "  seed          - Seed database with test data (runs migrate first)"
	@echo "  seed-fresh    - Clear existing data and seed with fresh test data"
	@echo "  seed-clear    - Alias for seed-fresh"
	@echo "  runserver     - Start Django development server"
	@echo "  shell         - Open Django shell"
	@echo "  test          - Run tests"
	@echo "  clean         - Clean Python cache files"
	@echo "  collectstatic - Collect static files"
	@echo "  superuser     - Create superuser"
	@echo "  requirements  - Generate requirements.txt"
	@echo "  check-imports - Test if all models can be imported"
	@echo "  check-user    - Check user details for calisamba@gmail.com"
	@echo "  reset-user-password - Reset password for calisamba@gmail.com"
	@echo "  docker-status - Check Docker containers status"
	@echo "  db-test       - Test database connection"
	@echo "  list-users    - List all users in database"
	@echo "  pgadmin       - Show pgAdmin access information"
	@echo "  fix-event-ownership - Ensure all events belong to calisambaa@gmail.com"
	@echo "  check-event-ownership - Check event ownership (dry run)"
	@echo "  clear-all-data - Clear all data from database (DANGEROUS)"
	@echo "  seed-super-fresh - Clear all data then seed fresh"
	@echo "  debug-events - Debug events and promoter relationships"
	@echo "  check-db-state - Check current database state"
	@echo "  seed-cities - Seed California cities"
	@echo "  seed-categories - Seed music categories"
	@echo "  seed-locations-categories - Seed both cities and categories"
	@echo "  check-connection - Check database connection and current data"
	@echo "  force-seed-now - Force seed categories and cities to current DB"
	@echo "  seed-direct - Seed categories and cities with verification"
	@echo "  fix-db-connection - Fix and test database connection to PostgreSQL"
	@echo "  install-postgres - Install PostgreSQL Python driver"
	@echo "  fix-event-images - Fix missing/broken event images"

# Install dependencies
install:
	pip install -r requirements.txt

# Run migrations
migrate:
	python manage.py makemigrations
	python manage.py migrate

# Check if all models can be imported
check-imports:
	python test_seed.py

# Seed database with test data (with migration check)
seed: migrate
	python manage.py seed_all

# Flush database and seed with fresh test data
seed-fresh: migrate
	python manage.py seed_all --clear

# Seed with clear flag (alias for seed-fresh)
seed-clear: seed-fresh

# Start development server
runserver:
	python manage.py runserver

# Open Django shell
shell:
	python manage.py shell

# Run tests
test:
	python manage.py test

# Clean Python cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -f test_seed.py

# Collect static files
collectstatic:
	python manage.py collectstatic --noinput

# Create superuser
superuser:
	python manage.py createsuperuser

# Generate requirements file
requirements:
	pip freeze > requirements.txt

# Setup project (install, migrate, seed)
setup: install migrate seed
	@echo "Project setup complete!"

# Reset database and start fresh
reset: seed-fresh
	@echo "Database reset complete!"

# Development workflow
dev: migrate runserver

# Production setup
prod: install migrate collectstatic
	@echo "Production setup complete!"

# Debug seed issues
debug-seed: check-imports
	@echo "Running seed with debug info..."
	python manage.py seed_data --verbosity=2

# Check what data exists in database
check-data:
	python manage.py check_data

# Check user details and optionally reset password
check-user:
	python manage.py check_user calisamba@gmail.com

# Reset user password
reset-user-password:
	python manage.py check_user calisamba@gmail.com --reset-password

# Check Docker containers status
docker-status:
	docker-compose ps

# Check database connection
db-test:
	python manage.py dbshell --command="SELECT current_database(), current_user;"

# List all users in database
list-users:
	python manage.py shell -c "from django.contrib.auth.models import User; from event.models import Promoter; from customer.models import Customer; print('=== All Users ==='); [print(f'Username: {u.username}, Email: {u.email}, Active: {u.is_active}, Staff: {u.is_staff}') for u in User.objects.all()]; print('=== Promoters ==='); [print(f'User: {p.user.username}, Name: {p.name}') for p in Promoter.objects.all()]; print('=== Customers ==='); [print(f'User: {c.user.username}, Name: {c.first_name} {c.last_name}') for c in Customer.objects.all()]"

# Access pgAdmin (should open in browser)
pgadmin:
	@echo "pgAdmin should be available at: http://localhost:5050"
	@echo "Login with: admin@eventlinez.com / admin123"
	@echo "Database connection details:"
	@echo "  Host: eventlinez_db (or localhost if connecting from host)"
	@echo "  Port: 5432"
	@echo "  Database: eventlinez"
	@echo "  Username: eventlinez"
	@echo "  Password: Texera123@"

# Fix event ownership to calisambaa@gmail.com
fix-event-ownership:
	python manage.py fix_event_ownership

# Dry run to see what would be changed
check-event-ownership:
	python manage.py fix_event_ownership --dry-run

# Clear all data (dangerous - use with caution)
clear-all-data:
	python manage.py clear_all_data --confirm

# Safe seed fresh (clear then seed)
seed-super-fresh: clear-all-data seed
	@echo "Database completely refreshed with new seed data!"

# Debug events and promoter relationships
debug-events:
	python manage.py debug_events

# Check database state
check-db-state:
	python manage.py check_database_state

# Seed only events (faster)
seed-events-only:
	python manage.py seed_events_only

# Seed California cities
seed-cities:
	python manage.py seed_cities

# Seed music categories
seed-categories:
	python manage.py seed_categories

# Seed both locations and categories
seed-locations-categories:
	python manage.py seed_locations_categories

# Check database connection and data
check-connection:
	python manage.py check_connection

# Force seed directly to current database
force-seed-now:
	@echo "🚀 Force seeding current database..."
	python manage.py seed_categories
	python manage.py seed_cities
	@echo "✅ Done! Check the event form now."

# Seed directly with verification
seed-direct:
	python manage.py seed_direct_db

# Show database configuration
show-db-config:
	python manage.py show_db_config

# Fix database connection to PostgreSQL
fix-db-connection:
	python manage.py fix_database_connection

# Install PostgreSQL dependency
install-postgres:
	pip install psycopg2-binary

# Fix missing/broken event images
fix-event-images:
	python manage.py fix_event_images

# Fix migration issues with database views
fix-migration:
	python fix_migration.py

# Complete migration process with view fix
migrate-fix: fix-migration migrate
	@echo "Migration with view fix completed!"

# Reset database completely (DANGER: deletes all data)
reset-db:
	@echo "WARNING: This will delete ALL database data!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read
	docker-compose down
	docker volume rm eventlinez_pg_data || true
	docker-compose up -d db
	@echo "Waiting for database to start..."
	sleep 10
	docker-compose up -d web

# Fresh start with clean database
fresh-start: reset-db migrate seed
	@echo "Fresh database setup complete!"

# Database access commands
db-shell:
	docker exec -it eventlinez_db psql -U eventlinez -d eventlinez

db-backup:
	docker exec eventlinez_db pg_dump -U eventlinez eventlinez > backup.sql

db-restore:
	docker exec -i eventlinez_db psql -U eventlinez -d eventlinez < backup.sql

db-logs:
	docker logs eventlinez_db
