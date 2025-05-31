import { Box, Button, Typography, TextField, Table, TableBody, TableCell, Tabs, Tab, TableContainer, TableHead, TableRow, Paper, createTheme, ThemeProvider, Stack, CircularProgress } from "@mui/material";
import { TabPanel, TabContext } from '@mui/lab';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { MuiFileInput } from 'mui-file-input'
import { useState, useEffect } from "react";
import error_img from './assets/rainy.svg';
import Footer from './components/footer'

const theme = createTheme({
    typography: {
        fontFamily: '"Roboto Mono", monospace',
        h2: {
            color: "#ffffff",
        },
        h3: {
            color: "#ffffff",
        },
        body1: {
            color: "#ffffff",
        }
    },
    palette: {
        primary: {
            main: '#1c3e5c',
        },
        secondary: {
            main: '#3789ad',
        },
    },
});

export default function FinancePage() {
    const apiUrl = 'http://localhost:5170';
    const [weatherData, setWeatherData] = useState(null);
    const [location, setLocation] = useState('San Jose');
    const [message, setMessage] = useState('Where your money is going?');
    const [error, setError] = useState(false);
    const [loading, setLoading] = useState(false);
    const [file, setFile] = useState(null)

    useEffect(() => {
    }, []);

    const handleChange = (newFile) => {
        setFile(newFile)
    }

    const VisuallyHiddenInput = styled('input')({
        clip: 'rect(0 0 0 0)',
        clipPath: 'inset(50%)',
        height: 1,
        overflow: 'hidden',
        position: 'absolute',
        bottom: 0,
        left: 0,
        whiteSpace: 'nowrap',
        width: 1,
    });

    if (loading) {
        return (
            <ThemeProvider theme={theme}>
                <Box className="my-container">
                    <CircularProgress color="secondary" />
                    <nav>
                        <a href="/" className='my-button'>Home</a>
                    </nav>
                </Box>
            </ThemeProvider>
        );
    }

    if (error) {
        return (
            <ThemeProvider theme={theme}>
                <Box className="my-container">
                    <img src={error_img} alt="error" style={{ width: '350px', height: '350px' }} />
                    <Typography variant="body1">{error}</Typography>
                    <nav>
                        <a href="/" className='my-button'>Home</a>
                    </nav>
                </Box>
            </ThemeProvider>
        );
    }

    return (
        <ThemeProvider theme={theme}>
            <Box className="my-container">
                <Typography variant="h2">Parser</Typography>
                <nav>
                    <a href="/" className='my-button'>Home</a>
                </nav>
                <p>{message}</p>
                <Button
                    component="label"
                    role={undefined}
                    variant="contained"
                    tabIndex={-1}
                    startIcon={<CloudUploadIcon />}
                    >
                    Upload files
                    <VisuallyHiddenInput
                        type="file"
                        onChange={(event) => console.log(event.target.files)}
                        multiple
                    />
                </Button>       
            </Box>
            <Footer sx={{ margin: "50px" }} />
            
        </ThemeProvider>
    );
}