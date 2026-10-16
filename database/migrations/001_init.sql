-- Версия 1 схемы БД: портал "Конференции.РФ"
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    login         VARCHAR(30)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    fio           VARCHAR(150) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    phone         VARCHAR(18)  NOT NULL,
    role          VARCHAR(10)  NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin'))
);

CREATE TABLE IF NOT EXISTS status (
    id   INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT OR IGNORE INTO status (id, name) VALUES
    (1, 'Новая'),
    (2, 'Мероприятие назначено'),
    (3, 'Завершено');

CREATE TABLE IF NOT EXISTS event (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(200) NOT NULL,
    date        DATE         NOT NULL,
    start_time  VARCHAR(5)   NOT NULL,
    place       VARCHAR(50)  NOT NULL,
    description TEXT         NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS request (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER     NOT NULL REFERENCES user(id),
    event_id       INTEGER     NOT NULL REFERENCES event(id),
    status_id      INTEGER     NOT NULL DEFAULT 1 REFERENCES status(id),
    payment_method VARCHAR(30) NOT NULL,
    created_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER  NOT NULL UNIQUE REFERENCES request(id),
    text       TEXT     NOT NULL CHECK (length(text) BETWEEN 1 AND 2000),
    rating     INTEGER  NOT NULL CHECK (rating BETWEEN 1 AND 5),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_request_user   ON request(user_id);
CREATE INDEX IF NOT EXISTS idx_request_status ON request(status_id);
