const { createApp } = Vue

createApp({
    data() {
        return {
            stats: {
                totalCalls: 0,
                successRate: 0,
                avgDuration: '0:00'
            },
            newCall: {
                phone: '',
                businessType: 'hospital',
                purpose: ''
            },
            calls: []
        }
    },
    methods: {
        async makeCall() {
            try {
                const response = await fetch('/api/calls.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        phone_number: this.newCall.phone,
                        business_type: this.newCall.businessType,
                        purpose: this.newCall.purpose
                    })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    this.loadCalls();
                    this.newCall.phone = '';
                    this.newCall.purpose = '';
                    alert('Call initiated successfully!');
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                console.error('Error making call:', error);
                alert('Error making call. Please try again.');
            }
        },
        async handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/api/upload.php', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (data.status === 'success') {
                    this.loadCalls();
                    alert(`Successfully processed ${data.total_processed} numbers!`);
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                console.error('Error uploading file:', error);
                alert('Error uploading file. Please try again.');
            }
        },
        async loadCalls() {
            try {
                const response = await fetch('/api/calls.php');
                const data = await response.json();
                if (data.status === 'success') {
                    this.calls = data.data;
                    this.updateStats();
                }
            } catch (error) {
                console.error('Error loading calls:', error);
            }
        },
        updateStats() {
            this.stats.totalCalls = this.calls.length;
            const completed = this.calls.filter(call => call.status === 'completed').length;
            this.stats.successRate = Math.round((completed / this.calls.length) * 100) || 0;
            
            const durations = this.calls.map(call => parseInt(call.duration) || 0);
            const avgSeconds = durations.length ? 
                Math.round(durations.reduce((a, b) => a + b) / durations.length) : 0;
            this.stats.avgDuration = `${Math.floor(avgSeconds / 60)}:${String(avgSeconds % 60).padStart(2, '0')}`;
        },
        formatDate(dateString) {
            return new Date(dateString).toLocaleDateString();
        },
        formatDuration(seconds) {
            if (!seconds) return '0:00';
            return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
        }
    },
    mounted() {
        this.loadCalls();
        // Refresh calls every 30 seconds
        setInterval(this.loadCalls, 30000);
    }
}).mount('#app') 