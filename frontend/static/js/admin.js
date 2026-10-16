// Панель администратора: карточки заявок, фильтры, смена статуса

const NEXT_STATUS = { 1: 'Назначить мероприятие', 2: 'Завершить' };

function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;   // textContent, чтобы не вставлять чужой HTML
    return node;
}

function row(dl, name, value) {
    const wrap = el('div');
    wrap.appendChild(el('dt', '', name));
    wrap.appendChild(el('dd', '', value));
    dl.appendChild(wrap);
}

function renderCard(item) {
    const card = el('article', 'card');
    const top = el('div', 'card-top');
    top.appendChild(el('span', 'status status-' + item.status_id, item.status));
    top.appendChild(el('span', 'muted', '№ ' + item.id));
    card.appendChild(top);
    card.appendChild(el('h3', '', item.event_name));
    card.appendChild(el('div', 'user-line', item.fio + ' (' + item.login + ')'));

    const dl = el('dl', 'meta');
    row(dl, 'Дата', item.date + ', ' + item.start_time);
    row(dl, 'Помещение', item.room);
    row(dl, 'Оплата', item.payment);
    card.appendChild(dl);

    if (item.review_id) {
        const review = el('div', 'review-done');
        review.appendChild(el('strong', '', 'Отзыв: ' + '★'.repeat(item.review_rating) + '☆'.repeat(5 - item.review_rating)));
        review.appendChild(el('p', '', item.review_text));
        card.appendChild(review);
    }

    if (NEXT_STATUS[item.status_id]) {
        const actions = el('div', 'card-actions');
        const btn = el('button', 'btn btn-small', NEXT_STATUS[item.status_id]);
        btn.type = 'button';
        btn.addEventListener('click', function () { changeStatus(item, btn); });
        actions.appendChild(btn);
        card.appendChild(actions);
    }
    return card;
}

async function changeStatus(item, button) {
    await withBusy(button, async function () {
        const res = await api('/api/admin/requests/' + item.id + '/status', 'POST', { status_id: item.status_id + 1 });
        if (res.success) {
            toast('Статус заявки № ' + item.id + ' изменён', 'ok');
            loadRequests();
        } else {
            toast(res.message, 'error');
        }
    });
}

async function loadRequests() {
    const form = document.getElementById('filters');
    const params = new URLSearchParams(new FormData(form));
    // пустые параметры не отправляем
    Array.from(params.keys()).forEach(function (key) { if (!params.get(key)) params.delete(key); });

    const res = await api('/api/admin/requests?' + params.toString());
    const box = document.getElementById('admin-cards');
    box.textContent = '';
    if (!res.success) {
        toast(res.message || 'Не удалось загрузить заявки', 'error');
        return;
    }
    res.items.forEach(function (item) { box.appendChild(renderCard(item)); });
    document.getElementById('empty-msg').hidden = res.items.length > 0;
    document.getElementById('counter').textContent = 'Найдено: ' + res.items.length;
}

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('filters');
    let timer = null;
    form.addEventListener('change', loadRequests);
    // в поиске ждём паузу в наборе, чтобы не слать запрос на каждую букву
    form.elements.q.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(loadRequests, 300);
    });
    form.addEventListener('reset', function () { setTimeout(loadRequests, 0); });
    loadRequests();
});
