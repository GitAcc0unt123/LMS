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
function uploadFilesCourseElement(id) {
    const input = document.getElementById('id_upload_files');
    const data = new FormData();

    for (const file of input.files) {
        data.append('files', file, file.name);
    }

    fetch(`/api-lms/course-element-upload-files/${id}/`, {
        method: 'POST',
        body: data,
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': getCook('csrftoken'),
        }
    }).then(response => {
        if (response.status === 200) {
            showMessage('Файлы загружены');
            response.json().then(json => {
                // update file list
                const course_element_div = document.getElementById('course_element_id_'+id);
                const file_list = course_element_div.querySelector('ul');
                file_list.innerHTML = "";

                for(let i=0; i < json.length; i++){
                    const file = json[i];
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    const button = document.createElement('button');
                    li.id = 'file_id_'+file.id;
                    a.href = `/files/${file.id}/${file.filename}`;
                    a.innerHTML = file.filename;
                    button.onclick = () => { deleteFile(file.id) };
                    button.textContent = 'удалить';
                    button.style = 'color: #FF0000';
                    li.appendChild(a);
                    li.appendChild(button);
                    file_list.appendChild(li);
                }
            })
        } else {
            showMessage('Ошибка');
        }
    }).catch(err => console.log(err))
}

function uploadFilesTask(id) {
    const input = document.getElementById('id_upload_files');
    const data = new FormData();

    for (const file of input.files) {
        data.append('files', file, file.name);
    }

    fetch(`/api-lms/task-upload-files/${id}/`, {
        method: 'POST',
        body: data,
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': getCook('csrftoken'),
        }
    }).then(response => {
        if (response.status === 200) {
            showMessage('Файлы загружены');
            response.json().then(json => {
                // update table
                const table = document.getElementsByTagName('table');
                const rows = table[0].rows;

                const files = json['files'];
                const ul = document.createElement('ul');
                for(let i=0; i < files.length; i++){
                    const file = files[i];
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    const div = document.createElement('div');
                    li.id = 'file_id_'+file.id;
                    a.href = `/files/${file.id}/${file.filename}`;
                    a.download=true;
                    a.innerHTML = file.filename;
                    div.onclick = () => { deleteFile(file.id) };
                    div.classList.add("cl-btn");
                    li.appendChild(a);
                    li.appendChild(div);
                    ul.appendChild(li);
                }

                rows[0].cells[1].innerHTML = 'отправлено для оценивания';
                rows[rows.length-2].cells[1].innerHTML = json['datetime_load'];
                
                const node = rows[rows.length-1].cells[1];
                while (node.hasChildNodes()) {
                    node.removeChild(node.lastChild);
                }
                node.appendChild(ul);
            })
        } else {
            showMessage('Ошибка');
        }
    }).catch(err => console.log(err))
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