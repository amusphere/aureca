#!/usr/bin/env python3

import sqlite3
from app.schema import TaskPriority

# Create test database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Create test table
cursor.execute('''
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title TEXT,
    priority INTEGER,
    expires_at REAL
)
''')

# Insert test data
test_data = [
    (1, 1, "High Priority Task", TaskPriority.HIGH.value, 1672617600.0),
    (2, 1, "Middle Priority Task", TaskPriority.MIDDLE.value, 1672704000.0),
    (3, 1, "Low Priority Task", TaskPriority.LOW.value, 1672790400.0),
    (4, 1, "No Priority Task", None, 1672876800.0),
]

cursor.executemany('''
INSERT INTO tasks (id, user_id, title, priority, expires_at)
VALUES (?, ?, ?, ?, ?)
''', test_data)

print("Data inserted:")
cursor.execute("SELECT title, priority FROM tasks")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\nTesting different ORDER BY approaches...")

# Test 1: Direct priority ordering
print("\n1. Direct priority ORDER BY:")
cursor.execute('''
SELECT title, priority
FROM tasks
ORDER BY priority, expires_at
''')
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Test 2: CASE with NULLS LAST
print("\n2. CASE with explicit NULL handling:")
cursor.execute('''
SELECT title, priority,
       CASE
           WHEN priority IS NULL THEN 999
           ELSE priority
       END as sort_priority
FROM tasks
ORDER BY sort_priority, expires_at
''')
for row in cursor.fetchall():
    print(f"  {row[0]}: priority={row[1]}, sort_priority={row[2]}")

# Test 3: IS NULL first, then priority
print("\n3. IS NULL first approach:")
cursor.execute('''
SELECT title, priority
FROM tasks
ORDER BY priority IS NULL, priority, expires_at
''')
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
