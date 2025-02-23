import React, { useState } from 'react';
import axios from 'axios';
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';

const Finance = () => {
    const [bankName, setBankName] = useState('');
    const [records, setRecords] = useState([]);
    const [chartData, setChartData] = useState({});

    const fetchRecords = async () => {
        try {
            const response = await axios.get(`http://10.0.0.163:8000/records?bank_name=${bankName}`, {
                headers: {
                    'Access-Control-Allow-Origin': '*',
                },
            });
            setRecords(response.data.records);
            prepareChartData(response.data.records);
        } catch (error) {
            console.error('Error fetching records:', error);
        }
    };

    const prepareChartData = (records) => {
        const dates = records.map(record => record.date);
        const amounts = records.map(record => record.amount);

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

    return (
        <div>
            <h1>Finance Records</h1>
            <input
                type="text"
                value={bankName}
                onChange={(e) => setBankName(e.target.value)}
                placeholder="Enter bank name"
            />
            <button onClick={fetchRecords}>Fetch Records</button>

            {records.length > 0 && (
                <div>
                    <h2>Records</h2>
                    <ul>
                        {records.map((record) => (
                            <li key={record.id}>
                                {record.date} - {record.description} - ${record.amount}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {chartData.labels && (
                <div>
                    <h2>Amount Over Time</h2>
                    <Line data={chartData} />
                </div>
            )}
        </div>
    );
};

export default Finance;