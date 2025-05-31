/* eslint-disable react/prop-types */
import { useState } from 'react';
import { Line, Pie } from 'react-chartjs-2';
import walletLogo from '../assets/wallet.svg'
import amexLogo from '../assets/amex.svg'
import citiLogo from '../assets/citi.svg'
import discoverLogo from '../assets/discover.svg'
import noPurchases from '../assets/no-purchases.svg'
import axios from 'axios';
import 'chart.js/auto';
import '../app.css'

const API_URL = "http://10.0.0.163";
const SERVER_PORT = "8000";

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
    <div>
        <p>Bank Selector</p>
        <select
            value={bankName}
            onChange={(e) => setBankName(e.target.value)}
            className='my-select'
        >
            <option value="">ALL</option>
            {bankNames.map((name) => (
                <option key={name} value={name}>{name}</option>
            ))}
        </select>
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
    <div style={{ width: '80%' }}>
        <div style={{ textAlign: 'left' }}>
            <h3>Select Months</h3>
            {['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'].map((month) => (
                <label key={month} className='my-checkbox' style={{ display: 'block' }}>
                    <input
                        type="checkbox"
                        value={month}
                        name={month}
                        checked={selectedMonths.includes(month)}
                        onChange={({ target: { value, checked } }) => {
                            console.log(`Month ${value} is now ${checked ? 'checked' : 'unchecked'}`);
                            setSelectedMonths(prev => {
                                const newMonths = checked 
                                    ? [...prev, value] 
                                    : prev.filter(month => month !== value);
                                console.log('Updated selected months:', newMonths);
                                return newMonths;
                            });
                            console.log('Selected months:', selectedMonths);
                        }}
                    />
                    {new Date(0, month - 1).toLocaleString('default', { month: 'long' })}
                </label>
            ))}
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
            <h2>Records</h2>
            <input
                type="text"
                className="my-select"
                placeholder="Search records..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
            />
            <table className="my-table">
                <thead>
                    <tr>
                        <th onClick={() => requestSort('date')}>Date</th>
                        <th onClick={() => requestSort('description')}>Description</th>
                        <th onClick={() => requestSort('amount')}>Amount</th>
                        <th onClick={() => requestSort('category')}>Category</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredRecords.map((record) => (
                        <tr key={record.id}>
                            <td>{record.date}</td>
                            <td>{record.description}</td>
                            <td>{record.amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</td>
                            <td>{record.category}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

const TabNavigation = ({ activeTab, setActiveTab }) => (
    <div className="my-tab-navigation">
        <button
            className={activeTab === 'amountOverTime' ? 'active' : ''}
            onClick={() => setActiveTab('amountOverTime')}
        >
            Time Series
        </button>
        <button
            className={activeTab === 'distribution' ? 'active' : ''}
            onClick={() => setActiveTab('distribution')}
        >
            Distribution
        </button>
        <button
            className={activeTab === 'records' ? 'active' : ''}
            onClick={() => setActiveTab('records')}
        >
            Records
        </button>
    </div>
);

const FinanceTabs = ({ activeTab, bankName, bankNames, setBankName, setActiveTab, lineData, pieData, totalAmount, sortedRecords, searchText, setSearchText, requestSort, selectedMonths, setSelectedMonths }) => (
    <>
        <TabNavigation
            activeTab={activeTab}
            setActiveTab={setActiveTab}
        />
        <div style={{ display: 'flex', justifyContent: 'center', textAlign: 'center' }}>
            <div style={{ flex: '1' }}>
                <BankSelector 
                    bankName={bankName}
                    bankNames={bankNames}
                    setBankName={setBankName}
                    searchText={searchText}
                    setSearchText={setSearchText}
                />
                <MonthSelector
                    selectedMonths={selectedMonths}
                    setSelectedMonths={setSelectedMonths}
                />
            </div>
            <div style={{ flex: '3', width: '100%' }}>
                {sortedRecords.length === 0 ? (
                    <div>
                        <h3>No purchases for selected months</h3>
                        <img src={noPurchases} className="my-no-purchases" alt="No purchases" width={250} />
                    </div>
                ) : (
                    <>
                        {activeTab === 'amountOverTime' && (
                            <div>
                                <AmountLine lineData={lineData} />
                            </div>
                        )}
                        {activeTab === 'distribution' && (
                            <div>
                                <AmountPie
                                    pieData={pieData}
                                    totalAmount={totalAmount}
                                />
                            </div>
                        )}
                        {activeTab === 'records' && (
                            <RecordTable
                                sortedRecords={sortedRecords}
                                requestSort={requestSort}
                            />
                        )}
                    </>
                )}
            </div>
        </div>
    </>
);

const UploadTab = ({uploadMessage, setUploadMessage, fetchRecords}) => (
    <div>
        <h2>Upload</h2>
        <p>{uploadMessage}</p>
        <button className="my-button" onClick={() => document.getElementById('fileInput').click()}>
            Upload
        </button>
        <input
            type="file"
            id="fileInput"
            style={{ display: 'none' }}
            multiple
            onChange={async (e) => {
                const files = e.target.files;
                const formData = new FormData();
                for (let i = 0; i < files.length; i++) {
                    formData.append('pdf_files', files[i]);
                }

                try {
                    const response = await axios.post(`${API_URL}:${SERVER_PORT}/parse/`, formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data',
                            'Access-Control-Allow-Origin': '*',
                        },
                    });
                    console.log(response.data);
                    setUploadMessage('Files uploaded!');
                    fetchRecords();
                } catch (error) {
                    console.error('Error uploading files:', error);
                }
            }}
        />
    </div>
);

const SupportedBanks = () => (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
            <h3>Supported Banks</h3>
            <img src={amexLogo} className="my-bank-logo" alt="American Express logo" />
            <img src={discoverLogo} className="my-bank-logo" alt="Discover logo" />
            <img src={citiLogo} className="my-bank-logo" alt="Citi Bank logo" />
    </div>
);

export { Header, BankSelector, FinanceTabs, SupportedBanks, UploadTab };