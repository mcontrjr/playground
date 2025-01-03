import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, createTheme, ThemeProvider, CircularProgress } from "@mui/material";
import { useState, useEffect } from "react";
import error_img from './assets/error.svg'

const theme = createTheme({
    typography: {
        fontFamily: '"Roboto Mono", monospace',
        h2: {
            color: "#ffffff" // Custom color for h2
        },
        h3: {
            color: "#ffffff" // Custom color for h3
        },
        body1: {
            color: "#ffffff" // Custom default text color
        }
    },
    palette: {
        primary: {
            main: '#1c3e5c', // Main color for primary elements
        },
        secondary: {
            main: '#3789ad', // Main color for secondary elements
        },
    },
});


export default function InfoPage() {
    const apiUrl = 'http://localhost:5170';
    const [specs, setSpecs] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        try {
            fetch(`${apiUrl}/specs`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                setSpecs(data.response);
                setLoading(false);
            })
            .catch(error => setError(error));
        } catch (e) {
            setError(e);
        }
        
    }, []);

    // console.log(`Error state: ${error}`)
    if (loading) return (
        <ThemeProvider theme={theme}>
            <Box className="my-container" >
                <CircularProgress color="#3789ad" />
                <nav>
                    <a href="/" className='my-button'>Home</a>
                </nav>
            </Box>
        </ThemeProvider>
    )

    if (error) return (
        <ThemeProvider theme={theme}>
            <Box className="my-container">
                <img src={error_img} alt="error" style={{ width: '480px', height: '480px' }}></img>
                <Typography variant="body1">{error}</Typography>
                <nav>
                    <a href="/" className='my-button'>Home</a>
                </nav>
            </Box>
        </ThemeProvider>
    )

    return (
        <ThemeProvider theme={theme}>
            <Box className="my-container" >
                <Typography variant="h2">Server Stats</Typography>
                <TableContainer component={Paper} className="custom-table-container" sx={{backgroundColor: '#3789ad'}}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Hostname</TableCell>
                                <TableCell>Platform</TableCell>
                                <TableCell>Architecture</TableCell>
                                <TableCell>Total Memory</TableCell>
                                <TableCell>Free Memory</TableCell>
                                <TableCell>Uptime</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            <TableRow>
                                <TableCell>{specs.hostname}</TableCell>
                                <TableCell>{specs.platform}</TableCell>
                                <TableCell>{specs.architecture}</TableCell>
                                <TableCell>{specs.totalMemory}</TableCell>
                                <TableCell>{specs.freeMemory}</TableCell>
                                <TableCell>{specs.uptime}</TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </TableContainer>

                <Typography variant="h2" sx={{ margin: "10px" }}>CPU Info</Typography>
                <TableContainer component={Paper} className="custom-table-container" sx={{backgroundColor: '#3789ad'}}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Model</TableCell>
                                <TableCell>Speed (MHz)</TableCell>
                                <TableCell>User Time</TableCell>
                                <TableCell>Idle Time</TableCell>
                                <TableCell>System Time</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {specs.cpu.map((cpu, index) => (
                                <TableRow key={index} className="custom-table-row">
                                    <TableCell>{cpu.model}</TableCell>
                                    <TableCell>{cpu.speed}</TableCell>
                                    <TableCell>{cpu.times.user}</TableCell>
                                    <TableCell>{cpu.times.idle}</TableCell>
                                    <TableCell>{cpu.times.sys}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
                <nav>
                    <a href="/" className='my-button'>Home</a>
                </nav>
            </Box>
        </ThemeProvider>
    );
}