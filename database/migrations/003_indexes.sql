-- Практика 15: индексы под запросы, которые на большой базе шли полным перебором таблицы.

-- удаление заявки проверяет, остались ли другие заявки на это мероприятие, и JOIN идёт по event_id
CREATE INDEX IF NOT EXISTS idx_request_event ON request(event_id);

-- фильтр по дате в админ-панели
CREATE INDEX IF NOT EXISTS idx_event_date ON event(date);

-- фильтр по помещению вместе с датой
CREATE INDEX IF NOT EXISTS idx_event_room_date ON event(room_id, date);
