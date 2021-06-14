"use strict";

function deleteTask(id) {
    if (!confirm(`Удалить задание с id ${id}?`))
        return;

    fetch(`/api-lms/task/${id}/`, {
        method: 'DELETE',
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': getCook('csrftoken'),
        }
    }).then(response => {
        if (response.status === 204) {
            showMessage(`Задача с ${id} удалена}`);
            document.getElementById('task_id_' + id).remove();
        } else {
            showMessage('Удалить не получилось');
        }
    }).catch(err => console.log(err))
}

function evaluateTask(task_answer_id) {
    const confirm_deletion = confirm(`Поставить ${task_answer_id} оценку ${mark}?`);
    if (!confirm_deletion) return;

    const mark = document.getElementById('mark_id_'+task_answer_id).value;
    const text = document.getElementById('text_id_'+task_answer_id).value;
    const body = {
        "mark": mark,
        "review": text,
    }

    const URL = '/api-lms/task-answer-evaluate/';
    const csrftoken = getCook('csrftoken'); // sessionid

    fetch(`${URL}${task_answer_id}/`, {
        method: 'PUT',
        body: JSON.stringify(body),
        headers: {
            'Content-Type': 'application/json',
            'mode': 'same-origin',
            'X-CSRFToken': csrftoken,
        }
    }).then(response => {
        console.log(response);
        if (response.status === 200) {
            showMessage('Оценка поставлена')
        } else {
            response.json().then(json => {
                showMessage('Ошибка: '+json);
            })
        }
    }).catch(err => console.log(err))
}

// todo
function deleteTaskMark(id) {
    const confirm_deletion = confirm(`Удалить оценку с id ${id}?`);
    if (!confirm_deletion) return;

    // https://docs.djangoproject.com/en/3.2/ref/csrf/#ajax
    const csrftoken = getCook('csrftoken'); // sessionid

    fetch('', {
        method: 'DELETE',
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': csrftoken,
        }
    }).then(response => {
        if (response.status === 204) {
            showMessage(`Оценка с ${id} удалена}`);
            document.getElementById('id_task_answer_' + id).remove();
        }
    }).catch(err => console.log(err))
}

function createTaskTest(task_id) {
    const input = document.getElementById('id_input');
    const output = document.getElementById('id_output');

    const body = {
        "task": task_id,
        "input": input.value,
        "output": output.value,
        "hidden": true,
    }

    const URL = '/api-lms/task-test/';
    const csrftoken = getCook('csrftoken'); // sessionid

    fetch(URL, {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
            'Content-Type': 'application/json',
            'mode': 'same-origin',  // do not send CSRF token to another domain
            'X-CSRFToken': csrftoken,
        }
    }).then(response => {
        response.json().then(json => {
            if (response.status === 201) {
                const task_tests = document.getElementById('id_task_tests');    
                const div = document.createElement('div');
                div.id = 'id_task_test_' + json.id;
                
                const input_new = document.createElement('textarea');
                const output_new = document.createElement('textarea');
                input_new.value = json.input;
                output_new.value = json.output;
                input_new.readOnly = true;
                output_new.readOnly = true;
                input_new.rows = output_new.rows = 10;
                input_new.cols = output_new.cols = 50;

                // кнопка удалить тест
                const but = document.createElement('button');
                but.onclick = () => { deleteTaskTest(json.id) };
                but.textContent = 'Удалить';

                div.appendChild(input_new);
                div.appendChild(output_new);
                div.appendChild(document.createElement('br'));
                div.appendChild(but);
                
                task_tests.appendChild(div);
    
                showMessage('Тест создан');
            } else {
                showMessage('Ошибка.' + 'Output: ' + json.output, 5000);
            }
        })
    }).catch(err => console.log(err))
}

function deleteTaskTest(task_test_id) {
    const confirm_deletion = confirm(`Удалить тест ${task_test_id}?`);
    if (!confirm_deletion) return;

    const URL = '/api-lms/task-test/'
    const csrftoken = getCook('csrftoken');

    fetch(`${URL}${task_test_id}/`, {
        method: 'DELETE',
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': csrftoken,
        }
    }).then(response => {
        console.log(response);
        if (response.status === 204) {
            showMessage('Тест к заданию удалён');
            document.getElementById('id_task_test_'+task_test_id).remove();
        }
    }).catch(err => console.log(err))
}

function addComment(task_id) {
    const text = document.getElementById('comment_text').value;
    const body = {
        "task": task_id,
        "text": text,
    }

    fetch('/api-lms/comment/', {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
            'Content-Type': 'application/json',
            'mode': 'same-origin',
            'X-CSRFToken': getCook('csrftoken'),
        }
    }).then(response => {
        console.log(response);

        if (response.status === 201) {
            // add comment on the page
            // пока перезагрузим страницу, потом нормально сделаем
            document.location.reload();
        }
    }).catch(err => console.log(err))
}

function deleteComment(id) {
    const confirm_deletion = confirm(`Удалить комментарий с id ${id}?`);
    if (!confirm_deletion) return;

    fetch(`/api-lms/comment/${id}/`, {
        method: 'DELETE',
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': getCook('csrftoken'),
        }
    }).then(response => {
        if (response.status === 204) {
            // пока перезагрузим страницу, потом нормально сделаем
            document.location.reload();
        }
    }).catch(err => console.log(err))
}

function uploadCode(task_id) {
    const csrftoken = getCook('csrftoken');
    const URL = `/api-lms/task-upload-code/${task_id}/`;

    const code = document.getElementById('id_code');
    const language = document.getElementById('id_language');

    const data = {
        "code": code.value,
        "language": language.value,
    }

    fetch(URL, {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
            'Content-Type': 'application/json',
            'mode': 'same-origin',
            'X-CSRFToken': csrftoken,
        }
    }).then(response => {
        console.log(response);
        if (response.status === 200) {
            showMessage('код загружен');
        } else {
            showMessage('ошибка загрузки кода');
        }
    }).catch((error) => {
        console.error('Error:', error);
    });
}