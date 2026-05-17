-- Seed data for development/testing
-- Run after migrations: psql -U northstar -d northstar -f sql/seed.sql

INSERT INTO projects (id, name, description, status, created_at, updated_at)
VALUES
  ('a0000000-0000-0000-0000-000000000001', 'Test Project Alpha', 'A test project for development', 'ACTIVE', NOW(), NOW()),
  ('a0000000-0000-0000-0000-000000000002', 'Research: AI Safety', 'Research project on AI alignment and safety', 'DRAFT', NOW(), NOW());

INSERT INTO sources (id, project_id, title, url, content_type, raw_content, created_at, updated_at)
VALUES
  ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'Sample Article', 'https://example.com/article', 'text/html', 'This is sample raw content for testing.', NOW(), NOW());
