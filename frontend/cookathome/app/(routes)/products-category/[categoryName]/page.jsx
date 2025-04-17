import React from 'react';
import GlobalApi from '@/app/_Utils/GlobalApi';
import TopCategoryList from '../_components/TopCategoryList';
import ProductList from '@/app/_components/ProductList';
async function ProductCategory({ params }) {
  const productList = await GlobalApi.getProductByCategory();
  const categoryList=await GlobalApi.getCategoryList();
  return (
    <div>
      <h2 className='text-2xl font-bold text-center bg-primary text-white p-3'>
        {params.categoryName}</h2>
        <TopCategoryList categoryList={categoryList} />
        <ProductList productList={productList} />
    </div>
  );
}

export default ProductCategory;  