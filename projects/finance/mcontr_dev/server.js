// server.js
import express from 'express';
import cors from 'cors';
import os from 'os';

const app = express();
const PORT = process.env.SERVER_PORT;

app.use(cors());
app.use(express.json());

class Specs {
    constructor () {
        this.hostname = os.hostname();
        this.platform = os.platform();
        this.architecture = os.arch();
        this.cpu = os.cpus();
        this.totalMemory = `${(os.totalmem() / 1024 / 1024).toFixed(2)} MB`;
        this.freeMemory = `${(os.freemem() / 1024 / 1024).toFixed(2)} MB`;
        this.uptime = `${(os.uptime() / 3600).toFixed(2)} hours`;
    }
}

function serverSpecs(){
    const specs = new Specs();
    return specs;
}

app.get('/specs', (req, res) => {
  try {
    const specs = serverSpecs(); 
    res.json({ response : specs });   
  } catch(error) {
      console.error('Could not load. Error: ', error);
      res.status(500).json({ response: error });
  }
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});