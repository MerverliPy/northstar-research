# SQL Scripts

- `init.sql` — Create database and user (run once as postgres superuser)
- `seed.sql` — Sample data for development

## Usage

```
psql -U postgres -f sql/init.sql
alembic upgrade head
psql -U northstar -d northstar -f sql/seed.sql
```
