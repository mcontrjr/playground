import React, { useState, useEffect } from 'react';
import 'chart.js/auto';
import '../styles/stock.css';
import { FinanceTabs, SupportedBanks, UploadTab } from './components/FinanceComponents.jsx';
import logo from './assets/finance-logo.svg';
import light from './assets/light.svg';
import dark from './assets/dark.svg';

const API_URL = "http://localhost:8000";

// Theme Hook
function useTheme() {
    const [theme, setTheme] = useState(() => {
        return localStorage.getItem('theme') || 'light';
    });

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
    };

    return { theme, toggleTheme };
}

// Theme Toggle Component
function ThemeToggle({ theme, toggleTheme }) {
    return (
        <button 
            className="theme-toggle" 
            onClick={toggleTheme}
            aria-label="Toggle theme"
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
            {theme === 'light' ? <img src={light} alt="Dark mode" /> : <img src={dark} alt="Light mode" />}
        </button>
    );
}

// Modern Header Component
function ModernHeader({ theme, toggleTheme }) {
    return (
        <header className="my-header">
            <div className="my-header-content">
                <div className="my-logo">
                    <img src={logo} alt="finance-logo" />
                    <div className="my-logo-text">mcontr</div>
                </div>
                <nav className="my-nav" style={{ gap: '0.5rem' }}>
                    <a href="/" className="my-button">
                        Home
                    </a>
                    <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
                </nav>
            </div>
        </header>
    );
}

