
import os

def fix_dashboard():
    file_path = 'dashboard.html'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the line where loadData starts
    start_index = -1
    for i, line in enumerate(lines):
        if 'async function loadData() {' in line:
            start_index = i
            break
            
    if start_index == -1:
        print("Could not find start index")
        return

    # Keep everything before loadData
    new_lines = lines[:start_index]
    
    # Append the corrected code
    new_script = """        async function loadData() {
            clearError();
            document.getElementById('loading').style.display = 'block';
            document.getElementById('content').style.display = 'none';

            try {
                const ts = new Date().getTime(); // Cache busting
                // Load portfolio data
                const portfolioResponse = await fetch('data/portfolio.json?t=' + ts);
                if (!portfolioResponse.ok) {
                    throw new Error('Fehler beim Laden der Portfolio-Daten');
                }
                const portfolio = await portfolioResponse.json();

                // Load trade log for historical data
                const tradeLogResponse = await fetch('data/trade_log.csv?t=' + ts);
                if (!tradeLogResponse.ok) {
                    throw new Error('Fehler beim Laden der Handelshistorie');
                }
                const tradeLogText = await tradeLogResponse.text();

                // Load benchmark data
                let benchmarkData = null;
                try {
                    const benchmarkResponse = await fetch('data/benchmark.json?t=' + ts);
                    if (benchmarkResponse.ok) {
                        benchmarkData = await benchmarkResponse.json();
                    }
                } catch (e) {
                    console.log('Benchmark data not available');
                }

                updateStats(portfolio, benchmarkData, tradeLogText);
                updateChart(portfolio, benchmarkData);
                updateHoldings(portfolio, tradeLogText);

                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'block';
            } catch (error) {
                console.error('Error loading data:', error);
                showError(error.message);
                document.getElementById('loading').style.display = 'none';
            }
        }

        function updateStats(portfolio, benchmarkData, tradeLogText) {
            let totalValue = portfolio.total_value || 0;
            let cash = portfolio.cash || 0;
            let profitLoss = portfolio.profit_loss || 0;
            let returnPct = portfolio.return_pct || 0;
            const holdings = portfolio.holdings || {};

            // Calculate invested amount based on reported values
            let investedAmount = totalValue - cash;

            // FIX: If total_value equals cash but we have holdings, the backend calculation is wrong.
            // Recalculate based on recent trade prices logic.
            if (holdings && Object.keys(holdings).length > 0 && Math.abs(totalValue - cash) < 1) {
                console.warn("Backend reported total_value equals cash, but holdings exist. Recalculating...");
                
                const prices = parseTradeLog(tradeLogText);
                let calculatedInvested = 0;
                
                Object.entries(holdings).forEach(([ticker, quantity]) => {
                    // Use last known price from trade log
                    const price = prices[ticker] || 0;
                    calculatedInvested += quantity * price;
                });
                
                if (calculatedInvested > 0) {
                    investedAmount = calculatedInvested;
                    // Recalculate Total Value as Cash + Invested
                    totalValue = cash + investedAmount;
                    
                    // Recalculate Return/PL roughly based on initial 10k
                    const initialCapital = 10000;
                    profitLoss = totalValue - initialCapital;
                    returnPct = (profitLoss / initialCapital) * 100;
                }
            }
            
            // Total value
            document.getElementById('totalValue').textContent = formatCurrency(totalValue);
            const totalChangeEl = document.getElementById('totalChange');
            totalChangeEl.textContent = formatPercent(returnPct);
            totalChangeEl.className = `stat-change ${returnPct >= 0 ? 'positive' : 'negative'}`;

            // Cash
            document.getElementById('cashValue').textContent = formatCurrency(cash);
            const cashPct = totalValue > 0 ? (cash / totalValue * 100) : 0;
            document.getElementById('cashPercent').textContent = `${cashPct.toFixed(1)}% des Portfolios`;

            // Invested
            document.getElementById('investedValue').textContent = formatCurrency(investedAmount);
            const investedPct = totalValue > 0 ? (investedAmount / totalValue * 100) : 0;
            document.getElementById('investedPercent').textContent = `${investedPct.toFixed(1)}% des Portfolios`;

            // Profit/Loss
            const profitLossEl = document.getElementById('profitLoss');
            profitLossEl.textContent = formatCurrency(profitLoss);
            profitLossEl.className = `stat-value ${profitLoss >= 0 ? '' : ''}`;
            profitLossEl.style.color = profitLoss >= 0 ? 'var(--success)' : 'var(--danger)';
            
            const returnPercentEl = document.getElementById('returnPercent');
            returnPercentEl.textContent = formatPercent(returnPct);
            returnPercentEl.className = `stat-change ${returnPct >= 0 ? 'positive' : 'negative'}`;
        }

        function updateChart(portfolio, benchmarkData) {
            const ctx = document.getElementById('portfolioChart').getContext('2d');

            // Prepare chart data
            let labels = [];
            let portfolioData = [];
            let benchmarkChartData = [];

            // Initial investment
            const initialInvestment = 10000;
            
            if (benchmarkData && benchmarkData.history && benchmarkData.history.length > 0) {
                // Use benchmark history if available
                labels.push('Start');
                portfolioData.push(initialInvestment);
                benchmarkChartData.push(initialInvestment);

                benchmarkData.history.forEach((entry, index) => {
                    const date = new Date(entry.date);
                    labels.push(date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }));
                    
                    // Use actual values from benchmark tracking
                    portfolioData.push(entry.portfolio_value);
                    benchmarkChartData.push(entry.benchmark_value);
                });
            } else {
                // Fallback: show current state only
                labels = ['Start', 'Aktuell'];
                const currentTotal = portfolio.total_value || initialInvestment;
                portfolioData = [initialInvestment, currentTotal];
                benchmarkChartData = [initialInvestment, initialInvestment];
            }

            // Destroy existing chart if it exists
            if (chart) {
                chart.destroy();
            }

            // Create new chart
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Portfolio-Wert',
                            data: portfolioData,
                            borderColor: 'hsl(220, 90%, 56%)',
                            backgroundColor: 'rgba(59, 130, 246, 0.15)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            pointBackgroundColor: 'hsl(220, 90%, 56%)',
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2
                        },
                        {
                            label: 'MSCI World (Benchmark)',
                            data: benchmarkChartData,
                            borderColor: 'hsl(280, 90%, 60%)',
                            backgroundColor: 'rgba(192, 132, 252, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            pointBackgroundColor: 'hsl(280, 90%, 60%)',
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: 'hsl(0, 0%, 70%)',
                                font: {
                                    size: 12,
                                    weight: '600'
                                },
                                padding: 15,
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: 'hsl(0, 0%, 95%)',
                            bodyColor: 'hsl(0, 0%, 85%)',
                            borderColor: 'hsl(220, 18%, 22%)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: true,
                            callbacks: {
                                label: function (context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    label += formatCurrency(context.parsed.y);
                                    
                                    // Add return percentage for data points after start
                                    const dataIndex = context.dataIndex;
                                    if (dataIndex > 0) {
                                        const startValue = context.dataset.data[0];
                                        const currentValue = context.parsed.y;
                                        if (startValue && startValue > 0) {
                                            const returnPct = ((currentValue - startValue) / startValue * 100);
                                            label += ' (' + (returnPct >= 0 ? '+' : '') + returnPct.toFixed(2) + '%)';
                                        }
                                    }
                                    
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            grid: {
                                color: 'hsl(220, 18%, 18%)',
                                drawBorder: false
                            },
                            ticks: {
                                color: 'hsl(0, 0%, 70%)',
                                callback: function (value) {
                                    return formatCurrency(value);
                                }
                            }
                        },
                        x: {
                            grid: {
                                display: false,
                                drawBorder: false
                            },
                            ticks: {
                                color: 'hsl(0, 0%, 70%)',
                                maxRotation: 45,
                                minRotation: 0
                            }
                        }
                    }
                }
            });
        }

        function updateHoldings(portfolio, tradeLogText) {
            const holdingsGrid = document.getElementById('holdingsGrid');
            const holdings = portfolio.holdings || {};

            if (Object.keys(holdings).length === 0) {
                holdingsGrid.innerHTML = '<div class="empty-state">Keine Aktien im Portfolio</div>';
                return;
            }

            // Parse trade log to get prices
            const prices = parseTradeLog(tradeLogText);

            // Calculate total invested value for percentages
            let totalInvested = 0;
            Object.entries(holdings).forEach(([ticker, quantity]) => {
                const price = prices[ticker] || 0;
                totalInvested += quantity * price;
            });

            let holdingsHTML = '';
            Object.entries(holdings).forEach(([ticker, quantity]) => {
                const price = prices[ticker] || 0;
                const value = quantity * price;
                const allocation = totalInvested > 0 ? (value / totalInvested * 100) : 0;

                holdingsHTML += `
                    <div class="holding-item">
                        <div>
                            <div class="holding-ticker">${ticker}</div>
                        </div>
                        <div class="holding-quantity">
                            <div class="holding-label">Anzahl</div>
                            <div>${quantity}</div>
                        </div>
                        <div class="holding-value">
                            <div class="holding-label">Wert</div>
                            <div>${formatCurrency(value)}</div>
                        </div>
                        <div class="holding-allocation">
                            <div class="holding-label">Anteil</div>
                            <div>${allocation.toFixed(1)}%</div>
                        </div>
                    </div>
                `;
            });

            holdingsGrid.innerHTML = holdingsHTML;
        }

        function parseTradeLog(csvText) {
            const prices = {};
            const lines = csvText.trim().split('\\n');

            // Skip header
            for (let i = 1; i < lines.length; i++) {
                const line = lines[i].trim();
                if (!line) continue;

                const parts = line.split(',');
                if (parts.length >= 5) {
                    const ticker = parts[1];
                    const price = parseFloat(parts[4]);
                    if (ticker && !isNaN(price)) {
                        prices[ticker] = price;
                    }
                }
            }

            return prices;
        }
        
        // Load data on page load
        loadData();

        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
"""
    new_lines.append(new_script)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print("Dashboard fixed successfully")

if __name__ == '__main__':
    fix_dashboard()
