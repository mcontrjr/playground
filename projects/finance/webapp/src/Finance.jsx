import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';
import './App.css'

const Finance = () => {
    const [bankName, setBankName] = useState('');
    const [bankNames, setBankNames] = useState([]);
    const [records, setRecords] = useState([]);
    const [chartData, setChartData] = useState({});
    const [selectedMonths, setSelectedMonths] = useState([]);

    // Fetch the list of bank names on component mount
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

        setChartData({
            labels: dates,
            datasets: [
                {
                    label: 'Amount',
                    data: amounts,
                    borderColor: 'rgba(75,192,192,1)',
                    backgroundColor: 'rgba(75,192,192,0.2)',
                },
            ],
        });
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
            <h1>Finance Records</h1>
            <select
                value={bankName}
                onChange={(e) => setBankName(e.target.value)}
                className='my-select'
            >
                <option value="">Select a bank</option>
                {bankNames.map((name) => (
                    <option key={name} value={name}>{name}</option>
                ))}
            </select>
            <button onClick={fetchRecords} className='my-button'>Fetch Records</button>

            {chartData.labels && (
                <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                        <h2>Amount Over Time</h2>
                        <Line data={chartData} />
                    </div>
                    <div style={{ marginLeft: '20px' }}>
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
                </div>
            )}
            
            {records.length > 0 && (
                <div>
                    <h2>Records</h2>
                    <table className="my-table">
                        <thead>
                            <tr>
                                <th onClick={() => requestSort('date')}>Date</th>
                                <th onClick={() => requestSort('description')}>Description</th>
                                <th onClick={() => requestSort('amount')}>Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sortedRecords.map((record) => (
                                <tr key={record.id}>
                                    <td>{record.date}</td>
                                    <td>{record.description}</td>
                                    <td>${record.amount}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default Finance;