
import os

def upgrade_dashboard():
    file_path = 'dashboard.html'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
            
    # Wir suchen den Beginn des Scripts, um es komplett sauber neu zu schreiben
    # Das ist sicherer als patchen.
    start_marker = "async function loadData() {"
    end_marker = "// Auto-refresh every 30 seconds"
    
    if start_marker not in content:
        print("Konnte start_marker nicht finden.")
        return

    # Wir splitten den Content
    part1_end = content.find(start_marker)
    part1 = content[:part1_end]
    
    # Neues Script mit Performance-Berechnung und Chart-Fix
    new_script = """        async function loadData() {
            clearError();
            document.getElementById('loading').style.display = 'block';
            document.getElementById('content').style.display = 'none';

            try {
                const ts = new Date().getTime(); // Cache busting
                
                // Parallel fetching for speed
                const [portfolioRes, tradeLogRes, benchmarkRes] = await Promise.all([
                    fetch('data/portfolio.json?t=' + ts),
                    fetch('data/trade_log.csv?t=' + ts),
                    fetch('data/benchmark.json?t=' + ts).catch(() => ({ ok: false }))
                ]);

                if (!portfolioRes.ok) throw new Error('Fehler beim Laden der Portfolio-Daten');
                const portfolio = await portfolioRes.json();

                if (!tradeLogRes.ok) throw new Error('Fehler beim Laden der Handelshistorie');
                const tradeLogText = await tradeLogRes.text();

                let benchmarkData = null;
                if (benchmarkRes.ok) {
                    try {
                        benchmarkData = await benchmarkRes.json();
                    } catch (e) {
                        console.log('Benchmark data parsing failed');
                    }
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

            // FIX: If total_value reported is suspicious (equal to cash but having holdings), recalculate.
            if (holdings && Object.keys(holdings).length > 0 && Math.abs(totalValue - cash) < 1) {
                // console.warn("Recalculating total value due to backend mismatch...");
                const prices = parseCurrentPrices(tradeLogText);
                let calculatedInvested = 0;
                
                Object.entries(holdings).forEach(([ticker, quantity]) => {
                    const price = prices[ticker] || 0;
                    calculatedInvested += quantity * price;
                });
                
                if (calculatedInvested > 0) {
                    investedAmount = calculatedInvested;
                    totalValue = cash + investedAmount;
                    
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

            let labels = [];
            let portfolioData = [];
            let benchmarkChartData = [];
            const initialInvestment = 10000;

            if (benchmarkData && benchmarkData.history && benchmarkData.history.length > 0) {
                // Add Start Point
                labels.push('Start');
                portfolioData.push(initialInvestment);
                benchmarkChartData.push(initialInvestment);

                benchmarkData.history.forEach((entry) => {
                    // FIX: Filter out invalid 0 values from history
                    if (entry.portfolio_value <= 100) return; 

                    const date = new Date(entry.date);
                    labels.push(date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }));
                    
                    portfolioData.push(entry.portfolio_value);
                    benchmarkChartData.push(entry.benchmark_value);
                });
            } else {
                // Fallback
                labels = ['Start', 'Aktuell'];
                const currentTotal = (portfolio.total_value > 100) ? portfolio.total_value : initialInvestment;
                portfolioData = [initialInvestment, currentTotal];
                benchmarkChartData = [initialInvestment, initialInvestment];
            }

            if (chart) chart.destroy();

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
                            labels: { color: 'hsl(0, 0%, 70%)', usePointStyle: true, pointStyle: 'circle' }
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
                                    if (label) label += ': ';
                                    label += formatCurrency(context.parsed.y);
                                    
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
                            grid: { color: 'hsl(220, 18%, 18%)', drawBorder: false },
                            ticks: { color: 'hsl(0, 0%, 70%)', callback: (val) => formatCurrency(val) }
                        },
                        x: {
                            grid: { display: false, drawBorder: false },
                            ticks: { color: 'hsl(0, 0%, 70%)', maxRotation: 45, minRotation: 0 }
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

            // 1. Get Current Prices
            const currentPrices = parseCurrentPrices(tradeLogText);
            
            // 2. Calculate Average Buy Prices
            const avgBuyPrices = calculateAvgBuyPrices(tradeLogText);

            // Calculate total invested for allocation %
            let totalInvestedCurrentVal = 0;
            Object.entries(holdings).forEach(([ticker, quantity]) => {
                const price = currentPrices[ticker] || 0;
                totalInvestedCurrentVal += quantity * price;
            });

            let holdingsHTML = '';
            Object.entries(holdings).forEach(([ticker, quantity]) => {
                const currentPrice = currentPrices[ticker] || 0;
                const buyPrice = avgBuyPrices[ticker] || 0;
                
                const currentValue = quantity * currentPrice;
                const allocation = totalInvestedCurrentVal > 0 ? (currentValue / totalInvestedCurrentVal * 100) : 0;
                
                // Calculate Performance
                let performanceHtml = '<div style="color: var(--text-muted)">-</div>';
                if (buyPrice > 0) {
                    const diffPct = ((currentPrice - buyPrice) / buyPrice) * 100;
                    const colorClass = diffPct >= 0 ? 'positive' : 'negative';
                    const sign = diffPct >= 0 ? '+' : '';
                    const color = diffPct >= 0 ? 'var(--success)' : 'var(--danger)';
                    performanceHtml = `<div style="color: ${color}; font-weight: 600;">${sign}${diffPct.toFixed(2)}%</div>`;
                }

                holdingsHTML += `
                    <div class="holding-item" style="grid-template-columns: 1fr auto auto auto auto;">
                        <div>
                            <div class="holding-ticker">${ticker}</div>
                            <div style="font-size: 0.75rem; color: var(--text-muted);">Buy: ${formatCurrency(buyPrice)}</div>
                        </div>
                        <div class="holding-quantity">
                            <div class="holding-label">Anzahl</div>
                            <div>${quantity}</div>
                        </div>
                        <div class="holding-value">
                            <div class="holding-label">Wert</div>
                            <div>${formatCurrency(currentValue)}</div>
                        </div>
                         <div class="holding-value">
                            <div class="holding-label">Perf.</div>
                            ${performanceHtml}
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

        // Helper to parse the last known price for each ticker from CSV logic
        function parseCurrentPrices(csvText) {
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
                        prices[ticker] = price; // Latest price will overwrite previous
                    }
                }
            }
            return prices;
        }

        // Helper to calculate average weighted buy price from trade history
        function calculateAvgBuyPrices(csvText) {
            const buys = {}; // map ticker -> { totalCost: 0, totalQty: 0 }
            const lines = csvText.trim().split('\\n');
            
            // Process chronologically (top to bottom usually, but let's assume standard append log)
            for (let i = 1; i < lines.length; i++) {
                const line = lines[i].trim();
                if (!line) continue;
                const parts = line.split(',');
                if (parts.length < 6) continue;

                const ticker = parts[1];
                const action = parts[2]; // BUY or SELL
                const quantity = parseFloat(parts[3]);
                const price = parseFloat(parts[4]);
                
                if (!buys[ticker]) buys[ticker] = { totalCost: 0, totalQty: 0 };
                
                if (action === 'BUY') {
                    buys[ticker].totalCost += (price * quantity);
                    buys[ticker].totalQty += quantity;
                } else if (action === 'SELL') {
                    // Reduce quantity, keep average cost same logic or FIFO? 
                    // Simple average logic: selling doesn't change the average buy price of remaining shares
                    // but we need to track remaining qty correctly.
                    buys[ticker].totalQty -= quantity;
                    if (buys[ticker].totalQty <= 0) {
                        // Position closed
                        buys[ticker].totalCost = 0;
                        buys[ticker].totalQty = 0;
                    } else {
                        // Proportional cost reduction
                        const avgPrice = buys[ticker].totalCost / (buys[ticker].totalQty + quantity);
                        buys[ticker].totalCost -= (avgPrice * quantity);
                    }
                }
            }
            
            const avgPrices = {};
            Object.keys(buys).forEach(ticker => {
                const data = buys[ticker];
                if (data.totalQty > 0) {
                    avgPrices[ticker] = data.totalCost / data.totalQty;
                }
            });
            return avgPrices;
        }
        
"""
    # Rest of the file handling
    footer = """        // Load data on page load
        loadData();

        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>"""

    # We need to cut off the old script tail first.
    # The start_marker was `async function loadData() {`
    # We replaced everything after that.
    
    final_content = part1 + new_script + footer
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print("Dashboard upgraded successfully.")

if __name__ == '__main__':
    upgrade_dashboard()
