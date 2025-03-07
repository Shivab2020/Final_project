$(document).ready(function() {
    // Handle outbound call form submission
    $('#outboundCallForm').submit(function(e) {
        e.preventDefault();
        
        const formData = {
            phone_number: $('input[name="phone_number"]').val(),
            purpose: $('select[name="purpose"]').val()
        };

        $.ajax({
            url: '/make-call',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                alert('Call initiated successfully!');
                loadCallHistory();
            },
            error: function(error) {
                alert('Error making call');
            }
        });
    });

    function loadCallHistory() {
        $.get('/call-history', function(data) {
            $('#callHistory').empty();
            data.forEach(call => {
                $('#callHistory').append(`
                    <tr>
                        <td>${new Date(call.timestamp).toLocaleString()}</td>
                        <td>${call.direction}</td>
                        <td>${call.phone_number}</td>
                        <td>${call.call_duration || 'N/A'}</td>
                        <td>${call.recording_url ? 
                            `<audio controls src="${call.recording_url}"></audio>` : 
                            'No recording'}</td>
                    </tr>
                `);
            });
        });
    }

    // Load call history on page load
    loadCallHistory();
    // Refresh every 30 seconds
    setInterval(loadCallHistory, 30000);
}); 