import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Line, Pie } from 'react-chartjs-2';
import walletLogo from './assets/wallet.svg'
import 'chart.js/auto';
import './app.css'

const Header = () => (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
        <h1>MyFinance</h1>
        <a href="https://github.com/mcontrjr/playground/tree/main/projects/finance" target="_blank">
            <img src={walletLogo} className="logo react" alt="Wallet logo" />
        </a>
    </div>
);

const BankSelector = ({ bankName, bankNames, setBankName, fetchRecords }) => (
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
        <button onClick={fetchRecords} className='my-button'>Analyze</button>
    </div>
);

const AmountLine = ({ chartData }) => (
    <div>
        <h2 className='my-h2'>Amount Over Time</h2>
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

const MonthSelector = ({ selectedMonths, setSelectedMonths }) => (
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
                    }}
                />
                {new Date(0, month - 1).toLocaleString('default', { month: 'long' })}
            </label>
        ))}
    </div>
);

const AmountPie = ({ pieChartData, totalAmount }) => (
    <div>
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
                        <td>${record.amount}</td>
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


const Finance = () => {
    const [bankName, setBankName] = useState('');
    const [bankNames, setBankNames] = useState([]);
    const [records, setRecords] = useState([]);
    const [chartData, setChartData] = useState({});
    const [pieChartData, setPieChartData] = useState({});
    const [totalAmount, setTotalAmount] = useState(0);
    const [selectedMonths, setSelectedMonths] = useState([]);
    const [activeTab, setActiveTab] = useState('amountOverTime');
    

    useEffect(() => {
        const fetchBankNames = async () => {
            try {
                const response = await axios.get('http://10.0.0.163:8000/records');
                const fetchedBankNames = [...new Set(response.data.records.map(record => record.bank))];
                setBankNames(fetchedBankNames);
            } catch (error) {
                console.error('Error fetching bank names:', error);
            }
        };

        fetchBankNames();
    }, []);

    const fetchRecords = async () => {
        try {
            const response = await axios.get(`http://10.0.0.163:8000/records?bank_name=${bankName}`, {
                headers: {
                    'Access-Control-Allow-Origin': '*',
                },
            });
            const fetchedRecords = response.data.records.map(record => ({
                ...record,
                amount: parseFloat(record.amount),
            }));
            setRecords(fetchedRecords);
            prepareChartData(fetchedRecords);
        } catch (error) {
            console.error('Error fetching records:', error);
        }
    };

    const prepareChartData = (records) => {
        const filteredRecords = selectedMonths.length > 0
            ? records.filter(record => selectedMonths.includes(record.date.split('-')[1]))
            : records;
        const sortedRecords = filteredRecords.sort((a, b) => new Date(a.date) - new Date(b.date));

        const dates = sortedRecords.map(record => record.date);
        const amounts = sortedRecords.map(record => record.amount);
        const descriptions = sortedRecords.map(record => record.description);

        setChartData({
            labels: dates,
            datasets: [
                {
                    label: 'Amount',
                    data: amounts,
                    borderColor: 'rgba(75,192,192,1)',
                    backgroundColor: 'rgba(75,192,192,0.2)',
                    descriptions: descriptions,
                },
            ],
        });

        // Prepare data for the pie chart
        const categoryData = {};
        sortedRecords.forEach(record => {
            if (categoryData[record.category]) {
                categoryData[record.category] += record.amount;
            } else {
                categoryData[record.category] = record.amount;
            }
        });

        const pieLabels = Object.keys(categoryData);
        const pieAmounts = Object.values(categoryData);

        setPieChartData({
            labels: pieLabels,
            datasets: [
            {
                label: 'Amount by Category',
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

        const formattedTotalAmount = pieAmounts.reduce((acc, amount) => acc + amount, 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
        setTotalAmount(formattedTotalAmount);
    };

    const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'ascending' });

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

    const requestSort = (key) => {
        let direction = 'ascending';
        if (sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
    };

    return (
        <div>
            <Header />
            <BankSelector
                bankName={bankName}
                bankNames={bankNames}
                setBankName={setBankName}
                fetchRecords={fetchRecords}
            />
            {records.length > 0 && (
                <>
                    <TabNavigation
                        activeTab={activeTab}
                        setActiveTab={setActiveTab}
                    />
                    {activeTab === 'amountOverTime' && (
                        <>
                            <AmountLine chartData={chartData} />
                            <MonthSelector
                                selectedMonths={selectedMonths}
                                setSelectedMonths={setSelectedMonths}
                            />
                        </>
                    )}
                    {activeTab === 'distribution' && (
                        <AmountPie
                            pieChartData={pieChartData}
                            totalAmount={totalAmount}
                        />
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
    );
};

export default Finance;