const Finance = () => {
    const { theme, toggleTheme } = useTheme();
    const [bankName, setBankName] = useState('');
    const [bankNames, setBankNames] = useState([]);
    const [uploadMessage, setUploadMessage] = useState('Upload your statements here..');
    const [analyzeMessage, setAnalyzeMessage] = useState('No records to analyze. Upload in the next tab!');
    const [records, setRecords] = useState([]);
    const [lineData, setLineData] = useState({});
    const [pieData, setPieData] = useState({});
    const [totalAmount, setTotalAmount] = useState(0);
    const [selectedMonths, setSelectedMonths] = useState(['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']);
    const [activeTab, setActiveTab] = useState('amountOverTime');
    const [activeFunctionTab, setActiveFunctionTab] = useState('upload');
    const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'ascending' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const sortedRecords = React.useMemo(() => {
        let sortableRecords = [...records];

        if (sortConfig !== null) {
            sortableRecords.sort((a, b) => {
                if (a[sortConfig.key] < b[sortConfig.key]) {
                    return sortConfig.direction === 'ascending' ? -1 : 1;
                }
                if (a[sortConfig.key] > b[sortConfig.key]) {
                    return sortConfig.direction === 'ascending' ? 1 : -1;
                }
                return 0;
            });
        }
        return sortableRecords;
    }, [records, sortConfig]);

    const fetchRecords = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch(`${API_URL}/records?bank_name=${bankName}`);
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            let fetchedRecords = data.records.map(record => ({
                ...record,
                amount: parseFloat(record.amount),
            }));

            if (selectedMonths.length > 0) {
                fetchedRecords = fetchedRecords.filter(record => selectedMonths.includes(record.date.split('-')[1]));
            }

            if (fetchedRecords.length === 0) {
                setAnalyzeMessage('No records for this month. Please select another month.');
            } else {
                setAnalyzeMessage('');
            }

            setRecords(fetchedRecords);
            prepareChartData(fetchedRecords);
        } catch (error) {
            console.error('Error fetching records:', error);
            setError(error);
            setAnalyzeMessage('Error loading records. Please try again.');
        } finally {
            setLoading(false);
        }
    };
    
    useEffect(() => {
        const fetchBankNames = async () => {
            try {
                const response = await fetch(`${API_URL}/records`);
                
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                
                const data = await response.json();
                const fetchedBankNames = [...new Set(data.records.map(record => record.bank))];
                setBankNames(fetchedBankNames);
            } catch (error) {
                console.error('Error fetching bank names:', error);
            }
        };

        fetchBankNames();
        fetchRecords();
    }, [selectedMonths, bankName]);

    const prepareChartData = (records) => {
        // understand this, how much of this is needed
        const filteredRecords = selectedMonths.length > 0
            ? records.filter(record => selectedMonths.includes(record.date.split('-')[1]))
            : records;
        const sortedRecords = filteredRecords.sort((a, b) => new Date(a.date) - new Date(b.date));

        const dates = sortedRecords.map(record => record.date);
        const purchases = sortedRecords.map(record => {
            if (record.amount > 0) {
                return record.amount;
            } else if (record.amount < 0) {
                return 0;
            }
        });
        const payments = sortedRecords.map(record => {
            if (record.amount < 0) {
                return record.amount;
            } else if (record.amount > 0) {
                return 0;
            }
        });
        console.log('purchases:', purchases);
        console.log('payments:', payments);
        const descriptions = sortedRecords.map(record => record.description);

        setLineData({
            labels: dates,
            datasets: [
                {
                    label: 'Purchases',
                    data: purchases,
                    borderColor: 'rgba(75,192,192,1)',
                    backgroundColor: 'rgba(75,192,192,0.2)',
                    descriptions: descriptions,
                },
                {
                    label: 'Payments',
                    data: payments,
                    borderColor: 'rgb(40, 139, 58)',
                    backgroundColor: 'rgba(26, 125, 35, 0.2)',
                    descriptions: descriptions,
                },
            ],
        });

        // Prepare data for the pie chart (purchases only - positive amounts)
        const categoryData = {};
        const purchaseRecords = sortedRecords.filter(record => record.amount > 0);
        
        purchaseRecords.forEach(record => {
            if (categoryData[record.category]) {
                categoryData[record.category] += record.amount;
            } else {
                categoryData[record.category] = record.amount;
            }
        });

        const pieLabels = Object.keys(categoryData);
        const pieAmounts = Object.values(categoryData);

        setPieData({
            labels: pieLabels,
            datasets: [
            {
                label: 'Spending by Category',
                data: pieAmounts,
                backgroundColor: [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                '#FF9F40', '#C9CBCF', '#FF5733', '#33FF57', '#3357FF',
                '#FF33A1', '#A133FF', '#33FFA1', '#A1FF33', '#FF3333',
                '#33FF33', '#3333FF', '#FF33FF', '#33FFFF', '#FFFF33'
                ],
            },
            ],
        });

        // Calculate high-level metrics
        const totalPurchases = sortedRecords.filter(record => record.amount > 0).reduce((sum, record) => sum + record.amount, 0);
        const totalPayments = Math.abs(sortedRecords.filter(record => record.amount < 0).reduce((sum, record) => sum + record.amount, 0));
        const netSpending = totalPurchases - totalPayments;
        const avgPurchase = purchaseRecords.length > 0 ? totalPurchases / purchaseRecords.length : 0;
        const transactionCount = sortedRecords.length;
        const purchaseCount = purchaseRecords.length;

        const metrics = {
            totalPurchases: totalPurchases.toLocaleString('en-US', { style: 'currency', currency: 'USD' }),
            totalPayments: totalPayments.toLocaleString('en-US', { style: 'currency', currency: 'USD' }),
            netSpending: netSpending.toLocaleString('en-US', { style: 'currency', currency: 'USD' }),
            avgPurchase: avgPurchase.toLocaleString('en-US', { style: 'currency', currency: 'USD' }),
            transactionCount,
            purchaseCount
        };
        
        setTotalAmount(metrics);
    };

    const requestSort = (key) => {
        let direction = 'ascending';
        if (sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
    };

    const handleKeyPress = (event) => {
        if (event.key === 'Enter') {
            fetchRecords();
        }
    };
    // can we merge this in with another useEffect? 
    useEffect(() => {
        window.addEventListener('keypress', handleKeyPress);
        return () => {
            window.removeEventListener('keypress', handleKeyPress);
        };
    }, []);

    if (loading) return (
        <>
            <ModernHeader theme={theme} toggleTheme={toggleTheme} />
            <div className="my-container">
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                    <div style={{ 
                        width: '40px', 
                        height: '40px', 
                        border: '4px solid var(--border)', 
                        borderTop: '4px solid var(--accent)', 
                        borderRadius: '50%', 
                        animation: 'spin 1s linear infinite',
                        margin: '0 auto'
                    }}></div>
                    <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>Loading financial data...</p>
                </div>
            </div>
        </>
    )

    if (error) return (
        <>
            <ModernHeader theme={theme} toggleTheme={toggleTheme} />
            <div className="my-container">
                <div style={{ textAlign: 'center' }}>
                    <div className="my-card">
                        <div className="my-card-body">
                            <h3 style={{ color: 'var(--text-primary)' }}>Error Loading Data</h3>
                            <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>
                                {error.message || 'Unable to connect to the finance server. Please try again.'}
                            </p>
                            <button 
                                className="my-button mt-2" 
                                onClick={() => {
                                    setError(null);
                                    fetchRecords();
                                }}
                            >
                                Retry
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )

    return (
        <>
            <ModernHeader theme={theme} toggleTheme={toggleTheme} />
            <main>
                <section className="my-section">
                    <div className="my-container">                        
                        {/* Main Finance Card */}
                        <div className="gallery-tabs-container animate-fade-in-up">
                            <div className="gallery-tabs-header">
                                <button
                                    className={`gallery-tab ${activeFunctionTab === 'upload' ? 'active' : ''}`}
                                    onClick={() => setActiveFunctionTab('upload')}
                                >
                                    Upload Center
                                </button>
                                <button
                                    className={`gallery-tab ${activeFunctionTab === 'analyze' ? 'active' : ''}`}
                                    onClick={() => {
                                        setActiveFunctionTab('analyze')
                                        setUploadMessage('Upload more statements here.')
                                    }}
                                >
                                    Breakdown
                                </button>
                            </div>
                            
                            <div className="gallery-tab-content">
                                {activeFunctionTab === 'analyze' && (
                                    <div className="gallery-tab-pane active">
                                        {analyzeMessage && (
                                            <div className="gallery-engine-info">
                                                <h3 className="gallery-engine-title">Financial Analysis</h3>
                                                <p className="gallery-engine-description">{analyzeMessage}</p>
                                            </div>
                                        )}
                                        
                                        <FinanceTabs
                                            activeTab={activeTab}
                                            bankName={bankName}
                                            bankNames={bankNames}
                                            setBankName={setBankName}
                                            setActiveTab={setActiveTab}
                                            lineData={lineData}
                                            pieData={pieData}
                                            totalAmount={totalAmount}
                                            sortedRecords={sortedRecords}
                                            requestSort={requestSort}
                                            selectedMonths={selectedMonths}
                                            setSelectedMonths={setSelectedMonths}
                                        />
                                    </div>
                                )}
                                
                                {activeFunctionTab === 'upload' && (
                                    <div className="gallery-tab-pane active">                                        
                                        <UploadTab
                                            uploadMessage={uploadMessage}
                                            setUploadMessage={setUploadMessage}
                                            fetchRecords={fetchRecords}
                                        />
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Supported Banks Section */}
                        <div className="mt-4 animate-fade-in-up">
                            <SupportedBanks />
                        </div>
                    </div>
                </section>
            </main>
        </>
    );
};

export default Finance;