import React from 'react';
import { Line, Pie } from 'react-chartjs-2';
import walletLogo from '../assets/wallet.svg'
import amexLogo from '../assets/amex.svg'
import 'chart.js/auto';
import '../app.css'

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

const AmountLine = ({ chartData }) => (
    <div style={{ width: '850px' }}>
        <h2>Purchases</h2>
        <Line
            data={chartData}
            options={{
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const description = context.dataset.descriptions[context.dataIndex];
                                const amount = context.raw;
                                return `${description}: $${amount}`;
                            }
                        }
                    }
                }
            }}
        />
    </div>
);

const MonthSelector = ({ selectedMonths, setSelectedMonths, fetchRecords }) => (
    <div>
        <h3>Select Months</h3>
        {['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'].map((month) => (
            <label key={month} className='my-checkbox'>
                <input
                    type="checkbox"
                    value={month}
                    checked={selectedMonths.includes(month)}
                    onChange={(e) => {
                        const value = e.target.value;
                        setSelectedMonths((prev) =>
                            prev.includes(value)
                                ? prev.filter((month) => month !== value)
                                : [...prev, value]
                        );
                        fetchRecords();
                    }}
                />
                {new Date(0, month - 1).toLocaleString('default', { month: 'long' })}
            </label>
        ))}
    </div>
);

const AmountPie = ({ pieChartData, totalAmount }) => (
    <div style={{ width: '750px' }}>
        <h2>Total Amount: {totalAmount}</h2>
        <Pie data={pieChartData} />
    </div>
);

const RecordTable = ({ sortedRecords, requestSort }) => (
    <div>
        <h2>Records</h2>
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
                {sortedRecords.map((record) => (
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

const FinanceTabs = ({ activeTab, setActiveTab, chartData, pieChartData, totalAmount, sortedRecords, requestSort, selectedMonths, setSelectedMonths, fetchRecords }) => (
    <>
        <TabNavigation
            activeTab={activeTab}
            setActiveTab={setActiveTab}
        />
        <div style={{ display: 'flex', justifyContent: 'center', textAlign: 'center' }}>
            <div style={{ flex: '1' }}>
                <MonthSelector
                    selectedMonths={selectedMonths}
                    setSelectedMonths={setSelectedMonths}
                    fetchRecords={fetchRecords}
                />
            </div>
            <div style={{ flex: '3' }}>
                {activeTab === 'amountOverTime' && (
                    <div>
                        <AmountLine chartData={chartData} />
                    </div>
                )}
                {activeTab === 'distribution' && (
                    <div>
                        <AmountPie
                            pieChartData={pieChartData}
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
            </div>
        </div>
    </>
);

const SupportBanks = () => (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
            <h3>Supported Banks</h3>
            <img src={amexLogo} className="my-bank-logo" alt="American Express logo" />
    </div>
);

export { Header, BankSelector, FinanceTabs, SupportBanks };