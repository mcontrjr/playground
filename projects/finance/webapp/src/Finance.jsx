import React, { useState, useEffect } from 'react';
import axios from 'axios';
import 'chart.js/auto';
import './app.css'
import { Header, FinanceTabs, SupportedBanks, UploadTab } from './components/FinanceComponents.jsx';

const API_URL = "http://10.0.0.163";
const SERVER_PORT = "8000";
console.log('API_URL:', API_URL);
console.log('SERVER_PORT:', SERVER_PORT);

// Notes: fix chart for neg values, fix pie chart to only indlude current amount and spoedning (no negs), fix date co9l in records

const Finance = () => {
    const [bankName, setBankName] = useState('');
    const [bankNames, setBankNames] = useState([]);
    const [uploadMessage, setUploadMessage] = useState('Upload your financial data here.');
    const [analyzeMessage, setAnalyzeMessage] = useState('No records to analyze. Upload in the next tab!');
    const [records, setRecords] = useState([]);
    const [lineData, setLineData] = useState({});
    const [pieData, setPieData] = useState({});
    const [totalAmount, setTotalAmount] = useState(0);
    const [selectedMonths, setSelectedMonths] = useState(['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']);
    const [activeTab, setActiveTab] = useState('amountOverTime');
    const [activeFunctionTab, setActiveFunctionTab] = useState('upload');
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

    const fetchRecords = async () => {
        try {
            const response = await axios.get(`${API_URL}:${SERVER_PORT}/records?bank_name=${bankName}`, {
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

            if (fetchedRecords.length === 0) {
                setAnalyzeMessage('No records for this month. Please select another month.');
            }

            setRecords(fetchedRecords);
            prepareChartData(fetchedRecords);
        } catch (error) {
            console.error('Error fetching records:', error);
        }
    };
    
    useEffect(() => {
        const fetchBankNames = async () => {
            try {
                const response = await axios.get(`${API_URL}:${SERVER_PORT}/records`);
                const fetchedBankNames = [...new Set(response.data.records.map(record => record.bank))];
                setBankNames(fetchedBankNames);
            } catch (error) {
                console.error('Error fetching bank names:', error);
            }
        };

        fetchBankNames();
        fetchRecords();
        // fix this ? 
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

        setPieData({
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

    // use more components!
    return (
        <div>
            <Header />
            <div className='my-card'>
                <div className="my-tab-navigation">
                    <button
                        className={`${activeFunctionTab === 'upload' ? 'active' : ''}`}
                        onClick={() => setActiveFunctionTab('upload')}
                    >
                        Upload
                    </button>
                    <button
                        className={`${activeFunctionTab === 'analyze' ? 'active' : ''}`}
                        onClick={() => {
                            setActiveFunctionTab('analyze')
                            setUploadMessage('Upload your financial data here.')
                        }}
                    >
                        Analyze
                    </button>
                </div>
                {activeFunctionTab === 'analyze' && (
                    <div>
                        {/* Add your Analyze tab content here */}
                        <h2>Analyze</h2>
                        <p>{analyzeMessage}</p>
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
                    <UploadTab
                        uploadMessage={uploadMessage}
                        setUploadMessage={setUploadMessage}
                        fetchRecords={fetchRecords}
                    />
                )}
            </div>
            <SupportedBanks />
        </div>
    );
};

export default Finance;