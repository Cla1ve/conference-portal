// Формы входа и регистрации

const RULES = {
    login: [/^[A-Za-z0-9_]{6,30}$/, 'Логин: от 6 до 30 символов, только латиница, цифры и _'],
    password: [/^.{8,}$/, 'Пароль должен быть не короче 8 символов'],
    fio: [/^[А-Яа-яЁё-]+( [А-Яа-яЁё-]+){1,2}$/, 'ФИО: 2-3 слова кириллицей, например Иванов Иван Иванович'],
    phone: [/^8\(\d{3}\)-\d{3}-\d{2}-\d{2}$/, 'Телефон в формате 8(900)-123-45-67'],
    email: [/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/, 'Введите корректный email'],
};

// проверка на стороне клиента (на сервере всё проверяется ещё раз)
function checkForm(data, fields) {
    const errors = {};
    fields.forEach(function (name) {
        const rule = RULES[name];
        if (rule && !rule[0].test(data[name] || '')) errors[name] = rule[1];
    });
    return errors;
}

// телефон подставляем по маске, пока человек печатает
function maskPhone(input) {
    input.addEventListener('input', function () {
        let digits = input.value.replace(/\D/g, '');
        if (digits.startsWith('8')) digits = digits.slice(1);
        digits = digits.slice(0, 10);
        let out = '8';
        if (digits.length > 0) out += '(' + digits.slice(0, 3);
        if (digits.length >= 3) out += ')';
        if (digits.length > 3) out += '-' + digits.slice(3, 6);
        if (digits.length > 6) out += '-' + digits.slice(6, 8);
        if (digits.length > 8) out += '-' + digits.slice(8, 10);
        input.value = digits.length ? out : '';
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (registerForm) maskPhone(registerForm.elements.phone);

    [loginForm, registerForm].forEach(function (form) {
        if (!form) return;
        const isLogin = form === loginForm;
        form.addEventListener('submit', async function (event) {
            event.preventDefault();
            const data = formData(form);
            let errors = {};
            if (isLogin) {
                // при входе формат не проверяем, только что поля не пустые
                if (!data.login) errors.login = 'Введите логин';
                if (!data.password) errors.password = 'Введите пароль';
            } else {
                errors = checkForm(data, ['login', 'password', 'fio', 'phone', 'email']);
            }
            if (Object.keys(errors).length) {
                showErrors(form, errors);
                return;
            }
            const button = form.querySelector('button[type="submit"]');
            await withBusy(button, async function () {
                const res = await api(isLogin ? '/api/login' : '/api/register', 'POST', data);
                if (res.success) {
                    if (isLogin) {
                        location.href = res.redirect;
                    } else {
                        toast('Регистрация прошла успешно, теперь войдите', 'ok');
                        setTimeout(function () { location.href = '/login'; }, 1200);
                    }
                } else {
                    showErrors(form, res.errors);
                    form.querySelector('.form-error').textContent = res.errors ? '' : res.message;
                }
            });
        });
    });
});
