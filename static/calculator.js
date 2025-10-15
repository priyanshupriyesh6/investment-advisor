document.getElementById('investmentType').addEventListener('change', function() {
    const incrementDiv = document.getElementById('incrementDiv');
    incrementDiv.style.display = this.value === 'floating' ? 'block' : 'none';
});

document.getElementById('investmentForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Show loading state
    const submitButton = this.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.innerHTML = 'Calculating...';
    
    const formData = {
        amount: parseFloat(document.getElementById('amount').value),
        time_period: parseInt(document.getElementById('timePeriod').value),
        investment_type: document.getElementById('investmentType').value,
        risk_tolerance: document.getElementById('riskTolerance').value,
        monthly_increment: parseFloat(document.getElementById('monthlyIncrement').value || 0)
    };

    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while calculating recommendations. Please try again.');
    } finally {
        // Reset button state
        submitButton.disabled = false;
        submitButton.innerHTML = 'Calculate';
    }
});

function displayResults(data) {
    const results = document.getElementById('results');
    const summaryText = document.getElementById('summaryText');
    const recommendationsText = document.getElementById('recommendationsText');
    
    if (!data || !data.advice || !data.advice.asset_allocation) {
        console.error('Invalid data structure received:', data);
        alert('Invalid data received from server');
        return;
    }
    
    // Show results container with animation
    results.style.opacity = '0';
    results.style.display = 'block';
    setTimeout(() => {
        results.style.opacity = '1';
    }, 100);
    
    // Create pie chart for asset allocation
    const allocation = data.advice.asset_allocation;
    const pieData = [{
        values: [
            allocation.stocks.percentage * 100,
            allocation.mutual_funds.percentage * 100,
            allocation.bonds.percentage * 100,
            allocation.cash.percentage * 100
        ],
        labels: ['Stocks', 'Mutual Funds', 'Bonds', 'Cash'],
        type: 'pie',
        marker: {
            colors: ['#2E86DE', '#10AC84', '#5758BB', '#FFA502']
        },
        textinfo: 'label+percent',
        hoverinfo: 'label+value+percent'
    }];
    
    const layout = {
        height: 400,
        title: {
            text: 'Recommended Asset Allocation',
            font: {
                size: 20,
                family: 'Arial, sans-serif'
            }
        },
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.1
        },
        margin: {
            l: 50,
            r: 50,
            t: 50,
            b: 50
        }
    };
    
    Plotly.newPlot('summaryChart', pieData, layout);
    
    // Display summary
    // Display summary with animation
    summaryText.innerHTML = `
        <div class="alert alert-success">
            <h4 class="alert-heading">Investment Summary</h4>
            <p class="mb-0">Expected total value after ${data.advice.time_period} years: 
                <strong>₹${numberWithCommas(Math.round(data.advice.total_expected_value))}</strong></p>
        </div>
    `;
    
    // Display detailed recommendations
    let recommendationsHtml = `<div class="recommendation-container">`;
    
    // Add strategy sections
    for (const section in data.strategy) {
        if (section !== 'overview') {
            recommendationsHtml += `
                <div class="recommendations-section ${section}-section">
                    ${data.strategy[section].replace(/\n/g, '<br>')}
                </div>
            `;
        }
    }
    
    recommendationsHtml += '</div>';
    recommendationsText.innerHTML = recommendationsHtml;
    
    // Add smooth scroll to results
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}