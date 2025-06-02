/* eslint-disable react/prop-types */
import { useState } from 'react';
import { Line, Pie } from 'react-chartjs-2';
import walletLogo from '../assets/wallet.svg'
import amexLogo from '../assets/amex.svg'
import citiLogo from '../assets/citi.svg'
import discoverLogo from '../assets/discover.svg'
import noPurchases from '../assets/no-purchases.svg'
import 'chart.js/auto';
import '../../styles/stock.css'

const API_URL = "http://localhost:8000";

const Header = () => (
    <>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
            <h1>MyParser</h1>
            <a href="https://github.com/mcontrjr/playground/tree/main/projects/finance" target="_blank">
                <img src={walletLogo} className="logo react" alt="Wallet logo" />
            </a>
        </div>
    </>
);

const BankSelector = ({ bankName, bankNames, setBankName }) => (
    <div className="my-card mb-2">
        <div className="my-card-header">
            <h4 className="my-card-title">Bank Selector</h4>
        </div>
        <div className="my-card-body">
            <select
                value={bankName}
                onChange={(e) => setBankName(e.target.value)}
                className='finance-select'
                style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-primary)',
                    fontFamily: 'inherit'
                }}
            >
                <option value="">ALL BANKS</option>
                {bankNames.map((name) => (
                    <option key={name} value={name}>{name}</option>
                ))}
            </select>
        </div>
    </div>
);

const AmountLine = ({ lineData }) => {
    const getThemeColors = () => {
        const computedStyle = getComputedStyle(document.documentElement);
        return {
            primary: computedStyle.getPropertyValue('--text-primary').trim(),
            secondary: computedStyle.getPropertyValue('--text-secondary').trim(),
            border: computedStyle.getPropertyValue('--border').trim(),
        };
    };

    const colors = getThemeColors();

    return (
        <div className="finance-chart-container">
            <Line
                data={lineData}
                options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: {
                                color: colors.border
                            },
                            ticks: {
                                color: colors.secondary
                            }
                        },
                        y: {
                            grid: {
                                color: colors.border
                            },
                            ticks: {
                                color: colors.secondary
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const description = context.dataset.descriptions[context.dataIndex];
                                    const amount = context.raw;
                                    return `${description}: $${amount}`;
                                }
                            }
                        },
                        legend: {
                            labels: {
                                color: colors.primary
                            }
                        }
                    }
                }}
            />
        </div>
    );
};

const MonthSelector = ({ selectedMonths, setSelectedMonths }) => (
    <div className="my-card">
        <div className="my-card-header">
            <h4 className="my-card-title">Select Months</h4>
        </div>
        <div className="my-card-body" style={{ textAlign: 'left', padding: '1rem' }}>
            <div className="finance-month-grid">
                {['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'].map((month) => (
                    <label key={month} className="finance-month-item">
                        <input
                            type="checkbox"
                            value={month}
                            name={month}
                            checked={selectedMonths.includes(month)}
                            onChange={({ target: { value, checked } }) => {
                                setSelectedMonths(prev => {
                                    const newMonths = checked 
                                        ? [...prev, value] 
                                        : prev.filter(month => month !== value);
                                    return newMonths;
                                });
                            }}
                            style={{ accentColor: 'var(--accent)' }}
                        />
                        <span style={{ fontSize: '0.8rem' }}>
                            {new Date(0, month - 1).toLocaleString('default', { month: 'short' })}
                        </span>
                    </label>
                ))}
            </div>
        </div>
    </div>
);

