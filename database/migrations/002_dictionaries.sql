-- Версия 2 схемы (практика 12): справочники помещений и способов оплаты
-- и журнал смены статусов заявок.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS room (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS payment_method (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS status_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER  NOT NULL REFERENCES request(id) ON DELETE CASCADE,
    status_id  INTEGER  NOT NULL REFERENCES status(id),
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by INTEGER  REFERENCES user(id)
);

-- переносим старые значения в справочники
INSERT OR IGNORE INTO room (name) SELECT DISTINCT place FROM event;
INSERT OR IGNORE INTO payment_method (name) SELECT DISTINCT payment_method FROM request;

ALTER TABLE event   ADD COLUMN room_id INTEGER REFERENCES room(id);
ALTER TABLE request ADD COLUMN payment_method_id INTEGER REFERENCES payment_method(id);

UPDATE event   SET room_id = (SELECT id FROM room WHERE room.name = event.place);
UPDATE request SET payment_method_id = (SELECT id FROM payment_method WHERE payment_method.name = request.payment_method);

-- у каждой существующей заявки в журнале появляется запись с текущим статусом
INSERT INTO status_history (request_id, status_id, changed_at)
SELECT id, status_id, created_at FROM request;

CREATE INDEX IF NOT EXISTS idx_event_room        ON event(room_id);
CREATE INDEX IF NOT EXISTS idx_request_payment   ON request(payment_method_id);
CREATE INDEX IF NOT EXISTS idx_history_request   ON status_history(request_id);

-- старые текстовые колонки больше не нужны
ALTER TABLE event   DROP COLUMN place;
ALTER TABLE request DROP COLUMN payment_method;
