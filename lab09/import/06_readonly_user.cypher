// 06 — read-only користувач для text-to-Cypher.
    // Виконувати в базі `system` (:use system). Працює в Neo4j Enterprise (Neo4j Desktop містить
    // Enterprise Edition для розробки). У Community Edition ролей немає — тоді t2c.py
    // використовує транзакції в режимі READ (сервер відхиляє будь-який запис).
    CREATE USER t2c IF NOT EXISTS SET PASSWORD 'readonly-t2c' CHANGE NOT REQUIRED;
    GRANT ROLE reader TO t2c;
    SHOW USERS;
    