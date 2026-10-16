// Общие функции для всех страниц

function csrfToken() {
    return document.querySelector('meta[name="csrf-token"]').content;
}

// запрос к API, возвращает уже разобранный JSON
async function api(url, method, body) {
    const options = {
        method: method || 'GET',
        headers: { 'X-CSRF-Token': csrfToken() },
    };
    if (body !== undefined) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        data.status = response.status;
        return data;
    } catch (err) {
        console.error('Ошибка запроса', url, err);
        return { success: false, message: 'Нет связи с сервером. Попробуйте позже.', status: 0 };
    }
}

// всплывающее сообщение (type: ok, error или пусто)
function toast(message, type) {
    const box = document.getElementById('toasts');
    const item = document.createElement('div');
    item.className = 'toast ' + (type || '');
    item.textContent = message;
    box.appendChild(item);
    setTimeout(function () {
        item.classList.add('hide');
        setTimeout(function () { item.remove(); }, 300);
    }, 3500);
}

// показать ошибки под полями формы
function showErrors(form, errors) {
    clearErrors(form);
    Object.keys(errors || {}).forEach(function (name) {
        const holder = form.querySelector('[data-error-for="' + name + '"]');
        if (holder) {
            holder.textContent = errors[name];
            const field = holder.closest('.field');
            if (field) field.classList.add('invalid');
        }
    });
}

function clearErrors(form) {
    form.querySelectorAll('.error').forEach(function (e) { e.textContent = ''; });
    form.querySelectorAll('.field.invalid').forEach(function (f) { f.classList.remove('invalid'); });
    const common = form.querySelector('.form-error');
    if (common) common.textContent = '';
}

// проверка одного поля, когда человек из него вышел (check вернёт текст ошибки или пустую строку)
function liveValidate(form, check) {
    form.querySelectorAll('input, select, textarea').forEach(function (field) {
        field.addEventListener('blur', function () {
            const message = check(field.name, field.value.trim(), formData(form));
            const holder = form.querySelector('[data-error-for="' + field.name + '"]');
            if (!holder) return;
            holder.textContent = message || '';
            field.closest('.field').classList.toggle('invalid', Boolean(message));
        });
        // как только поле исправили, ошибку убираем
        field.addEventListener('input', function () {
            const holder = form.querySelector('[data-error-for="' + field.name + '"]');
            if (holder && holder.textContent && !check(field.name, field.value.trim(), formData(form))) {
                holder.textContent = '';
                field.closest('.field').classList.remove('invalid');
            }
        });
    });
}

function formData(form) {
    const result = {};
    new FormData(form).forEach(function (value, key) { result[key] = value.trim ? value.trim() : value; });
    return result;
}

// блокируем кнопку на время запроса, чтобы не отправить форму дважды
async function withBusy(button, action) {
    button.disabled = true;
    try {
        return await action();
    } finally {
        button.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const logout = document.getElementById('logout-btn');
    if (logout) {
        logout.addEventListener('click', async function () {
            const res = await api('/api/logout', 'POST', {});
            location.href = res.redirect || '/login';
        });
    }

    // мобильное меню
    const burger = document.getElementById('burger');
    const nav = document.getElementById('nav');
    if (burger && nav) {
        burger.addEventListener('click', function () {
            const open = nav.classList.toggle('open');
            burger.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
    }

    // плавный уход со страницы при переходе по внутренней ссылке
    document.addEventListener('click', function (event) {
        const link = event.target.closest('a[href^="/"]');
        if (!link || event.ctrlKey || event.metaKey || link.target === '_blank') return;
        event.preventDefault();
        const page = document.querySelector('.page');
        if (page) page.classList.add('leaving');
        setTimeout(function () { location.href = link.getAttribute('href'); }, 160);
    });
});

// цифры в блоке статистики плавно набираются от нуля
document.addEventListener('DOMContentLoaded', function () {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    document.querySelectorAll('.stat-num').forEach(function (num) {
        const target = parseInt(num.textContent, 10);
        if (!target) return;
        const start = performance.now();
        const duration = 700;
        function step(now) {
            const k = Math.min((now - start) / duration, 1);
            num.textContent = Math.round(target * k);
            if (k < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    });
});