const AmountPie = ({ pieData, totalAmount }) => {
    const getThemeColors = () => {
        const computedStyle = getComputedStyle(document.documentElement);
        return {
            primary: computedStyle.getPropertyValue('--text-primary').trim(),
            secondary: computedStyle.getPropertyValue('--text-secondary').trim(),
            border: computedStyle.getPropertyValue('--border').trim(),
        };
    };

    const colors = getThemeColors();

    return (
        <div style={{ display: 'flex', gap: '2rem', height: '500px' }}>
            {/* Pie Chart */}
            <div style={{ flex: '1', minWidth: '400px' }}>
                <Pie 
                    data={pieData} 
                    options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    color: colors.primary,
                                    padding: 20
                                }
                            }
                        }
                    }}
                />
            </div>
            
            {/* Metrics Panel */}
            <div style={{ flex: '0 0 300px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div className="my-card" style={{ margin: 0 }}>
                    <div className="my-card-header">
                        <h4 className="my-card-title">Financial Summary</h4>
                    </div>
                    <div className="my-card-body">
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Total Purchases:</span>
                                <span style={{ color: 'var(--text-primary)', fontWeight: '600' }}>{totalAmount.totalPurchases}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Total Payments:</span>
                                <span style={{ color: 'var(--text-primary)', fontWeight: '600' }}>{totalAmount.totalPayments}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Net Spending:</span>
                                <span style={{ color: totalAmount.netSpending.includes('-') ? '#ef4444' : 'var(--text-primary)', fontWeight: '600' }}>{totalAmount.netSpending}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Avg Purchase:</span>
                                <span style={{ color: 'var(--text-primary)', fontWeight: '600' }}>{totalAmount.avgPurchase}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Purchases:</span>
                                <span style={{ color: 'var(--text-primary)', fontWeight: '600' }}>{totalAmount.purchaseCount}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Total Transactions:</span>
                                <span style={{ color: 'var(--text-primary)', fontWeight: '600' }}>{totalAmount.transactionCount}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const RecordTable = ({ sortedRecords, requestSort }) => {
    const [searchText, setSearchText] = useState('');

    const filteredRecords = sortedRecords.filter(record =>
        record.description.toLowerCase().includes(searchText.toLowerCase())
    );

    return (
        <div className="finance-records-table">
            <div className="mb-3">
                <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>Transaction Records ({filteredRecords.length})</h3>
                <input
                    type="text"
                    placeholder="Search records..."
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    style={{
                        width: '100%',
                        maxWidth: '500px',
                        padding: '0.75rem 1rem',
                        border: '1px solid var(--border)',
                        borderRadius: '8px',
                        backgroundColor: 'var(--bg-card)',
                        color: 'var(--text-primary)',
                        fontFamily: 'inherit',
                        fontSize: '1rem'
                    }}
                />
            </div>
            
            <div className="custom-table-container" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                <table className="custom-table">
                    <thead style={{ position: 'sticky', top: 0, backgroundColor: 'var(--bg-secondary)', zIndex: 1 }}>
                        <tr>
                            <th onClick={() => requestSort('date')} style={{ cursor: 'pointer', padding: '1rem' }}>
                                Date ↕
                            </th>
                            <th onClick={() => requestSort('description')} style={{ cursor: 'pointer', padding: '1rem', minWidth: '250px' }}>
                                Description ↕
                            </th>
                            <th onClick={() => requestSort('amount')} style={{ cursor: 'pointer', padding: '1rem' }}>
                                Amount ↕
                            </th>
                            <th onClick={() => requestSort('category')} style={{ cursor: 'pointer', padding: '1rem' }}>
                                Category ↕
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredRecords.map((record) => (
                            <tr key={record.id} className="custom-table-row">
                                <td style={{ padding: '1rem', whiteSpace: 'nowrap' }}>{record.date}</td>
                                <td style={{ padding: '1rem', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{record.description}</td>
                                <td style={{ 
                                    padding: '1rem',
                                    color: record.amount >= 0 ? 'var(--text-primary)' : '#ff6b6b',
                                    fontWeight: '600',
                                    whiteSpace: 'nowrap'
                                }}>
                                    {record.amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                                </td>
                                <td style={{ padding: '1rem' }}>
                                    <span style={{
                                        padding: '0.25rem 0.75rem',
                                        borderRadius: '12px',
                                        backgroundColor: 'var(--accent)',
                                        fontSize: '0.8rem',
                                        fontWeight: '500'
                                    }}>
                                        {record.category}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

const TabNavigation = ({ activeTab, setActiveTab }) => (
    <div className="gallery-tabs-header">
        <button
            className={`gallery-tab ${activeTab === 'amountOverTime' ? 'active' : ''}`}
            onClick={() => setActiveTab('amountOverTime')}
        >
            Time Series
        </button>
        <button
            className={`gallery-tab ${activeTab === 'distribution' ? 'active' : ''}`}
            onClick={() => setActiveTab('distribution')}
        >
            Distribution
        </button>
        <button
            className={`gallery-tab ${activeTab === 'records' ? 'active' : ''}`}
            onClick={() => setActiveTab('records')}
        >
            Records
        </button>
    </div>
);

const FinanceTabs = ({ activeTab, bankName, bankNames, setBankName, setActiveTab, lineData, pieData, totalAmount, sortedRecords, searchText, setSearchText, requestSort, selectedMonths, setSelectedMonths }) => (
    <div className="gallery-tabs-container">
        <TabNavigation
            activeTab={activeTab}
            setActiveTab={setActiveTab}
        />
        
        <div className="gallery-tab-content">
            <div className="finance-layout">
                {/* Left Sidebar - Controls (20% width) */}
                <div className="finance-sidebar">
                    <BankSelector 
                        bankName={bankName}
                        bankNames={bankNames}
                        setBankName={setBankName}
                    />
                    <MonthSelector
                        selectedMonths={selectedMonths}
                        setSelectedMonths={setSelectedMonths}
                    />
                </div>
                
                {/* Main Content Area (80% width) */}
                <div className="finance-main-content">
                    {sortedRecords.length === 0 ? (
                        <div className="text-center">
                            <div className="my-card">
                                <div className="my-card-body">
                                    <h3 style={{ color: 'var(--text-primary)' }}>No purchases for selected months</h3>
                                    <img src={noPurchases} className="custom-img" alt="No purchases" style={{ maxWidth: '200px', marginTop: '1rem' }} />
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="gallery-tab-pane active">
                            {activeTab === 'amountOverTime' && (
                                <div className="my-card finance-chart-card">
                                    <div className="my-card-header">
                                        <h3 className="my-card-title">Purchases Over Time</h3>
                                    </div>
                                    <div className="my-card-body" style={{ padding: 0 }}>
                                        <AmountLine lineData={lineData} />
                                    </div>
                                </div>
                            )}
                            {activeTab === 'distribution' && (
                                <div className="my-card finance-chart-card">
                                    <div className="my-card-header">
                                        <h3 className="my-card-title">Spending Distribution & Metrics</h3>
                                        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>Purchase categories and financial overview</p>
                                    </div>
                                    <div className="my-card-body" style={{ padding: '1rem' }}>
                                        <AmountPie
                                            pieData={pieData}
                                            totalAmount={totalAmount}
                                        />
                                    </div>
                                </div>
                            )}
                            {activeTab === 'records' && (
                                <div className="my-card finance-chart-card">
                                    <div className="my-card-body">
                                        <RecordTable
                                            sortedRecords={sortedRecords}
                                            requestSort={requestSort}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    </div>
);

const UploadTab = ({uploadMessage, setUploadMessage, fetchRecords}) => (
    <div className="text-center">
        <div className="my-card" style={{ maxWidth: '500px', margin: '0 auto' }}>
            <div className="my-card-header">
                <h3 className="my-card-title">Upload Bank Statements</h3>
            </div>
            <div className="my-card-body">
                <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                    Select your PDF bank statements to analyze your financial data
                </p>
                
                <button 
                    className="my-button" 
                    onClick={() => document.getElementById('fileInput').click()}
                    style={{ 
                        padding: '1rem 2rem',
                        fontSize: '1.1rem',
                        minWidth: '200px'
                    }}
                >
                    Choose Files
                </button>
                
                <input
                    type="file"
                    id="fileInput"
                    style={{ display: 'none' }}
                    multiple
                    accept=".pdf"
                    onChange={async (e) => {
                        const files = e.target.files;
                        if (files.length === 0) return;
                        
                        setUploadMessage(`Uploading ${files.length} file(s)...`);
                        const formData = new FormData();
                        for (let i = 0; i < files.length; i++) {
                            formData.append('pdf_files', files[i]);
                        }

                        try {
                            const response = await fetch(`${API_URL}/parse/`, {
                                method: 'POST',
                                body: formData,
                            });
                            
                            if (!response.ok) {
                                throw new Error('Network response was not ok');
                            }
                            
                            const data = await response.json();
                            setUploadMessage(`Successfully uploaded ${files.length} file(s)! Switch to Analyze tab to view your data.`);
                            fetchRecords();
                        } catch (error) {
                            console.error('Error uploading files:', error);
                            setUploadMessage('Error uploading files. Please try again.');
                        }
                    }}
                />
            </div>
            
            <div className="my-card-footer">
                <p style={{ 
                    fontSize: '0.9rem', 
                    color: 'var(--text-muted)', 
                    margin: 0,
                    fontStyle: 'italic'
                }}>
                    {uploadMessage}
                </p>
            </div>
        </div>
    </div>
);

const SupportedBanks = () => (
    <div className="my-card finance-supported-banks text-center">
        <div className="my-card-header">
            <h4 className="my-card-title">Supported Banks</h4>
        </div>
        <div className="my-card-body">
            <div style={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                gap: '1.5rem',
                flexWrap: 'wrap'
            }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
                    <img 
                        src={amexLogo} 
                        alt="American Express logo" 
                        style={{ width: '40px', height: '40px', objectFit: 'contain' }}
                    />
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>AmEx</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
                    <img 
                        src={discoverLogo} 
                        alt="Discover logo" 
                        style={{ width: '40px', height: '40px', objectFit: 'contain' }}
                    />
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Discover</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
                    <img 
                        src={citiLogo} 
                        alt="Citi Bank logo" 
                        style={{ width: '40px', height: '40px', objectFit: 'contain' }}
                    />
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Citi</span>
                </div>
            </div>
        </div>
    </div>
);

export { Header, BankSelector, FinanceTabs, SupportedBanks, UploadTab };