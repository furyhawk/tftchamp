import * as axios from 'axios';
const serverURL = `http://${window.location.hostname}:8000`;
const instance = axios.create();
instance.defaults.baseURL = serverURL;

export { instance as default };