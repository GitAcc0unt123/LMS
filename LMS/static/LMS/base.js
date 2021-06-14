"use strict";

function getCook(cookiename) {
    // Get name followed by anything except a semicolon
    const cookiestring = RegExp(cookiename+"=[^;]+").exec(document.cookie);
    // Return everything after the equal sign, or undefined if the cookie name not found
    return decodeURIComponent(!!cookiestring ? cookiestring.toString().replace(/^[^=]+./,"") : undefined);
}

function deleteFile(id) {
    const confirm_deletion = confirm(`Удалить файл с id ${id}?`);
    if (!confirm_deletion) return;

    fetch(`/api-lms/file-delete/${id}/`, {
        method: 'DELETE',
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': getCook('csrftoken'),
        }
    }).then(response => {
        if (response.status === 204) {
            document.getElementById('file_id_' + id).remove();
            showMessage('файл удалён');

            const list = document.getElementById('file_list');
            if (list.getElementsByTagName('li').length === 0) {
                document.location.reload();
            }
        }
    }).catch(err => console.log(err))
}

// загрузить файлы на сервер
// https://learn.javascript.ru/formdata
function uploadFiles(id, is_course_element) {
    const csrftoken = getCook('csrftoken');
    const courseElementURL = '/api-lms/course-element-upload-files/';
    const taskURL = '/api-lms/task-upload-files/';

    const input = document.getElementById('id_upload_files');
    const data = new FormData();

    for (const file of input.files) {
        data.append('files', file, file.name);
    }

    fetch(`${is_course_element ? courseElementURL : taskURL}${id}/`, {
        method: 'POST',
        body: data,
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': csrftoken,
        }
    }).then(response => {
        return response.json();
    }).then(data => {
        console.log(data);
    }).catch((error) => {
        console.error('Error:', error);
    });
}

function excludeStudent(course_id, user_id, username, black_list) {
    const confirm_deletion = confirm(black_list ? `Заблокировать пользователя ${username}?` : `Исключить пользователя ${username}?`);
    if (!confirm_deletion) return;

    const csrftoken = getCook('csrftoken');
    const requestURL = '/api-lms/course_subscribers/';

    const body = {
        //"course": course_id,
        "user": user_id,
        "black_list": black_list,
    }

    fetch(`${requestURL}${course_id}/`, {
        method: 'PUT',
        body: JSON.stringify(body),
        headers: {
            'Content-Type': 'application/json',
            'mode': 'same-origin',
            'X-CSRFToken': csrftoken,
        }
    }).then(response => {
        console.log(response);
        // remove user from page
        if (response.status === 200) {
            showMessage(`пользователь ${username}` + (black_list ? 'заблокирован' : 'исключён'));
            document.getElementById('user_id_' + user_id).remove();
        } else {
            showMessage('исключить не получилось', 5000);
        }
    }).catch(err => console.log(err))
}

// создаёт всплывающее уведомление на странице
function showMessage(text, timeout=3000, color='green') {
    let message_box = document.getElementById('message-box');
    if (!message_box) {
        message_box = document.createElement('div');
        message_box.id = 'message-box';
        document.body.appendChild(message_box);
    }

    const message = document.createElement('div');
    message.classList.add('message');
    message.innerText = text;
    message.style.backgroundcolor = color;
    message_box.appendChild(message);
    setTimeout(() => {
        message.remove();
        if (message_box.childNodes.length === 0) {
            message_box.remove();
        }
    }, timeout);
}