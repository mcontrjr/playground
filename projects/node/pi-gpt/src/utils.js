const os = require('os');

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
    const specs = new Specs()
    return specs;
}

module.exports = { serverSpecs }; 