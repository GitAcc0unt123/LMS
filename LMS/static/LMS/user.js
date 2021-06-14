"use strict";

function deleteNotification(id) {
    fetch(`/api-lms/notification/${id}/`, {
        method: 'DELETE',
        headers: {
            'mode': 'same-origin',
            'X-CSRFToken': getCook('csrftoken'),
        }
    }).then(response => {
        if (response.status === 204) {
            document.getElementById('notification_id_' + id).remove();
            showMessage('Уведомление удалено', 1000);
        }
    }).catch(err => console.log(err))
}