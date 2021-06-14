"use strict";

function deleteTest(id) {
    const confirm_deletion = confirm(`Удалить тест с id ${id}?`);
    if (!confirm_deletion) return;

    const URL = '/api-lms/test/';
    const csrftoken = getCook('csrftoken');

    fetch(`${URL}${id}/`, {
        method: 'DELETE',
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': csrftoken,
        }   
    }).then(response => {
        if (response.status === 204) {
            document.getElementById('test_id_' + id).remove();
            showMessage('Тест удалён', 3000, 'red');
        }
    }).catch(err => console.log(err))
}

function createTest(course_element) {
    const confirm_creation = confirm('Создать тест?');
    if (!confirm_creation) return;

    const fields = [
        'title',
        'description',
        'mark_outer',
        'number_of_attempts',
        'shuffle',
        'test_type',
        'duration',
    ]
    const body = {}
    fields.forEach(x => { body[x] = document.getElementById('id_'+x).value} );

    const start_0 = document.getElementById('id_start_0').value.split('.').reverse().join('-');
    const start_1 = document.getElementById('id_start_1').value;
    const end_0 = document.getElementById('id_end_0').value.split('.').reverse().join('-');
    const end_1 = document.getElementById('id_end_1').value;

    body['course_element'] = course_element;
    body['start'] = `${start_0} ${start_1}`; // 2020-01-01 00:00:00
    body['end'] = `${end_0} ${end_1}`;
    body['questions'] = [
        //{ 'question_text':'чего надо?', 'max_mark':'5.00', 'answer_type':'many1', 'answer_values':['ty', 'yu', 'ui'], 'answer_true':[0,2] },
        //{ 'question_text':'чего надо?', 'max_mark':'3.00', 'answer_type':'free', 'answer_values':[], 'answer_true':'нет' },
    ]

    // готовим вопросы
    const questions = document.getElementById('id_questions').getElementsByClassName('question');
    for (let question of questions) {
        const res = {};

        const answer_values = question.querySelectorAll('input[type="text"]');
        const answer_true = question.querySelectorAll('input[type="checkbox"]');
        res['question_text'] = question.querySelector('textarea').value;
        res['max_mark'] = question.querySelector('input[type="number"]').value;
        res['answer_type'] = question.querySelector('select').value;

        res['answer_values'] = [];
        res['answer_true'] = [];
        for (let i=0; i < answer_values.length; i++) {
            res['answer_values'].push(answer_values[i].value);
            if (answer_true[i].checked) {
                res['answer_true'].push(i);
            }
        }
        
        if (res['answer_type'] === 'free') {
            if (res['answer_values'].length !== 1 || 0 < res['answer_true'].length) {
                alert('неправильный вопрос со свободным ответом')
                return;
            }
            res['answer_true'] = res['answer_values'][0];
            res['answer_values'] = [];
        }
        body['questions'].push(res);
    }

    console.log(JSON.stringify(body));

    fetch(requestTestURL, {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
            "Content-Type": "application/json",
            'mode': 'same-origin',
            'X-CSRFToken': getCook('csrftoken'),
        }
    }).then(response => {
        return response.json();
    }).then(data => {
        console.log(data);
    }).catch((error) => {
        console.error('Error:', error);
    });
}

function finishTest(test_result_id, test_id) {
    const confirm_deletion = confirm('Завершить тест?');
    if (!confirm_deletion) return;

    const URL = '/api-lms/test-result-complete/';
    const csrftoken = getCook('csrftoken');

    fetch(`${URL}${test_result_id}/`, {
        method: 'PATCH',
        body: {},
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': csrftoken,
        }
    }).then(response => {
        if (response.status === 200) {
            window.location.href = `/test/${test_id}`;
            showMessage('Тест завершён');
        } else {
            showMessage('Ошибка');
        }
        console.log(response);
    }).catch(err => console.log(err))
}