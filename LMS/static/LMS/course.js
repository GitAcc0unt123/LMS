function courseSubscribeState(course_id, subscribe, is_key) {
    const confirm_deletion = confirm(subscribe ? 'Записаться на курс?' : 'Покинуть курс?');
    if (!confirm_deletion) return;

    // https://docs.djangoproject.com/en/3.2/ref/csrf/#ajax
    const csrftoken = getCook('csrftoken');
    const key_field = document.getElementById('key_field');
    const body = {
        'course': course_id,
        'subscribe': subscribe
    }

    if (is_key) {
        body['key'] = key_field.value;
    }

    fetch('/api-lms/course_subscribe/', {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
            'Content-Type': 'application/json',
            'mode': 'same-origin',  // do not send CSRF token to another domain
            'X-CSRFToken': csrftoken,
        }
    }).then(response => {
        // получили ответ от сервера
        console.log(response);
        response.json().then(json => {
            if (response.status === 200){
                console.log(json);
                showMessage(json.user);
                showMessage(json.subscribe);
                setTimeout(function(){ document.location.reload(); }, 2000);
            }
        }).catch(err => {
            // получили код ошибки
            console.log(err);
            if (key_field) {
                key_field.value = '';
            }
        });
    }).catch(err => {
        // не получили ответ
        console.log(err);
    })
}