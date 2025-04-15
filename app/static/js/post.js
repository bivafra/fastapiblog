// function getCookie(name) {
//     return document.cookie
//         .split(';')
//         .map(cookie => cookie.trim())
//         .find(cookie => cookie.startsWith(`${name}=`))
//         ?.split('=')[1] || null;
// }

async function sendRequest(url, method, body = null) {
    const headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    };

    try {
        const response = await fetch(url, {
            method,
            headers,
            credentials: 'include',
            body: body ? JSON.stringify(body) : null,
        });

        if (!response.ok) {
            let errorData = {};
            try {
                errorData = await response.json();
            } catch (jsonError) {
                console.error('Error of JSON parsing:', jsonError);
            }
            throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        if (error.name === 'TypeError') {
            console.error('Network or CORS error:', error);
        }
        console.error(`Request error: ${error.message}`);
        throw error;
    }
}


async function deletePost({id}) {
    try {
        await sendRequest(`/api/posts/${id}`, 'DELETE', null);
        alert('Post successfully deleted. Redirecting...');
        window.location.href = '/posts';
    } catch (error) {
        console.error('Error occured while creating post:', error);
    }
}


async function changePostStatus({id}, newStatus) {
    try {
        const url = `/api/posts/${id}?new_status=${encodeURIComponent(newStatus)}`;
        await sendRequest(url, 'PATCH', null);
        alert('Status has been successfully changed.');
        location.reload();
    } catch (error) {
        console.error('Error occureed while changing post status:', error);
        alert('Error occureed while changing post status. Try again.');
    }
}


document.addEventListener('DOMContentLoaded', () => {
    const articleContainer = document.querySelector('.article-container');
    if (!articleContainer) {
        console.error('Element .article-container not found. Ensure it exists in DOM.');
        return;
    }

    const POST_DATA = {
        id: articleContainer.dataset.postId,
        status: articleContainer.dataset.postStatus,
        author: articleContainer.dataset.postAuthor,
        // token: getCookie('user_access_token'),
    };

    console.log('POST_DATA:', POST_DATA);

    const deleteButton = document.querySelector('[data-action="delete"]');
    if (deleteButton) {
        deleteButton.addEventListener('click', () => {
            if (confirm('Do you indeed want to delete this post?')) {
                deletePost(POST_DATA);
            }
        });
    }

    const statusButton = document.querySelector('[data-action="change-status"]');
    if (statusButton) {
        statusButton.addEventListener('click', () => {
            const newStatus = statusButton.dataset.newStatus;
            changePostStatus(POST_DATA, newStatus);
        });
    }
});
