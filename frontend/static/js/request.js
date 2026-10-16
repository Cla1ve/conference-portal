// Форма новой заявки

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('request-form');
    const today = new Date().toISOString().slice(0, 10);
    form.elements.date.min = today;

    liveValidate(form, function (name, value) {
        if (name === 'event_name' && value.length < 3) return 'Название мероприятия: от 3 до 200 символов';
        if (name === 'date' && !value) return 'Укажите дату';
        if (name === 'date' && value < today) return 'Дата не может быть в прошлом';
        if (name === 'start_time' && !value) return 'Укажите время начала';
        if (name === 'room_id' && !value) return 'Выберите помещение из списка';
        if (name === 'payment_method_id' && !value) return 'Выберите способ оплаты из списка';
        return '';
    });

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        const data = formData(form);
        const errors = {};

        if (data.event_name.length < 3) errors.event_name = 'Название мероприятия: от 3 до 200 символов';
        if (!data.date) errors.date = 'Укажите дату';
        else if (data.date < today) errors.date = 'Дата не может быть в прошлом';
        if (!data.start_time) errors.start_time = 'Укажите время начала';
        if (!data.room_id) errors.room_id = 'Выберите помещение из списка';
        if (!data.payment_method_id) errors.payment_method_id = 'Выберите способ оплаты из списка';

        if (Object.keys(errors).length) {
            showErrors(form, errors);
            return;
        }
        clearErrors(form);

        const button = form.querySelector('button[type="submit"]');
        await withBusy(button, async function () {
            data.room_id = Number(data.room_id);
            data.payment_method_id = Number(data.payment_method_id);
            const editId = form.dataset.edit;
            const res = editId ? await api('/api/requests/' + editId, 'PUT', data) : await api('/api/requests', 'POST', data);
            if (res.success) {
                toast(editId ? 'Изменения сохранены' : 'Заявка отправлена', 'ok');
                setTimeout(function () { location.href = res.redirect; }, 900);
            } else {
                showErrors(form, res.errors);
                if (!res.errors) form.querySelector('.form-error').textContent = res.message;
            }
        });
    });
});
