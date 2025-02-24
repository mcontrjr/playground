import React, { useState, useEffect } from 'react';
import axios from 'axios';
import 'chart.js/auto';
import './app.css'
import {Header, BankSelector, FinanceTabs} from './components/FinanceComponents.jsx';

const API_URL = process.env.VITE_API_URL;
const API_PORT = process.env.SERVER_PORT;

const Finance = () => {
    const [bankName, setBankName] = useState('');
    const [bankNames, setBankNames] = useState([]);
    const [records, setRecords] = useState([]);
    const [chartData, setChartData] = useState({});
    const [pieChartData, setPieChartData] = useState({});
    const [totalAmount, setTotalAmount] = useState(0);
    const [selectedMonths, setSelectedMonths] = useState([]);
    const [activeTab, setActiveTab] = useState('amountOverTime');
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
    

    useEffect(() => {
        const fetchBankNames = async () => {
            try {
                const response = await axios.get(`${API_URL}:${API_PORT}/records`);
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
            const response = await axios.get(`${API_URL}:${API_PORT}/records?bank_name=${bankName}`, {
                headers: {
                    'Access-Control-Allow-Origin': '*',
                },
            });
            let fetchedRecords = response.data.records.map(record => ({
                ...record,
                amount: parseFloat(record.amount),
            }));

            if (selectedMonths.length > 0) {
                fetchedRecords = fetchedRecords.filter(record => selectedMonths.includes(record.date.split('-')[1]));
            }

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
                <FinanceTabs
                    activeTab={activeTab}
                    setActiveTab={setActiveTab}
                    chartData={chartData}
                    pieChartData={pieChartData}
                    totalAmount={totalAmount}
                    sortedRecords={sortedRecords}
                    requestSort={requestSort}
                    selectedMonths={selectedMonths}
                    setSelectedMonths={setSelectedMonths}
                />
            )}
        </div>
    );
};

export default Finance;