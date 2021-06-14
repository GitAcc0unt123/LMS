"use strict";

function deleteCourseElement(id) {
    const confirm_deletion = confirm(`Удалить элемент курса с id ${id}?`);
    if (!confirm_deletion) return;

    fetch(`/api-lms/course-element/${id}/`, {
        method: 'DELETE',
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': getCook('csrftoken'),
        }
    }).then(response => {
        document.getElementById('course_element_id_' + id).remove();
        showMessage('Элемент курса удалён');
    }).catch(err => console.log(err))
}