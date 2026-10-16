// Отзывы в личном кабинете

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.review-form').forEach(function (form) {
        form.addEventListener('submit', async function (event) {
            event.preventDefault();
            const data = formData(form);
            const holder = form.querySelector('[data-error-for="review"]');
            holder.textContent = '';

            if (!data.rating) {
                holder.textContent = 'Поставьте оценку';
                return;
            }
            if (!data.text) {
                holder.textContent = 'Напишите текст отзыва';
                return;
            }
            const button = form.querySelector('button');
            await withBusy(button, async function () {
                const res = await api('/api/requests/' + form.dataset.request + '/review', 'POST', data);
                if (res.success) {
                    toast(res.message, 'ok');
                    setTimeout(function () { location.reload(); }, 900);
                } else {
                    holder.textContent = res.message;
                }
            });
        });
    });
});
