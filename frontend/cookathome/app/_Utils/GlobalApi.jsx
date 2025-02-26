const { default: axios } = require('axios');

const axiosClient = axios.create({
  baseURL: 'http://192.168.1.155:1337/api',
});

// Fetch categories with populated fields
const getCategory = () => axiosClient.get('/categories?populate=*');

// Fetch sliders with populated fields
const getSliders = () => 
  axiosClient.get('/sliders?populate=*').then((resp) =>{return  resp.data.data});
const getCategoryList = () => 
  axiosClient.get('/categories?populate=*').then((resp) => {return resp.data.data});

const getAllProducts = () => 
  axiosClient.get('/products?populate=*').then((resp) => {return resp.data.data});
export default {
  getCategory,
  getSliders,
  getCategoryList,
  getAllProducts,
};
