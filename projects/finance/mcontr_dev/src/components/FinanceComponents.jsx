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

const AmountLine = ({ lineData }) => (
    <div style={{ width: '100%' }}>
        <h2>Purchases</h2>
        <Line
            data={lineData}
            options={{
                scales: {
                    x: {
                        grid: {
                            color: '#49585c'
                        },
                        ticks: {
                            color: '#b8d8e0'
                        }
                    },
                    y: {
                        grid: {
                            color: '#49585c'
                        },
                        ticks: {
                            color: '#b8d8e0'
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
                            color: '#509aad'
                        }
                    }
                }
            }}
        />
    </div>
);

const MonthSelector = ({ selectedMonths, setSelectedMonths }) => (
    <div className="my-card">
        <div className="my-card-header">
            <h4 className="my-card-title">Select Months</h4>
        </div>
        <div className="my-card-body" style={{ textAlign: 'left' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
                {['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'].map((month) => (
                    <label key={month} style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '0.5rem',
                        padding: '0.25rem',
                        cursor: 'pointer',
                        color: 'var(--text-secondary)'
                    }}>
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
                        <span>{new Date(0, month - 1).toLocaleString('default', { month: 'long' })}</span>
                    </label>
                ))}
            </div>
        </div>
    </div>
);

const AmountPie = ({ pieData, totalAmount }) => (
    <div style={{ width: '100%' }}>
        <h2>Total Amount: {totalAmount}</h2>
        <Pie 
            data={pieData} 
            options={{
                plugins: {
                    legend: {
                        labels: {
                            color: 'white'
                        }
                    }
                }
            }}
        />
    </div>
);

const RecordTable = ({ sortedRecords, requestSort }) => {
    const [searchText, setSearchText] = useState('');

    const filteredRecords = sortedRecords.filter(record =>
        record.description.toLowerCase().includes(searchText.toLowerCase())
    );

    return (
        <div>
            <div className="mb-3">
                <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>Transaction Records</h3>
                <input
                    type="text"
                    placeholder="Search records..."
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    style={{
                        width: '100%',
                        maxWidth: '400px',
                        padding: '0.75rem 1rem',
                        border: '1px solid var(--border)',
                        borderRadius: '8px',
                        backgroundColor: 'var(--bg-card)',
                        color: 'var(--text-primary)',
                        fontFamily: 'inherit'
                    }}
                />
            </div>
            
            <div className="custom-table-container">
                <table className="custom-table">
                    <thead>
                        <tr>
                            <th onClick={() => requestSort('date')} style={{ cursor: 'pointer' }}>
                                Date ↕
                            </th>
                            <th onClick={() => requestSort('description')} style={{ cursor: 'pointer' }}>
                                Description ↕
                            </th>
                            <th onClick={() => requestSort('amount')} style={{ cursor: 'pointer' }}>
                                Amount ↕
                            </th>
                            <th onClick={() => requestSort('category')} style={{ cursor: 'pointer' }}>
                                Category ↕
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredRecords.map((record) => (
                            <tr key={record.id} className="custom-table-row">
                                <td>{record.date}</td>
                                <td>{record.description}</td>
                                <td style={{ 
                                    color: record.amount >= 0 ? 'var(--text-primary)' : '#ff6b6b',
                                    fontWeight: '500'
                                }}>
                                    {record.amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                                </td>
                                <td>
                                    <span style={{
                                        padding: '0.25rem 0.5rem',
                                        borderRadius: '4px',
                                        backgroundColor: 'var(--accent)',
                                        fontSize: '0.85rem'
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
            <div className="game-layout">
                {/* Left Sidebar - Controls */}
                <div className="game-sidebar" style={{ flex: '0 0 300px' }}>
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
                
                {/* Main Content Area */}
                <div className="game-main" style={{ flex: '1', minWidth: '0' }}>
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
                                <div className="my-card">
                                    <div className="my-card-header">
                                        <h3 className="my-card-title">Purchases Over Time</h3>
                                    </div>
                                    <div className="my-card-body">
                                        <AmountLine lineData={lineData} />
                                    </div>
                                </div>
                            )}
                            {activeTab === 'distribution' && (
                                <div className="my-card">
                                    <div className="my-card-header">
                                        <h3 className="my-card-title">Spending Distribution</h3>
                                        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>Total: {totalAmount}</p>
                                    </div>
                                    <div className="my-card-body">
                                        <AmountPie
                                            pieData={pieData}
                                            totalAmount={totalAmount}
                                        />
                                    </div>
                                </div>
                            )}
                            {activeTab === 'records' && (
                                <div className="my-card">
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
    <div className="my-card text-center">
        <div className="my-card-header">
            <h3 className="my-card-title">Supported Banks</h3>
        </div>
        <div className="my-card-body">
            <div style={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                gap: '2rem',
                flexWrap: 'wrap'
            }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                    <img 
                        src={amexLogo} 
                        alt="American Express logo" 
                        style={{ width: '60px', height: '60px', objectFit: 'contain' }}
                    />
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>American Express</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                    <img 
                        src={discoverLogo} 
                        alt="Discover logo" 
                        style={{ width: '60px', height: '60px', objectFit: 'contain' }}
                    />
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Discover</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                    <img 
                        src={citiLogo} 
                        alt="Citi Bank logo" 
                        style={{ width: '60px', height: '60px', objectFit: 'contain' }}
                    />
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Citi Bank</span>
                </div>
            </div>
        </div>
    </div>
);

export { Header, BankSelector, FinanceTabs, SupportedBanks, UploadTab };